package integration_test

import (
	"os/exec"
	"path/filepath"

	"github.com/cloudfoundry/libbuildpack/cutlass"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("CF PHP Buildpack", func() {
	var app *cutlass.App
	RunCf := func(args ...string) error {
		command := exec.Command("cf", args...)
		command.Stdout = GinkgoWriter
		command.Stderr = GinkgoWriter
		return command.Run()
	}

	AfterEach(func() {
		app = DestroyApp(app)
		_ = RunCf("delete-service", "-f", "with_appdynamics")
	})

	It("configures appdynamics", func() {
		app = cutlass.New(filepath.Join(bpDir, "fixtures", "with_appdynamics"))
		app.SetEnv("BP_DEBUG", "true")
		Expect(app.PushNoStart()).To(Succeed())

		Expect(RunCf("cups", "with_appdynamics", "-p", `{"account-access-key":"fe244dc3-372f-4d36-83b0-379973103c5c","account-name":"customer1","host-name":"testhostname.com","port":"8090","ssl-enabled":"False"}`)).To(Succeed())
		Expect(RunCf("bind-service", app.Name, "with_appdynamics")).To(Succeed())
		Expect(RunCf("start", app.Name)).To(Succeed())

		ConfirmRunning(app)
		Expect(app.ConfirmBuildpack(buildpackVersion)).To(Succeed())

		By("should compile appdynamics agent", func() {
			Eventually(app.Stdout.String).Should(ContainSubstring("AppDynamics service detected, beginning compilation"))
		})

		By("should configure appdynamics agent", func() {
			Eventually(app.Stdout.String).Should(ContainSubstring("Running AppDynamics extension method _configure"))
		})

		By("should set credentials for appdynamics agent", func() {
			Eventually(app.Stdout.String).Should(ContainSubstring("Setting AppDynamics credentials info..."))
		})

		By("should download appdynamics agent", func() {
			Eventually(app.Stdout.String).Should(ContainSubstring("Downloading AppDynamics package..."))
		})

		By("should install appdynamics agent", func() {
			Eventually(app.Stdout.String).Should(ContainSubstring("Installing AppDynamics package..."))
		})
	})
})
