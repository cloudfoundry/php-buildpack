package integration_test

import (
	"os"
	"time"

	"github.com/cloudfoundry/libbuildpack/cutlass"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("CF PHP Buildpack", func() {
	var app *cutlass.App
	AfterEach(func() { app = DestroyApp(app) })
	JustBeforeEach(func() {
		app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))
	})

	Context("deploying a basic PHP72 app with custom conf files in php.ini.d dir in app root", func() {
		BeforeEach(func() {
			app = cutlass.New(Fixtures("php_72_with_php_ini_d"))
		})

		It("sets custom configurations", func() {
			PushAppAndConfirm(app)
			Expect(app.GetBody("/")).To(ContainSubstring("teststring"))
			Expect(app.Stdout.String()).To(ContainSubstring("PHP 7.2"))
		})
	})

	Context("deploying an app with an invalid extension in php.ini.d dir", func() {
		BeforeEach(func() {
			app = cutlass.New(Fixtures("invalid_php_ini_d"))
		})

		It("fails during staging", func() {
			Expect(app.Push()).ToNot(Succeed())
			Expect(app.ConfirmBuildpack(buildpackVersion)).To(Succeed())

			Eventually(app.Stdout.String, 10*time.Second).Should(ContainSubstring("The extension 'meatball' is not provided by this buildpack."))
		})
	})
})
