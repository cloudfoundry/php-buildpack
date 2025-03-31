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
			Expect(platform.Delete.Execute(name)).To(Succeed())
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
					ContainSubstring("Downloading vlucas/phpdotenv"),
					ContainSubstring("Installing vlucas/phpdotenv"),
					ContainSubstring("-----> Using custom GitHub OAuth token in $COMPOSER_GITHUB_OAUTH_TOKEN"),
				))

				Eventually(deployment).Should(Serve(
					ContainSubstring("<p style='text-align: center'>Powered By Cloud Foundry Buildpacks</p>"),
				))
			})
		})

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
