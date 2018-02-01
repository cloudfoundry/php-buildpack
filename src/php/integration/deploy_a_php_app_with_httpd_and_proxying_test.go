package integration_test

import (
	"os"
	"path/filepath"

	"github.com/cloudfoundry/libbuildpack/cutlass"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("CF PHP Buildpack", func() {
	var app *cutlass.App
	AfterEach(func() { app = DestroyApp(app) })

	Context("deploying a basic PHP app using HTTPD as the webserver", func() {
		BeforeEach(func() {
			app = cutlass.New(filepath.Join(bpDir, "fixtures", "httpd_and_proxying"))
			app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))
			PushAppAndConfirm(app)
		})

		It("does not set the HTTP_PROXY environment variable as the Proxy header value", func() {
			body, _, err := app.Get("/", map[string]string{"Proxy": "http://example.com"})
			Expect(err).ToNot(HaveOccurred())

			Expect(body).To(ContainSubstring("HTTP_PROXY env var is: "))
			Expect(body).ToNot(ContainSubstring("example.com"))
		})
	})
})
