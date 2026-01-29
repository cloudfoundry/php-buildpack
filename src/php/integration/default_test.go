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
				Expect(err).NotTo(HaveOccurred(), logs.String)

				Expect(logs).To(ContainLines(MatchRegexp(`Installing PHP [\d\.]+`)))
				Expect(logs).To(ContainSubstring("PHP buildpack supply phase complete"))

				Expect(logs).NotTo(ContainSubstring("WARNING: A version of PHP has been specified in both `composer.json` and `./bp-config/options.json`."))
				Expect(logs).NotTo(ContainSubstring("WARNING: The version defined in `composer.json` will be used."))

				if settings.Cached {
					Expect(logs).To(ContainLines(MatchRegexp(`Copy \[.*/dependencies/.*/php_[\d\.]+_linux_x64_.*\.tgz\]`)))
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
				if settings.Platform == "docker" {
					t.Skip("Git URL buildpacks require CF platform - Docker platform cannot clone git repos")
				}

				deployment, logs, err := platform.Deploy.
					WithBuildpacks("https://github.com/cloudfoundry/dotnet-core-buildpack#master", "php_buildpack").
					Execute(name, filepath.Join(fixtures, "dotnet_core_as_supply_app"))
				Expect(err).NotTo(HaveOccurred(), logs.String)

				Expect(logs).To(ContainSubstring("Supplying Dotnet Core"), logs.String)

				Eventually(deployment).Should(Serve(
					MatchRegexp(`dotnet: \d+\.\d+\.\d+`),
				), logs.String)
			})
		})

		context("PHP app deployed via git URL buildpack", func() {
			it("successfully builds without release YAML pollution", func() {
				if settings.Platform == "docker" {
					t.Skip("Git URL buildpacks require CF platform - Docker platform cannot clone git repos")
				}

				deployment, logs, err := platform.Deploy.
					WithBuildpacks("https://github.com/cloudfoundry/php-buildpack.git#fix-rewrite-binary-compilation").
					WithEnv(map[string]string{
						"BP_DEBUG": "1",
					}).
					Execute(name, filepath.Join(fixtures, "default"))

				Expect(err).NotTo(HaveOccurred(), logs.String)

				Expect(logs).To(ContainLines(MatchRegexp(`Installing PHP [\d\.]+`)))
				Expect(logs).To(ContainSubstring("PHP buildpack supply phase complete"))

				Eventually(deployment).Should(Serve(
					ContainSubstring("PHP Version"),
				))
			})
		})

	}
}
