package integration_test

import (
	"fmt"
	"net/http"
	"path/filepath"
	"testing"

	"github.com/cloudfoundry/switchblade"
	"github.com/sclevine/spec"

	. "github.com/cloudfoundry/switchblade/matchers"
	. "github.com/onsi/gomega"
)

func testWebServers(platform switchblade.Platform, fixtures string) func(*testing.T, spec.G, spec.S) {
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

		context("Default PHP web server with fpm.d dir in app root", func() {
			it("builds and runs the app", func() {
				deployment, _, err := platform.Deploy.
					Execute(name, filepath.Join(fixtures, "php_with_fpm_d"))
				Expect(err).NotTo(HaveOccurred())

				Eventually(deployment).Should(Serve(SatisfyAll(
					ContainSubstring("TEST_WEBDIR == htdocs"),
					ContainSubstring("TEST_HOME_PATH == /home/vcap/app/test/path"),
				)))
			})
		})

		context("PHP app with nginx web server", func() {
			it("builds and runs the app", func() {
				deployment, logs, err := platform.Deploy.
					Execute(name, filepath.Join(fixtures, "with_nginx"))
				Expect(err).NotTo(HaveOccurred())

				Eventually(logs).Should(
					ContainSubstring("Installing Nginx"),
				)

				Eventually(deployment).Should(Serve(
					ContainSubstring("PHP Version"),
				))
			})
		})

		context("PHP app with httpd web server", func() {
			context("default app", func() {
				it("builds and runs the app", func() {
					deployment, logs, err := platform.Deploy.
						Execute(name, filepath.Join(fixtures, "with_httpd"))
					Expect(err).NotTo(HaveOccurred())

					Eventually(logs).Should(
						ContainSubstring("Installing HTTPD"),
					)

					Eventually(deployment).Should(Serve(
						ContainSubstring("PHP Version"),
					))

					// Dynamic content
					req, err := http.NewRequest("GET", deployment.ExternalURL, nil)
					Expect(err).NotTo(HaveOccurred())
					req.Header.Set("Accept-Encoding", "gzip")
					response, err := (&http.Client{}).Do(req)
					Expect(err).NotTo(HaveOccurred())
					defer response.Body.Close()

					Expect(response.StatusCode).To(Equal(http.StatusOK))
					Expect(response.Header).To(HaveKeyWithValue("Server", []string{"Apache"}))
					Expect(response.Header).To(HaveKeyWithValue("Content-Encoding", []string{"gzip"}))

					// Static content
					req, err = http.NewRequest("GET", fmt.Sprintf("%s/staticfile.html", deployment.ExternalURL), nil)
					Expect(err).NotTo(HaveOccurred())
					req.Header.Set("Accept-Encoding", "gzip")
					response, err = (&http.Client{}).Do(req)
					Expect(err).NotTo(HaveOccurred())
					defer response.Body.Close()

					Expect(response.StatusCode).To(Equal(http.StatusOK))
					Expect(response.Header).To(HaveKeyWithValue("Server", []string{"Apache"}))
					Expect(response.Header).To(HaveKeyWithValue("Content-Encoding", []string{"gzip"}))
				})
			})

			context("app with custom httpd-modules.conf", func() {
				it("builds and runs the app", func() {
					deployment, logs, err := platform.Deploy.
						Execute(name, filepath.Join(fixtures, "httpd_custom_modules_conf"))
					Expect(err).NotTo(HaveOccurred())

					Eventually(logs).Should(
						ContainSubstring("Installing HTTPD"),
					)

					Eventually(func() string {
						logs, err := deployment.RuntimeLogs()
						Expect(err).NotTo(HaveOccurred())
						return logs
					}).Should(
						Not(ContainSubstring("Invalid command 'RequestHeader'")),
					)
				})
			})
		})

	}
}
