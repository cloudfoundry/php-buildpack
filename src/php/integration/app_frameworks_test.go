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

func testAppFrameworks(platform switchblade.Platform, fixtures string) func(*testing.T, spec.G, spec.S) {
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

		context("CakePHP", func() {
			it("builds and runs the app", func() {
				deployment, _, err := platform.Deploy.
					WithEnv(map[string]string{
						"COMPOSER_GITHUB_OAUTH_TOKEN": os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"),
					}).
					WithStartCommand(`/app/bin/cake migrations migrate && /app/.bp/bin/start`).
					Execute(name, filepath.Join(fixtures, "cake"))
				Expect(err).NotTo(HaveOccurred())

				Eventually(deployment).Should(Serve(SatisfyAll(
					ContainSubstring("CakePHP: the rapid development PHP framework"),
					Not(ContainSubstring("Missing Database Table")),
				)))

				Eventually(deployment).Should(Serve(
					ContainSubstring("Add User"),
				).WithEndpoint("/users/add"))
			})
		})

		context("Laminas", func() {
			it("builds and runs the app", func() {
				deployment, _, err := platform.Deploy.
					WithEnv(map[string]string{
						"COMPOSER_GITHUB_OAUTH_TOKEN": os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"),
					}).
					Execute(name, filepath.Join(fixtures, "laminas"))
				Expect(err).NotTo(HaveOccurred())

				Eventually(deployment).Should(Serve(
					ContainSubstring("Laminas MVC Skeleton Application"),
				))
			})
		})
	}
}
