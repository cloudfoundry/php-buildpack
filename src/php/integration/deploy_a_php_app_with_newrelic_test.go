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

	Context("in offline mode", func() {
		BeforeEach(SkipUnlessCached)

		It("succeeds", func() {
			app = cutlass.New(filepath.Join(bpDir, "fixtures", "with_newrelic"))
			app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))
			app.SetEnv("BP_DEBUG", "true")
			PushAppAndConfirm(app)

			By("downloads the binaries directly from the buildpack")
			Eventually(app.Stdout.String).Should(MatchRegexp(`Downloaded \[file://.*/dependencies/https___download.newrelic.com_php_agent_archive_[\d\.]+_newrelic-php5-[\d\.]+-linux\.tar\.gz\] to \[/tmp\]`))

			By("sets up New Relic")
			Eventually(app.Stdout.String).Should(ContainSubstring("Installing NewRelic"))
			Eventually(app.Stdout.String).Should(ContainSubstring("NewRelic Installed"))

			By("installs the default version of newrelic")
			Eventually(app.Stdout.String).Should(ContainSubstring("Using NewRelic default version:"))
		})

		AssertNoInternetTraffic("with_newrelic")
	})
})
