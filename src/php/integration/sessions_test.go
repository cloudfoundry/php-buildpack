package integration_test

import (
	"path/filepath"
	"testing"

	"github.com/cloudfoundry/switchblade"
	. "github.com/cloudfoundry/switchblade/matchers"
	. "github.com/onsi/gomega"
	"github.com/sclevine/spec"
)

func testSessions(platform switchblade.Platform, fixtures string) func(*testing.T, spec.G, spec.S) {
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

		context("app bound to a redis session store", func() {
			it("writes the session configuration into the dependency php.ini", func() {
				deployment, logs, err := platform.Deploy.
					WithServices(map[string]switchblade.Service{
						"redis-sessions": {
							"hostname": "redis.example.com",
							"port":     6379,
							"password": "secret",
						},
					}).
					Execute(name, filepath.Join(fixtures, "with_sessions"))
				Expect(err).NotTo(HaveOccurred(), logs.String)

				Eventually(logs.String()).Should(SatisfyAll(
					ContainSubstring("Running extension Compile phase"),
					Not(ContainSubstring("Extension compilation failed")),
				))

				Eventually(deployment).Should(Serve(
					ContainSubstring("handler=redis|name=PHPSESSIONID"),
				))
			})
		})
	}
}
