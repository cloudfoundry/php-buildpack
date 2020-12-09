package integration_test

import (
	"os"

	"github.com/cloudfoundry/libbuildpack/cutlass"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("invalid PHP versions", func() {
	var app *cutlass.App
	AfterEach(func() { app = DestroyApp(app) })

	It("version is specified using .bp-config/options.json", func() {
		app = cutlass.New(Fixtures("invalid_php_version"))
		app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))

		By("stages successfully")
		PushAppAndConfirm(app)
		Expect(app.GetBody("/")).To(ContainSubstring("PHP Version 7.4"))

		By("logs that an invalid version was provided")
		Expect(app.Stdout.String()).To(ContainSubstring("WARNING: PHP version 7.34.5 not available, using default version (7.4."))

		By("uses the default PHP version")
		Expect(app.Stdout.String()).To(ContainSubstring("PHP 7.4"))
	})

	It("version is specified using composer.json", func() {
		app = cutlass.New(Fixtures("invalid_php_version_composer"))
		app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))

		By("does not stage successfully")
		Expect(app.Push()).ToNot(Succeed())
		Expect(app.ConfirmBuildpack(buildpackVersion)).To(Succeed())

		By("logs that an invalid version was provided")
		Expect(app.Stdout.String()).To(ContainSubstring("WARNING: PHP version >=9.7.0 not available, using default version (7.4."))

		By("uses the default PHP version")
		Expect(app.Stdout.String()).To(ContainSubstring("PHP 7.4"))
	})
})
