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
		Expect(log(app)).To(ContainSubstring("Installing php"))
		Expect(log(app)).To(ContainSubstring("php 5.6"))

		By("does not return the version of PHP in the response headers")
		body, headers, err := app.Get("/", map[string]string{})
		Expect(err).ToNot(HaveOccurred())
		Expect(body).To(ContainSubstring("PHP Version"))
		Expect(headers).ToNot(HaveKey("X-Powered-By"))

		By("does not display a warning message about the php version config")
		Expect(log(app)).ToNot(ContainSubstring("WARNING: A version of PHP has been specified in both `composer.json` and `./bp-config/options.json`."))
		Expect(log(app)).ToNot(ContainSubstring("WARNING: The version defined in `composer.json` will be used."))

		if cutlass.Cached {
			By("downloads the binaries directly from the buildpack")
			Expect(log(app)).To(MatchRegexp(`Copy \[.*/php-5.6.\d+-linux-x64-[\da-f]+.tgz\]`))
		}
	})

	AssertNoInternetTraffic("php_app")
})
