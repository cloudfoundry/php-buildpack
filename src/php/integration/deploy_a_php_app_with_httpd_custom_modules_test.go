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

	Context("deploying a basic PHP app using httpd as the webserver and a custom httpd-modules.conf", func() {
		BeforeEach(func() {
			app = cutlass.New(filepath.Join(bpDir, "fixtures", "httpd_custom_modules_conf"))
			app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))
			PushAppAndConfirm(app)
			_, _ = app.GetBody("/")
		})

		It("does not log an error about the RequestHeader command", func() {
			Expect(app.Stdout.String()).ToNot(ContainSubstring("Invalid command 'RequestHeader'"))
		})
	})
})
