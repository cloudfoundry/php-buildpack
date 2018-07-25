package integration_test

import (
	"os"
	"path/filepath"
	"time"

	"github.com/cloudfoundry/libbuildpack/cutlass"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("CF PHP Buildpack", func() {
	var app *cutlass.App
	AfterEach(func() { app = DestroyApp(app) })

	It("PHP version is specified in both", func() {
		app = cutlass.New(filepath.Join(bpDir, "fixtures", "composer_multiple_versions"))
		app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))

		By("expects an app to be running")
		PushAppAndConfirm(app)

		By("installs the version of PHP defined in `composer.json`")
		Eventually(app.Stdout.String, 10*time.Second).Should(ContainSubstring("Installing PHP"))
		Eventually(app.Stdout.String, 10*time.Second).Should(ContainSubstring("PHP 5.6"))

		By("does not install the PHP version defined in `options.json`")
		Expect(app.Stdout.String()).NotTo(ContainSubstring("PHP 7.0"))

		By("displays a useful warning message that `composer.json` is being used over `options.json`")
		Expect(app.Stdout.String()).To(ContainSubstring("WARNING: A version of PHP has been specified in both `composer.json` and `./bp-config/options.json`."))
		Expect(app.Stdout.String()).To(ContainSubstring("WARNING: The version defined in `composer.json` will be used."))
	})

	It("PHP version is specified in neither", func() {
		// this app has a composer.json and a .bp-config/options.json, neither of which specifiy a PHP version. So we use it for this test
		app = cutlass.New(filepath.Join(bpDir, "fixtures", "php_5_all_modules_composer"))
		app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))
		app.SetEnv("BP_DEBUG", "1")

		By("expects an app to be running")
		PushAppAndConfirm(app)

		By("installs the default version of PHP")
		Eventually(app.Stdout.String, 10*time.Second).Should(ContainSubstring(`"update_default_version" is setting [PHP_VERSION]`))

		By("doesn't display a warning message")
		Expect(app.Stdout.String()).NotTo(ContainSubstring("WARNING: A version of PHP has been specified in both `composer.json` and `./bp-config/options.json`."))
		Expect(app.Stdout.String()).NotTo(ContainSubstring("WARNING: The version defined in `composer.json` will be used."))
	})

	It("PHP version is specified in composer.json but not options.json", func() {
		// this app has a composer.json and a .bp-config/options.json. Only the composer.json specifies a PHP version. So we use it for this test
		app = cutlass.New(filepath.Join(bpDir, "fixtures", "php_7_all_modules_composer"))
		app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))

		By("expects an app to be running")
		PushAppAndConfirm(app)

		By("installs the version of PHP defined in `composer.json`")
		Eventually(app.Stdout.String, 10*time.Second).Should(ContainSubstring("Installing PHP"))
		Eventually(app.Stdout.String, 10*time.Second).Should(ContainSubstring("PHP 7.0"))

		By("doesn't display a warning message")
		Expect(app.Stdout.String()).NotTo(ContainSubstring("WARNING: A version of PHP has been specified in both `composer.json` and `./bp-config/options.json`."))
		Expect(app.Stdout.String()).NotTo(ContainSubstring("WARNING: The version defined in `composer.json` will be used."))
	})
})
