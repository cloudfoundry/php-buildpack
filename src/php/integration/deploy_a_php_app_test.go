package integration_test

import (
	"os"
	"path/filepath"

	"github.com/cloudfoundry/libbuildpack/cutlass"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("CF PHP Buildpack", func() {
	var app *cutlass.App
	AfterEach(func() { app = DestroyApp(app) })

	BeforeEach(func() {
		app = cutlass.New(filepath.Join(bpDir, "fixtures", "php_app"))
		app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))
		app.SetEnv("BP_DEBUG", "1")
	})

	It("deploying a basic PHP app", func() {
		PushAppAndConfirm(app)

		By("installs a current version of PHP")
		Expect(app.Stdout.String()).To(ContainSubstring("Installing PHP"))
		Expect(app.Stdout.String()).To(ContainSubstring("PHP 5.6"))

		By("does not return the version of PHP in the response headers")
		body, headers, err := app.Get("/", map[string]string{})
		Expect(err).ToNot(HaveOccurred())
		Expect(body).To(ContainSubstring("PHP Version"))
		Expect(headers).ToNot(HaveKey("X-Powered-By"))

		By("does not display a warning message about the php version config")
		Expect(app.Stdout.String()).ToNot(ContainSubstring("WARNING: A version of PHP has been specified in both `composer.json` and `./bp-config/options.json`."))
		Expect(app.Stdout.String()).ToNot(ContainSubstring("WARNING: The version defined in `composer.json` will be used."))

		By("installs the default version of PHP")
		Expect(app.Stdout.String()).To(ContainSubstring(`"update_default_version" is setting [PHP_VERSION]`))

		By("installs the default version of composer")
		Expect(app.Stdout.String()).To(ContainSubstring("DEBUG: default_version_for composer is"))

		if cutlass.Cached {
			By("downloads the binaries directly from the buildpack")
			Expect(app.Stdout.String()).To(MatchRegexp(`Downloaded \[file://.*/dependencies/https___buildpacks.cloudfoundry.org_dependencies_php_php-5.6.\d+-linux-x64-[\da-f]+.tgz\] to \[/tmp\]`))
		}
	})

	AssertNoInternetTraffic("php_app")
})
