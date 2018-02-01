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
	JustBeforeEach(func() {
		app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))
	})

	Context("deploying a basic PHP5 app with custom conf files in php.ini.d dir in app root", func() {
		BeforeEach(func() {
			app = cutlass.New(filepath.Join(bpDir, "fixtures", "php_5_with_php_ini_d"))
		})

		It("sets custom configurations", func() {
			PushAppAndConfirm(app)
			Expect(app.GetBody("/")).To(ContainSubstring("teststring"))
		})
	})

	Context("deploying a basic PHP7 app with custom conf files in php.ini.d dir in app root", func() {
		BeforeEach(func() {
			app = cutlass.New(filepath.Join(bpDir, "fixtures", "php_7_with_php_ini_d"))
		})

		It("sets custom configurations", func() {
			PushAppAndConfirm(app)
			Expect(app.GetBody("/")).To(ContainSubstring("teststring"))
		})
	})

	Context("deploying a basic PHP71 app with custom conf files in php.ini.d dir in app root", func() {
		BeforeEach(func() {
			app = cutlass.New(filepath.Join(bpDir, "fixtures", "php_71_with_php_ini_d"))
		})

		It("sets custom configurations", func() {
			PushAppAndConfirm(app)
			Expect(app.GetBody("/")).To(ContainSubstring("teststring"))
		})
	})

	Context("deploying an app with an invalid extension in php.ini.d dir", func() {
		BeforeEach(func() {
			app = cutlass.New(filepath.Join(bpDir, "fixtures", "invalid_php_ini_d"))
		})

		It("fails during staging", func() {
			Expect(app.Push()).ToNot(Succeed())
			Expect(app.ConfirmBuildpack(buildpackVersion)).To(Succeed())

			Eventually(app.Stdout.String, 10*time.Second).Should(ContainSubstring("The extension 'meatball' is not provided by this buildpack."))
		})
	})
})
