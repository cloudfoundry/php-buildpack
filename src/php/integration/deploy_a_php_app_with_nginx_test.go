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

	Context("deploying a basic PHP app using Nginx as the webserver", func() {
		BeforeEach(func() {
			app = cutlass.New(filepath.Join(bpDir, "fixtures", "with_nginx"))
			app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))
			PushAppAndConfirm(app)
		})

		It("succeeds", func() {
			By("shows the current buildpack version for useful info")
			Expect(app.Stdout.String()).To(ContainSubstring("-------> Buildpack version " + buildpackVersion))

			By("installs nginx, the request web server")
			Expect(app.Stdout.String()).To(ContainSubstring("Installing Nginx"))

			By("logs NginX version")
			Expect(app.Stdout.String()).To(ContainSubstring("NGINX " + DefaultVersion("nginx")))

			By("the root endpoint renders a dynamic message")
			Expect(app.GetBody("/")).To(ContainSubstring("PHP Version"))
		})
	})

	AssertNoInternetTraffic("with_nginx")

	Context("using default versions", func() {
		BeforeEach(func() {
			app = cutlass.New(filepath.Join(bpDir, "fixtures", "with_nginx"))
			app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))
			app.SetEnv("BP_DEBUG", "1")
			PushAppAndConfirm(app)
		})

		It("installs the default version of nginx", func() {
			Expect(app.Stdout.String()).To(ContainSubstring(`"update_default_version" is setting [NGINX_VERSION]`))
		})
	})
})
