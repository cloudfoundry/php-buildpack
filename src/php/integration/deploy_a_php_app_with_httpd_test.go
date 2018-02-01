package integration_test

import (
	"os"
	"path/filepath"
	"time"

	"github.com/cloudfoundry/libbuildpack/cutlass"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("CF PHP Buildpack", func() {
	var app *cutlass.App
	AfterEach(func() { app = DestroyApp(app) })

	Context("deploying a basic PHP app using httpd as the webserver", func() {
		BeforeEach(func() {
			app = cutlass.New(filepath.Join(bpDir, "fixtures", "with_httpd"))
			app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))
			PushAppAndConfirm(app)
		})

		It("succeeds", func() {
			By("shows the current buildpack version for useful info")
			Eventually(app.Stdout.String, 10*time.Second).Should(ContainSubstring("-------> Buildpack version " + buildpackVersion))

			By("installs httpd, the request web server")
			Eventually(app.Stdout.String, 10*time.Second).Should(ContainSubstring("Installing HTTPD"))

			By("logs the httpd version")
			Eventually(app.Stdout.String, 10*time.Second).Should(ContainSubstring("HTTPD " + DefaultVersion("httpd")))

			By("the root endpoint renders a dynamic message")
			Expect(app.GetBody("/")).To(ContainSubstring("PHP Version"))

			By("compresses dynamic content")
			_, headers, err := app.Get("/", map[string]string{"Accept-Encoding": "gzip"})
			Expect(err).ToNot(HaveOccurred())
			Expect(headers).To(HaveKeyWithValue("StatusCode", []string{"200"}))
			Expect(headers).To(HaveKeyWithValue("Server", []string{"Apache"}))
			Expect(headers).To(HaveKeyWithValue("Content-Encoding", []string{"gzip"}))

			By("compresses static content")
			_, headers, err = app.Get("/staticfile.html", map[string]string{"Accept-Encoding": "gzip"})
			Expect(err).ToNot(HaveOccurred())
			Expect(headers).To(HaveKeyWithValue("StatusCode", []string{"200"}))
			Expect(headers).To(HaveKeyWithValue("Server", []string{"Apache"}))
			Expect(headers).To(HaveKeyWithValue("Content-Encoding", []string{"gzip"}))
		})
	})

	Context("deploying a basic PHP app using httpd as the webserver", func() {
		BeforeEach(func() {
			app = cutlass.New(filepath.Join(bpDir, "fixtures", "with_httpd"))
			app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))
			app.SetEnv("BP_DEBUG", "true")
			PushAppAndConfirm(app)
		})

		It("installs the default version of httpd", func() {
			Eventually(app.Stdout.String, 10*time.Second).Should(ContainSubstring(`"update_default_version" is setting [HTTPD_VERSION]`))
		})
	})

	AssertNoInternetTraffic("with_httpd")
})
