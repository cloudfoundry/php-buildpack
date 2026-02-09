package integration_test

import (
	"fmt"
	"io"
	"net/http"
	"path/filepath"
	"testing"

	"github.com/cloudfoundry/switchblade"
	"github.com/sclevine/spec"

	. "github.com/cloudfoundry/switchblade/matchers"
	. "github.com/onsi/gomega"
)

func testPlaceholders(platform switchblade.Platform, fixtures string) func(*testing.T, spec.G, spec.S) {
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

		context("PHP_XX_LATEST placeholder resolution", func() {
			it("resolves {PHP_83_LATEST} in options.json to actual version", func() {
				deployment, logs, err := platform.Deploy.
					WithEnv(map[string]string{
						"BP_DEBUG": "1",
					}).
					Execute(name, filepath.Join(fixtures, "php_version_placeholder"))
				Expect(err).NotTo(HaveOccurred(), logs.String)

				// Should resolve {PHP_83_LATEST} to actual version like 8.3.30
				Expect(logs).To(ContainLines(MatchRegexp(`Installing PHP 8\.3\.\d+`)))
				Expect(logs).NotTo(ContainSubstring("Installing PHP {PHP_83_LATEST}"))
				Expect(logs).NotTo(ContainSubstring("DEPENDENCY MISSING IN MANIFEST"))
				Expect(logs).NotTo(ContainSubstring("Version {PHP_83_LATEST}"))

				Eventually(deployment).Should(Serve(
					ContainSubstring("PHP Version"),
				))

				// Verify the actual PHP version is 8.3.x
				response, err := http.Get(deployment.ExternalURL)
				Expect(err).NotTo(HaveOccurred())
				defer response.Body.Close()

				body := string(ReadAll(response.Body))
				Expect(body).To(MatchRegexp(`PHP Version 8\.3\.\d+`))
			})

			it("resolves {PHP_82_LATEST} in options.json to actual version", func() {
				deployment, logs, err := platform.Deploy.
					WithEnv(map[string]string{
						"BP_DEBUG": "1",
					}).
					Execute(name, filepath.Join(fixtures, "php_82_version_placeholder"))
				Expect(err).NotTo(HaveOccurred(), logs.String)

				// Should resolve {PHP_82_LATEST} to actual version like 8.2.29
				Expect(logs).To(ContainLines(MatchRegexp(`Installing PHP 8\.2\.\d+`)))
				Expect(logs).NotTo(ContainSubstring("Installing PHP {PHP_82_LATEST}"))

				Eventually(deployment).Should(Serve(
					ContainSubstring("PHP Version"),
				))
			})

			it("handles invalid placeholder gracefully", func() {
				_, logs, err := platform.Deploy.
					WithEnv(map[string]string{
						"BP_DEBUG": "1",
					}).
					Execute(name, filepath.Join(fixtures, "php_invalid_placeholder"))

				// Should fail with clear error message showing the invalid placeholder
				Expect(err).To(HaveOccurred())
				Expect(logs).To(ContainSubstring("Installing PHP {PHP_99_LATEST}"))
				Expect(logs).To(ContainSubstring("DEPENDENCY MISSING IN MANIFEST"))
				Expect(logs).To(ContainSubstring("Version {PHP_99_LATEST} of dependency php is not supported"))
			})
		})

		context("#{VAR} placeholder syntax (backward compatibility)", func() {
			it("resolves #{WEBDIR} in httpd.conf", func() {
				deployment, logs, err := platform.Deploy.
					WithEnv(map[string]string{
						"BP_DEBUG": "1",
					}).
					Execute(name, filepath.Join(fixtures, "httpd_hash_placeholder"))
				Expect(err).NotTo(HaveOccurred(), logs.String)

				Expect(logs).To(ContainSubstring("Installing HTTPD"))
				Expect(logs).To(ContainSubstring("PHP buildpack finalize phase complete"))

				Eventually(deployment).Should(Serve(
					ContainSubstring("PHP Version"),
				))

				// Verify httpd is serving from correct directory
				response, err := http.Get(deployment.ExternalURL)
				Expect(err).NotTo(HaveOccurred())
				defer response.Body.Close()
				Expect(response.StatusCode).To(Equal(200))
			})

			it("resolves #{LIBDIR} in custom configs", func() {
				deployment, logs, err := platform.Deploy.
					WithEnv(map[string]string{
						"BP_DEBUG": "1",
					}).
					Execute(name, filepath.Join(fixtures, "custom_libdir_hash"))
				Expect(err).NotTo(HaveOccurred(), logs.String)

				Eventually(deployment).Should(Serve(
					ContainSubstring("PHP Version"),
				))

				// Verify include_path contains the lib directory
				response, err := http.Get(fmt.Sprintf("%s/phpinfo.php", deployment.ExternalURL))
				Expect(err).NotTo(HaveOccurred())
				defer response.Body.Close()

				body := string(ReadAll(response.Body))
				Expect(body).To(ContainSubstring("/home/vcap/app/lib"))
				Expect(body).NotTo(ContainSubstring("#{LIBDIR}"))
			})

			it("supports both @{VAR} and #{VAR} syntax in same file", func() {
				deployment, logs, err := platform.Deploy.
					WithEnv(map[string]string{
						"BP_DEBUG": "1",
					}).
					Execute(name, filepath.Join(fixtures, "mixed_placeholder_syntax"))
				Expect(err).NotTo(HaveOccurred(), logs.String)

				Eventually(deployment).Should(Serve(
					ContainSubstring("PHP Version"),
				))

				// Both syntaxes should be resolved
				response, err := http.Get(deployment.ExternalURL)
				Expect(err).NotTo(HaveOccurred())
				defer response.Body.Close()

				body := string(ReadAll(response.Body))
				Expect(body).NotTo(ContainSubstring("@{"))
				Expect(body).NotTo(ContainSubstring("#{"))
			})
		})

		context("PHP extension loading with correct paths", func() {
			it("loads extensions from correct deps directory", func() {
				deployment, logs, err := platform.Deploy.
					WithEnv(map[string]string{
						"BP_DEBUG": "1",
					}).
					Execute(name, filepath.Join(fixtures, "php_extensions_test"))
				Expect(err).NotTo(HaveOccurred(), logs.String)

				Expect(logs).To(ContainSubstring("Installing PHP"))
				Expect(logs).NotTo(ContainSubstring("Unable to load dynamic library"))
				Expect(logs).NotTo(ContainSubstring("/tmp/app/php/"))

				Eventually(deployment).Should(Serve(
					ContainSubstring("PHP Version"),
				))

				// Verify extensions are loaded
				response, err := http.Get(fmt.Sprintf("%s/extensions.php", deployment.ExternalURL))
				Expect(err).NotTo(HaveOccurred())
				defer response.Body.Close()

				body := string(ReadAll(response.Body))
				// Should show extensions loaded from /home/vcap/deps/0/php/lib/php/extensions/
				Expect(body).To(ContainSubstring("bz2"))
				Expect(body).To(ContainSubstring("curl"))
				Expect(body).To(ContainSubstring("zlib"))
			})

			it("uses correct extension_dir path in php.ini", func() {
				deployment, logs, err := platform.Deploy.
					WithEnv(map[string]string{
						"BP_DEBUG": "1",
					}).
					Execute(name, filepath.Join(fixtures, "php_extension_dir_test"))
				Expect(err).NotTo(HaveOccurred(), logs.String)

				Eventually(deployment).Should(Serve(
					ContainSubstring("PHP Version"),
				))

				// Verify extension_dir is set correctly
				response, err := http.Get(fmt.Sprintf("%s/phpinfo.php", deployment.ExternalURL))
				Expect(err).NotTo(HaveOccurred())
				defer response.Body.Close()

				body := string(ReadAll(response.Body))
				// Should be /home/vcap/deps/0/php/lib/php/extensions/no-debug-non-zts-*
				Expect(body).To(MatchRegexp(`extension_dir.*\/home\/vcap\/deps\/\d+\/php\/lib\/php\/extensions`))
				Expect(body).NotTo(ContainSubstring("extension_dir</td><td class=\"v\">/tmp/app/php"))
			})
		})

		context("WEBDIR placeholder in user configs", func() {
			it("resolves WEBDIR in custom httpd.conf", func() {
				deployment, logs, err := platform.Deploy.
					WithEnv(map[string]string{
						"BP_DEBUG": "1",
					}).
					Execute(name, filepath.Join(fixtures, "custom_webdir_config"))
				Expect(err).NotTo(HaveOccurred(), logs.String)

				Expect(logs).NotTo(ContainSubstring("DocumentRoot '/home/vcap/app/#{WEBDIR}' is not a directory"))
				Expect(logs).NotTo(ContainSubstring("DocumentRoot '/home/vcap/app/@{WEBDIR}' is not a directory"))

				Eventually(deployment).Should(Serve(
					ContainSubstring("PHP Version"),
				))
			})

			it("resolves custom WEBDIR value from options.json", func() {
				deployment, logs, err := platform.Deploy.
					WithEnv(map[string]string{
						"BP_DEBUG": "1",
					}).
					Execute(name, filepath.Join(fixtures, "custom_webdir_value"))
				Expect(err).NotTo(HaveOccurred(), logs.String)

				// App has WEBDIR set to "public" in options.json
				Eventually(deployment).Should(Serve(
					ContainSubstring("Custom WEBDIR: public"),
				))
			})
		})
	}
}

// Helper function to read response body
func ReadAll(r io.Reader) []byte {
	data, _ := io.ReadAll(r)
	return data
}
