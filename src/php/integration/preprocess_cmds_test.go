package integration_test

import (
	"path/filepath"
	"testing"

	"github.com/cloudfoundry/switchblade"
	"github.com/sclevine/spec"

	. "github.com/cloudfoundry/switchblade/matchers"
	. "github.com/onsi/gomega"
)

func testPreprocessCmds(platform switchblade.Platform, fixtures string) func(*testing.T, spec.G, spec.S) {
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

		context("ADDITIONAL_PREPROCESS_CMDS", func() {
			it("executes preprocess commands before app starts", func() {
				deployment, logs, err := platform.Deploy.
					WithEnv(map[string]string{
						"BP_DEBUG": "1",
					}).
					Execute(name, filepath.Join(fixtures, "preprocess_cmds"))
				Expect(err).NotTo(HaveOccurred(), logs.String)

				// Verify the finalize phase completed successfully
				Expect(logs).To(ContainSubstring("PHP buildpack finalize phase complete"))

				// Verify preprocess script was written (security warning is tested in unit tests)
				Expect(logs).To(ContainSubstring("Writing preprocess commands to .profile.d/preprocess.sh"))

				// The app should start and serve content
				Eventually(deployment).Should(Serve(
					ContainSubstring("ADDITIONAL_PREPROCESS_CMDS Test"),
				))

				// Verify the preprocess file was created at correct location
				Eventually(deployment).Should(Serve(
					ContainSubstring("Preprocess file found!"),
				))

				// Verify the preprocess commands actually ran by checking the markers
				Eventually(deployment).Should(Serve(
					ContainSubstring("MARKER_1_FOUND: YES"),
				))

				Eventually(deployment).Should(Serve(
					ContainSubstring("MARKER_2_FOUND: YES"),
				))

				// Verify commands executed in correct order
				Eventually(deployment).Should(Serve(
					ContainSubstring("EXECUTION_ORDER: CORRECT"),
				))

				// Verify $HOME was restored after preprocess commands
				Eventually(deployment).Should(Serve(
					ContainSubstring("HOME_RESTORED: YES"),
				))

				// Verify $HOME variable was properly rewritten to /home/vcap during preprocess
				// This is the key v4.x compatibility test - $HOME must be /home/vcap, not /home/vcap/app
				Eventually(deployment).Should(Serve(
					ContainSubstring("HOME_VAR_REWRITTEN: YES"),
				))
			})
		})
	}
}
