package integration_test

import (
	"path/filepath"
	"testing"

	"github.com/cloudfoundry/switchblade"
	"github.com/sclevine/spec"

	. "github.com/onsi/gomega"
)

func testStandaloneApp(platform switchblade.Platform, fixtures string) func(*testing.T, spec.G, spec.S) {
	return func(t *testing.T, context spec.G, it spec.S) {
		var (
			Expect = NewWithT(t).Expect

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

		context("APP_START_CMD with WEB_SERVER=none", func() {
			it("builds with explicit APP_START_CMD", func() {
				_, logs, err := platform.Deploy.
					WithHealthCheckType("none").
					WithEnv(map[string]string{
						"BP_DEBUG": "1",
					}).
					Execute(name, filepath.Join(fixtures, "standalone_app"))
				Expect(err).NotTo(HaveOccurred(), logs.String)

				// Verify the buildpack detected standalone mode
				Expect(logs).To(ContainSubstring("Standalone app mode: will run worker.php"))

				// Verify the finalize phase completed successfully
				Expect(logs).To(ContainSubstring("PHP buildpack finalize phase complete"))

				// Verify start script was created
				Expect(logs).To(ContainSubstring("Created start script for none"))
			})

			it("builds with auto-detected app.php", func() {
				_, logs, err := platform.Deploy.
					WithHealthCheckType("none").
					WithEnv(map[string]string{
						"BP_DEBUG": "1",
					}).
					Execute(name, filepath.Join(fixtures, "standalone_autodetect"))
				Expect(err).NotTo(HaveOccurred(), logs.String)

				// Verify the buildpack detected standalone mode and found app.php
				Expect(logs).To(ContainSubstring("Standalone app mode: will run app.php"))

				// Verify the finalize phase completed successfully
				Expect(logs).To(ContainSubstring("PHP buildpack finalize phase complete"))

				// Verify start script was created
				Expect(logs).To(ContainSubstring("Created start script for none"))
			})
		})
	}
}
