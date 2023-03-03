package integration_test

import (
	"fmt"
	"os"
	"os/exec"
	"time"

	"github.com/cloudfoundry/libbuildpack/cutlass"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("Deploy app with", func() {
	var (
		app                       *cutlass.App
		serviceName, serviceName2 string
		dynatraceAPI              *cutlass.App
		dynatraceAPIURI           string
	)

	var RunCf = func(args ...string) error {
		command := exec.Command("cf", args...)
		command.Stdout = GinkgoWriter
		command.Stderr = GinkgoWriter
		return command.Run()
	}

	BeforeEach(func() {
		dynatraceAPI = cutlass.New(Fixtures("fake_dynatrace_api"))
		// TODO: remove this once go-buildpack runs on cflinuxfs4
		// This is done to have the dynatrace broker app written in go up and running
		if os.Getenv("CF_STACK") == "cflinuxfs4" {
			dynatraceAPI.Stack = "cflinuxfs3"
		}
		dynatraceAPI.SetEnv("BP_DEBUG", "true")

		Expect(dynatraceAPI.Push()).To(Succeed())
		Eventually(func() ([]string, error) { return dynatraceAPI.InstanceStates() }, 60*time.Second).Should(Equal([]string{"RUNNING"}))

		var err error
		dynatraceAPIURI, err = dynatraceAPI.GetUrl("")
		Expect(err).NotTo(HaveOccurred())

		app = cutlass.New(Fixtures("with_dynatrace"))
		app.SetEnv("BP_DEBUG", "true")
		Expect(app.PushNoStart()).To(Succeed())
	})

	AfterEach(func() {
		app = DestroyApp(app)
		dynatraceAPI = DestroyApp(dynatraceAPI)

		if serviceName != "" {
			_ = RunCf("delete-service", "-f", serviceName)
			serviceName = ""
		}
		if serviceName2 != "" {
			_ = RunCf("delete-service", "-f", serviceName2)
			serviceName2 = ""
		}
	})

	It("single dynatrace service without manifest.json", func() {
		serviceName = "dynatrace-service-" + cutlass.RandStringRunes(20)
		Expect(RunCf("cups", serviceName, "-p", fmt.Sprintf(`{"apitoken":"TOKEN","apiurl":"%s/without-agent-path","environmentid":"envid"}`, dynatraceAPIURI))).To(Succeed())
		Expect(RunCf("bind-service", app.Name, serviceName)).To(Succeed())
		Expect(RunCf("start", app.Name)).To(Succeed())
		ConfirmRunning(app)
		Expect(app.ConfirmBuildpack(buildpackVersion)).To(Succeed())

		By("initializing dynatrace agent")
		Expect(app.Stdout.String()).To(ContainSubstring("Initializing"))

		By("detecting single dynatrace service")
		Expect(app.Stdout.String()).To(ContainSubstring("Found one matching Dynatrace service"))

		By("downloading dynatrace agent")
		Expect(app.Stdout.String()).To(ContainSubstring("Downloading Dynatrace OneAgent Installer"))

		By("extracting dynatrace agent")
		Expect(app.Stdout.String()).To(ContainSubstring("Extracting Dynatrace OneAgent"))

		By("removing dynatrace agent installer")
		Expect(app.Stdout.String()).To(ContainSubstring("Removing Dynatrace OneAgent Installer"))

		By("adding environment vars")
		Expect(app.Stdout.String()).To(ContainSubstring("Adding Dynatrace specific Environment Vars"))

		By("LD_PRELOAD settings")
		Expect(app.Stdout.String()).To(ContainSubstring("Adding Dynatrace LD_PRELOAD settings"))

		By("checking for manifest.json fallback")
		Expect(app.Stdout.String()).To(ContainSubstring("Agent path not found in manifest.json, using fallback"))
	})

	It("Deploy app with multiple dynatrace services", func() {
		serviceName = "dynatrace-service-" + cutlass.RandStringRunes(20)
		Expect(RunCf("cups", serviceName, "-p", fmt.Sprintf(`{"apitoken":"TOKEN","apiurl":"%s","environmentid":"envid"}`, dynatraceAPIURI))).To(Succeed())
		Expect(RunCf("bind-service", app.Name, serviceName)).To(Succeed())

		serviceName2 = "dynatrace-service-" + cutlass.RandStringRunes(20)
		Expect(RunCf("cups", serviceName2, "-p", fmt.Sprintf(`{"apitoken":"TOKEN","apiurl":"%s","environmentid":"envid_dupe"}`, dynatraceAPIURI))).To(Succeed())
		Expect(RunCf("bind-service", app.Name, serviceName2)).To(Succeed())

		By("deployment should fail")
		Expect(RunCf("start", app.Name)).ToNot(Succeed())
		Expect(app.ConfirmBuildpack(buildpackVersion)).To(Succeed())

		By("initializing dynatrace agent")
		Eventually(app.Stdout.String).Should(ContainSubstring("Initializing"))

		By("detecting multiple dynatrace services")
		Eventually(app.Stdout.String).Should(ContainSubstring("More than one matching service found!"))
	})

	It("Deploy app with single dynatrace service, wrong url and skiperrors on true", func() {
		serviceName = "dynatrace-service-" + cutlass.RandStringRunes(20)
		Expect(RunCf("cups", serviceName, "-p", fmt.Sprintf(`{"apitoken":"TOKEN","apiurl":"%s/no-such-endpoint","environmentid":"envid","skiperrors":"true"}`, dynatraceAPIURI))).To(Succeed())
		Expect(RunCf("bind-service", app.Name, serviceName)).To(Succeed())

		By("deployment should not fail")
		Expect(RunCf("start", app.Name)).To(Succeed())
		Expect(app.ConfirmBuildpack(buildpackVersion)).To(Succeed())

		By("initializing dynatrace agent")
		Expect(app.Stdout.String()).To(ContainSubstring("Initializing"))

		By("detecting single dynatrace service")
		Expect(app.Stdout.String()).To(ContainSubstring("Found one matching Dynatrace service"))

		By("downloading dynatrace agent")
		Expect(app.Stdout.String()).To(ContainSubstring("Downloading Dynatrace OneAgent Installer"))

		By("download retries work")
		Expect(app.Stdout.String()).To(ContainSubstring("Error during installer download, retrying in 4 seconds"))
		Expect(app.Stdout.String()).To(ContainSubstring("Error during installer download, retrying in 5 seconds"))
		Expect(app.Stdout.String()).To(ContainSubstring("Error during installer download, retrying in 7 seconds"))

		By("should exit gracefully")
		Expect(app.Stdout.String()).To(ContainSubstring("Error during installer download, skipping installation"))

		By("no further installer logs")
		Expect(app.Stdout.String()).ToNot(ContainSubstring("Extracting Dynatrace OneAgent"))
	})

	It("Deploy app with single dynatrace service, wrong url and skiperrors not set", func() {
		serviceName = "dynatrace-service-" + cutlass.RandStringRunes(20)
		Expect(RunCf("cups", serviceName, "-p", fmt.Sprintf(`{"apitoken":"TOKEN","apiurl":"%s/no-such-endpoint","environmentid":"envid"}`, dynatraceAPIURI))).To(Succeed())
		Expect(RunCf("bind-service", app.Name, serviceName)).To(Succeed())

		By("deployment should fail")
		Expect(RunCf("start", app.Name)).ToNot(Succeed())
		Expect(app.ConfirmBuildpack(buildpackVersion)).To(Succeed())

		By("initializing dynatrace agent")
		Eventually(app.Stdout.String).Should(ContainSubstring("Initializing"))

		By("detecting single dynatrace service")
		Expect(app.Stdout.String()).To(ContainSubstring("Found one matching Dynatrace service"))

		By("downloading dynatrace agent")
		Expect(app.Stdout.String()).To(ContainSubstring("Downloading Dynatrace OneAgent Installer"))

		By("download retries work")
		Expect(app.Stdout.String()).To(ContainSubstring("Error during installer download, retrying in 4 seconds"))
		Expect(app.Stdout.String()).To(ContainSubstring("Error during installer download, retrying in 5 seconds"))
		Expect(app.Stdout.String()).To(ContainSubstring("Error during installer download, retrying in 7 seconds"))

		By("no further installer logs")
		Expect(app.Stdout.String()).ToNot(ContainSubstring("Extracting Dynatrace OneAgent"))
	})

	It("Deploy app with single dynatrace service and network zone set", func() {
		serviceName := "dynatrace-" + cutlass.RandStringRunes(20) + "-service"
		Expect(RunCf("cups", serviceName, "-p", fmt.Sprintf(`{"apitoken":"secretpaastoken","apiurl":"%s","environmentid":"envid", "networkzone":"testzone"}`, dynatraceAPIURI))).To(Succeed())
		Expect(RunCf("bind-service", app.Name, serviceName)).To(Succeed())
		Expect(RunCf("start", app.Name)).To(Succeed())
		ConfirmRunning(app)

		Expect(app.ConfirmBuildpack(buildpackVersion)).To(Succeed())
		Expect(app.Stdout.String()).To(ContainSubstring("Extracting Dynatrace OneAgent"))
		Expect(app.Stdout.String()).To(ContainSubstring("Setting DT_NETWORK_ZONE..."))
	})

	It("Deploy app with single dynatrace service and check for config update", func() {
		serviceName := "dynatrace-" + cutlass.RandStringRunes(20) + "-service"
		Expect(RunCf("cups", serviceName, "-p", fmt.Sprintf(`{"apitoken":"secretpaastoken","apiurl":"%s","environmentid":"envid", "networkzone":"testzone"}`, dynatraceAPIURI))).To(Succeed())
		Expect(RunCf("bind-service", app.Name, serviceName)).To(Succeed())
		Expect(RunCf("start", app.Name)).To(Succeed())
		ConfirmRunning(app)

		Expect(app.ConfirmBuildpack(buildpackVersion)).To(Succeed())
		Expect(app.Stdout.String()).To(ContainSubstring("Fetching updated OneAgent configuration from tenant..."))
		Expect(app.Stdout.String()).To(ContainSubstring("Finished writing updated OneAgent config back to"))
	})

})
