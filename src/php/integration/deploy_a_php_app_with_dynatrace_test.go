package integration_test

import (
	"os/exec"
	"path/filepath"

	"github.com/cloudfoundry/libbuildpack/cutlass"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("Deploy app with", func() {
	var app *cutlass.App
	var serviceName, serviceName2 string
	RunCf := func(args ...string) error {
		command := exec.Command("cf", args...)
		command.Stdout = GinkgoWriter
		command.Stderr = GinkgoWriter
		return command.Run()
	}

	BeforeEach(func() {
		app = cutlass.New(filepath.Join(bpDir, "fixtures", "with_dynatrace"))
		app.SetEnv("BP_DEBUG", "true")
		Expect(app.PushNoStart()).To(Succeed())
	})
	AfterEach(func() {
		app = DestroyApp(app)
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
		Expect(RunCf("cups", serviceName, "-p", `{"apitoken":"TOKEN","apiurl":"https://s3.amazonaws.com/dt-paas","environmentid":"envid"}`)).To(Succeed())
		Expect(RunCf("bind-service", app.Name, serviceName)).To(Succeed())
		Expect(RunCf("start", app.Name)).To(Succeed())
		ConfirmRunning(app)
		Expect(app.ConfirmBuildpack(buildpackVersion)).To(Succeed())

		By("initializing dynatrace agent")
		Expect(app.Stdout.String()).To(ContainSubstring("Initializing"))

		By("detecting single dynatrace service")
		Expect(app.Stdout.String()).To(ContainSubstring("Found one matching Dynatrace service"))

		By("downloading dynatrace agent")
		Expect(app.Stdout.String()).To(ContainSubstring("Downloading Dynatrace PAAS-Agent Installer"))

		By("extracting dynatrace agent")
		Expect(app.Stdout.String()).To(ContainSubstring("Extracting Dynatrace PAAS-Agent"))

		By("removing dynatrace agent installer")
		Expect(app.Stdout.String()).To(ContainSubstring("Removing Dynatrace PAAS-Agent Installer"))

		By("adding environment vars")
		Expect(app.Stdout.String()).To(ContainSubstring("Adding Dynatrace specific Environment Vars"))

		By("LD_PRELOAD settings")
		Expect(app.Stdout.String()).To(ContainSubstring("Adding Dynatrace LD_PRELOAD settings"))

		By("checking for manifest.json fallback")
		Expect(app.Stdout.String()).To(ContainSubstring("Agent path not found in manifest.json, using fallback"))
	})

	It("Deploy app with multiple dynatrace services", func() {
		serviceName = "dynatrace-service-" + cutlass.RandStringRunes(20)
		Expect(RunCf("cups", serviceName, "-p", `{"apitoken":"TOKEN","apiurl":"https://s3.amazonaws.com/dt-paas","environmentid":"envid"}`)).To(Succeed())
		Expect(RunCf("bind-service", app.Name, serviceName)).To(Succeed())

		serviceName2 = "dynatrace-service-" + cutlass.RandStringRunes(20)
		Expect(RunCf("cups", serviceName2, "-p", `{"apitoken":"TOKEN","apiurl":"https://s3.amazonaws.com/dt-paas","environmentid":"envid_dupe"}`)).To(Succeed())
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
		Expect(RunCf("cups", serviceName, "-p", `{"apitoken":"TOKEN","apiurl":"https://s3.amazonaws.com/dt-paasFAIL","environmentid":"envid","skiperrors":"true"}`)).To(Succeed())
		Expect(RunCf("bind-service", app.Name, serviceName)).To(Succeed())

		By("deployment should not fail")
		Expect(RunCf("start", app.Name)).To(Succeed())
		Expect(app.ConfirmBuildpack(buildpackVersion)).To(Succeed())

		By("initializing dynatrace agent")
		Expect(app.Stdout.String()).To(ContainSubstring("Initializing"))

		By("detecting single dynatrace service")
		Expect(app.Stdout.String()).To(ContainSubstring("Found one matching Dynatrace service"))

		By("downloading dynatrace agent")
		Expect(app.Stdout.String()).To(ContainSubstring("Downloading Dynatrace PAAS-Agent Installer"))

		By("download retries work")
		Expect(app.Stdout.String()).To(ContainSubstring("Error during installer download, retrying in 4 seconds"))
		Expect(app.Stdout.String()).To(ContainSubstring("Error during installer download, retrying in 5 seconds"))
		Expect(app.Stdout.String()).To(ContainSubstring("Error during installer download, retrying in 7 seconds"))

		By("should exit gracefully")
		Expect(app.Stdout.String()).To(ContainSubstring("Error during installer download, skipping installation"))

		By("no further installer logs")
		Expect(app.Stdout.String()).ToNot(ContainSubstring("Extracting Dynatrace PAAS-Agent"))
	})

	It("Deploy app with single dynatrace service, wrong url and skiperrors not set", func() {
		serviceName = "dynatrace-service-" + cutlass.RandStringRunes(20)
		Expect(RunCf("cups", serviceName, "-p", `{"apitoken":"TOKEN","apiurl":"https://s3.amazonaws.com/dt-paasFAIL","environmentid":"envid"}`)).To(Succeed())
		Expect(RunCf("bind-service", app.Name, serviceName)).To(Succeed())

		By("deployment should fail")
		Expect(RunCf("start", app.Name)).ToNot(Succeed())
		Expect(app.ConfirmBuildpack(buildpackVersion)).To(Succeed())

		By("initializing dynatrace agent")
		Eventually(app.Stdout.String).Should(ContainSubstring("Initializing"))

		By("detecting single dynatrace service")
		Expect(app.Stdout.String()).To(ContainSubstring("Found one matching Dynatrace service"))

		By("downloading dynatrace agent")
		Expect(app.Stdout.String()).To(ContainSubstring("Downloading Dynatrace PAAS-Agent Installer"))

		By("download retries work")
		Expect(app.Stdout.String()).To(ContainSubstring("Error during installer download, retrying in 4 seconds"))
		Expect(app.Stdout.String()).To(ContainSubstring("Error during installer download, retrying in 5 seconds"))
		Expect(app.Stdout.String()).To(ContainSubstring("Error during installer download, retrying in 7 seconds"))

		By("error during agent download")
		Expect(app.Stdout.String()).To(ContainSubstring("ERROR: Dynatrace agent download failed"))

		By("no further installer logs")
		Expect(app.Stdout.String()).ToNot(ContainSubstring("Extracting Dynatrace PAAS-Agent"))
	})
})
