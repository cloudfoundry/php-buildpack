package integration_test

import (
	"path/filepath"
	"testing"

	"github.com/cloudfoundry/switchblade"
	"github.com/sclevine/spec"

	. "github.com/cloudfoundry/switchblade/matchers"
	. "github.com/onsi/gomega"
)

func testPythonExtension(platform switchblade.Platform, fixtures string) func(*testing.T, spec.G, spec.S) {
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

		context("app with buildpack-supported custom extension in python", func() {
			it.Pend("builds and runs the app", func() {
				// NOTE: Python-based user extensions (.extensions/<name>/extension.py) are NOT supported
				// in the Go-based v5 buildpack. The Python extension system allowed arbitrary code execution
				// and complex build-time operations (downloading binaries, file manipulation, etc).
				//
				// The v5 buildpack provides JSON-based user extensions instead (.extensions/<name>/extension.json)
				// which support:
				//   - preprocess_commands: Run shell commands at container startup
				//   - service_commands: Long-running background processes
				//   - service_environment: Environment variables
				//
				// JSON extensions are simpler, more secure, and sufficient for most use cases.
				// For complex build-time operations (like installing PHPMyAdmin), users should:
				//   1. Use a multi-buildpack approach with separate buildpacks for each component
				//   2. Include pre-built binaries in the app repository
				//   3. Use preprocess_commands to download/setup at runtime (if acceptable)
				//
				// See docs/user-extensions.md for JSON extension documentation.
				// See fixtures/json_extension for a working example.
				_, logs, err := platform.Deploy.
					Execute(name, filepath.Join(fixtures, "python_extension"))
				Expect(err).NotTo(HaveOccurred())

				Eventually(logs).Should(SatisfyAll(
					ContainSubstring("Installing PHPMyAdmin 5.2.1"),
				))
			})
		})

		context("app with JSON-based user extension", func() {
			it("loads and runs the extension", func() {
				deployment, logs, err := platform.Deploy.
					WithEnv(map[string]string{
						"BP_DEBUG": "1",
					}).
					Execute(name, filepath.Join(fixtures, "json_extension"))
				Expect(err).NotTo(HaveOccurred(), logs.String)

				// Verify user extension was loaded during staging
				Expect(logs).To(ContainSubstring("Loaded user extension: myapp-initializer"))

				// Verify the app runs and shows extension effects
				Eventually(deployment).Should(Serve(SatisfyAll(
					ContainSubstring("JSON Extension Test"),
					ContainSubstring("Extension Loaded: YES"),
					ContainSubstring("Extension Version: 1.0.0"),
					ContainSubstring("Marker File: myapp-extension-loaded"),
				)))
			})
		})

	}
}
