package integration_test

import (
	"os"
	"path/filepath"

	"github.com/cloudfoundry/libbuildpack/cutlass"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("invalid PHP versions", func() {
	var app *cutlass.App
	AfterEach(func() { app = DestroyApp(app) })

	It("version is specified using .bp-config/options.json", func() {
		app = cutlass.New(filepath.Join(bpDir, "fixtures", "invalid_php_version"))
		app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))

		By("stages successfully")
		PushAppAndConfirm(app)
		Expect(app.GetBody("/")).To(ContainSubstring("PHP Version 5.6"))

		By("logs that an invalid version was provided")
		Expect(app.Stdout.String()).To(ContainSubstring("WARNING: PHP version 7.34.5 not available, using default version (5.6."))

		By("uses the default PHP version")
		Expect(app.Stdout.String()).To(ContainSubstring("PHP 5.6"))
	})

	It("version is specified using composer.json", func() {
		app = cutlass.New(filepath.Join(bpDir, "fixtures", "invalid_php_version_composer"))
		app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))

		By("does not stage successfully")
		Expect(app.Push()).ToNot(Succeed())
		Expect(app.ConfirmBuildpack(buildpackVersion)).To(Succeed())

		By("logs that an invalid version was provided")
		Expect(app.Stdout.String()).To(ContainSubstring("WARNING: PHP version >=9.7.0 not available, using default version (5.6."))

		By("uses the default PHP version")
		Expect(app.Stdout.String()).To(ContainSubstring("PHP 5.6"))
	})
})
