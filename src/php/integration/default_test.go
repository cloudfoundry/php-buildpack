package integration_test

import (
	"net/http"
	"path/filepath"
	"testing"

	"github.com/cloudfoundry/switchblade"
	"github.com/sclevine/spec"

	. "github.com/cloudfoundry/switchblade/matchers"
	. "github.com/onsi/gomega"
)

func testDefault(platform switchblade.Platform, fixtures string) func(*testing.T, spec.G, spec.S) {
	return func(t *testing.T, context spec.G, it spec.S) {
		var (
			Expect     = NewWithT(t).Expect
			Eventually = NewWithT(t).Eventually

			name string
		)

		it.Before(func() {
			var err error
			name, err = switchblade.RandomName()
			Expect(err).NotTo(HaveOccurred())
		})

		it.After(func() {
			if t.Failed() && name != "" {
				t.Logf("❌ FAILED TEST - App/Container: %s", name)
				t.Logf("   Platform: %s", settings.Platform)
			}
			if name != "" && (!settings.KeepFailedContainers || !t.Failed()) {
				Expect(platform.Delete.Execute(name)).To(Succeed())
			}
		})

		context("default PHP web app", func() {
			it("builds and runs the app", func() {
				deployment, logs, err := platform.Deploy.
					WithEnv(map[string]string{
						"BP_DEBUG": "1",
					}).
					Execute(name, filepath.Join(fixtures, "default"))
				Expect(err).NotTo(HaveOccurred())

				Eventually(logs).Should(SatisfyAll(
					ContainLines("Installing PHP"),
					ContainLines(MatchRegexp(`PHP [\d\.]+`)),
					ContainSubstring(`"update_default_version" is setting [PHP_VERSION]`),
					ContainSubstring("DEBUG: default_version_for composer is"),

					Not(ContainSubstring("WARNING: A version of PHP has been specified in both `composer.json` and `./bp-config/options.json`.")),
					Not(ContainSubstring("WARNING: The version defined in `composer.json` will be used.")),
				))

				if settings.Cached {
					Eventually(logs).Should(
						ContainLines(MatchRegexp(`Downloaded \[file://.*/dependencies/https___buildpacks.cloudfoundry.org_dependencies_php_php.*_linux_x64_.*.tgz\] to \[/tmp\]`)),
					)
				}

				Eventually(deployment).Should(Serve(
					ContainSubstring("PHP Version"),
				))

				response, err := http.Get(deployment.ExternalURL)
				Expect(err).NotTo(HaveOccurred())
				defer response.Body.Close()
				// Does not return the version of PHP in the response headers
				Expect(response.Header).ToNot(HaveKey("X-Powered-By"))
			})
		})

		context("PHP web app with a supply buildpack", func() {
			it("builds and runs the app", func() {
				deployment, logs, err := platform.Deploy.
					WithBuildpacks("dotnet_core_buildpack", "php_buildpack").
					Execute(name, filepath.Join(fixtures, "dotnet_core_as_supply_app"))
				Expect(err).NotTo(HaveOccurred())

				Eventually(logs).Should(SatisfyAll(
					ContainSubstring("Supplying Dotnet Core"),
				))

				Eventually(deployment).Should(Serve(
					MatchRegexp(`dotnet: \d+\.\d+\.\d+`),
				))
			})
		})

		context("PHP app deployed via git URL buildpack", func() {
			it("successfully builds without release YAML pollution", func() {
				if settings.Platform == "docker" {
					t.Skip("Git URL buildpacks require CF platform - Docker platform cannot clone git repos")
				}

				deployment, logs, err := platform.Deploy.
					WithBuildpacks("https://github.com/cloudfoundry/php-buildpack.git").
					WithEnv(map[string]string{
						"BP_DEBUG": "1",
					}).
					Execute(name, filepath.Join(fixtures, "default"))

				Expect(err).NotTo(HaveOccurred(), logs.String)

				Eventually(logs).Should(SatisfyAll(
					ContainLines("Installing PHP"),
					ContainLines(MatchRegexp(`PHP [\d\.]+`)),
				))

				Eventually(deployment).Should(Serve(
					ContainSubstring("PHP Version"),
				))
			})
		})

	}
}
