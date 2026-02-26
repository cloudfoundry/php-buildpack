package integration_test

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/cloudfoundry/switchblade"
	"github.com/sclevine/spec"

	. "github.com/cloudfoundry/switchblade/matchers"
	. "github.com/onsi/gomega"
)

func testComposer(platform switchblade.Platform, fixtures string) func(*testing.T, spec.G, spec.S) {
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

		context("default PHP composer app", func() {
			it("builds and runs the app", func() {
				deployment, logs, err := platform.Deploy.
					WithEnv(map[string]string{
						"COMPOSER_GITHUB_OAUTH_TOKEN": os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"),
					}).
					Execute(name, filepath.Join(fixtures, "composer_default"))
				Expect(err).NotTo(HaveOccurred())

				Eventually(logs).Should(SatisfyAll(
					ContainSubstring("Installing Composer dependencies"),
				))

				if !settings.Cached {
					Eventually(logs).Should(
						ContainSubstring("-----> Using custom GitHub OAuth token in $COMPOSER_GITHUB_OAUTH_TOKEN"),
					)
				}

				Eventually(deployment).Should(Serve(
					ContainSubstring("<p style='text-align: center'>Powered By Cloud Foundry Buildpacks</p>"),
				))
			})
		})

		context("Composer app with custom path", func() {
			it("builds and runs the app", func() {
				_, logs, err := platform.Deploy.
					WithEnv(map[string]string{
						"COMPOSER_PATH":               "meatball/sub",
						"COMPOSER_GITHUB_OAUTH_TOKEN": os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"),
					}).
					Execute(name, filepath.Join(fixtures, "composer_custom_path"))
				Expect(err).NotTo(HaveOccurred())

				Eventually(logs).Should(SatisfyAll(
					ContainSubstring("Installing Composer dependencies"),
				))
			})
		})

		context("composer app with non-existent dependency", func() {
			it("fails with error", func() {
				_, logs, err := platform.Deploy.
					WithEnv(map[string]string{
						"COMPOSER_GITHUB_OAUTH_TOKEN": os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"),
					}).
					Execute(name, filepath.Join(fixtures, "composer_invalid_dependency"))
				Expect(err).To(HaveOccurred())
				Expect(err).To(MatchError(ContainSubstring("App staging failed")))

				Eventually(logs).Should(
					ContainSubstring("-----> Composer command failed"),
				)
			})
		})

		// Regression test for https://github.com/cloudfoundry/php-buildpack/issues/1220
		// In v5, pickPHPVersion incorrectly re-evaluated package-level PHP constraints from
		// composer.lock (e.g. "<8.3.0") and fell back to the default PHP version even when
		// composer.json explicitly required "^8.3". The fix restores v4 semantics: only the
		// top-level require.php in composer.json is used for version selection.
		context("composer.json requires ^8.3 with stale <8.3.0 package constraints in composer.lock", func() {
			it("selects PHP 8.3, ignoring stale package constraints in composer.lock (issue #1220)", func() {
				deployment, logs, err := platform.Deploy.
					Execute(name, filepath.Join(fixtures, "composer_83_version_selection"))
				Expect(err).NotTo(HaveOccurred(), logs.String)

				// Build log must show the composer.json constraint was read
				Expect(logs.String()).To(ContainSubstring("Composer requires PHP ^8.3"))

				// Build log must show PHP 8.3.x was installed — not the 8.1.x default
				Expect(logs.String()).To(MatchRegexp(`Installing PHP 8\.3\.\d+`))
				Expect(logs.String()).NotTo(MatchRegexp(`Installing PHP 8\.1\.\d+`))

				// The running app must confirm it is executing on PHP 8.3
				Eventually(deployment).Should(Serve(MatchRegexp(`PHP Version: 8\.3`)))
			})
		})

		if !settings.Cached {
			context("deployed with invalid COMPOSER_GITHUB_OAUTH_TOKEN", func() {
				it("logs warning", func() {
					_, logs, err := platform.Deploy.
						WithEnv(map[string]string{
							"COMPOSER_GITHUB_OAUTH_TOKEN": "badtoken123123",
						}).
						Execute(name, filepath.Join(fixtures, "composer_default"))
					Expect(err).NotTo(HaveOccurred())

					Eventually(logs.String()).Should(SatisfyAll(
						ContainSubstring("-----> The GitHub OAuth token supplied from $COMPOSER_GITHUB_OAUTH_TOKEN is invalid"),
					))
				})
			})
		}
	}
}
