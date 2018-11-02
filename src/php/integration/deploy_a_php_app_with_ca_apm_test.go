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
	var serviceName string
	RunCf := func(args ...string) error {
		command := exec.Command("cf", args...)
		command.Stdout = GinkgoWriter
		command.Stderr = GinkgoWriter
		return command.Run()
	}

	BeforeEach(func() {
		serviceName = "caapm-test-service" + cutlass.RandStringRunes(20)
	})

	AfterEach(func() {
		app = DestroyApp(app)
		_ = RunCf("delete-service", "-f", serviceName)
	})

	It("configures ca apm", func() {
		app = cutlass.New(filepath.Join(bpDir, "fixtures", "with_ca_apm"))
		app.SetEnv("BP_DEBUG", "true")
		Expect(app.PushNoStart()).To(Succeed())

		Expect(RunCf("cups", serviceName, "-p", `{"collport":"9009","collhost":"abcd.ca.com","appname":"my-integration-test"}`)).To(Succeed())
		Expect(RunCf("bind-service", app.Name, serviceName)).To(Succeed())
		Expect(RunCf("start", app.Name)).To(Succeed())

		ConfirmRunning(app)
		Expect(app.ConfirmBuildpack(buildpackVersion)).To(Succeed())

		By("load service info check", func() {
			Eventually(app.Stdout.String).Should(ContainSubstring("Loading service info to find CA APM Service"))
			Eventually(app.Stdout.String).Should(ContainSubstring("Using the first CA APM service present in user-provided services"))
			Eventually(app.Stdout.String).Should(ContainSubstring("IA Agent Host [abcd.ca.com]"))
			Eventually(app.Stdout.String).Should(ContainSubstring("IA Agent Port [9009]"))
			Eventually(app.Stdout.String).Should(ContainSubstring("PHP App Name [my-integration-test]"))
		})

		By("downloading CA APM binaries", func() {
			Eventually(app.Stdout.String).Should(ContainSubstring("Downloading CA APM PHP Agent package..."))
			Eventually(app.Stdout.String).Should(ContainSubstring("Downloaded CA APM PHP Agent package"))
		})

		By("Running CA APM installer script", func() {
			Eventually(app.Stdout.String).Should(ContainSubstring("Compiling CA APM PHP Agent install commands"))
			Eventually(app.Stdout.String).Should(ContainSubstring("Installing CA APM PHP Agent"))
			Eventually(app.Stdout.String).Should(ContainSubstring("Installing CA APM PHP Probe Agent..."))
			Eventually(app.Stdout.String).Should(ContainSubstring("Installation Status : Success"))
		})

		By("modifying php ini", func() {
			Eventually(app.Stdout.String).Should(ContainSubstring("Updating PHP INI file with CA APM PHP Agent Properties"))
		})

		By("installation complete", func() {
			Eventually(app.Stdout.String).Should(ContainSubstring("CA APM PHP Agent installation completed"))
		})
	})
})
