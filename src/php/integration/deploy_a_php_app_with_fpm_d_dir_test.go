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

	Context("deploying a basic PHP5 app with custom conf files in fpm.d dir in app root", func() {
		It("sets custom configurations", func() {
			app = cutlass.New(filepath.Join(bpDir, "fixtures", "php_5_with_fpm_d"))
			app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))
			PushAppAndConfirm(app)

			body, err := app.GetBody("/")
			Expect(err).ToNot(HaveOccurred())

			Expect(body).To(ContainSubstring("TEST_WEBDIR == htdocs"))
			Expect(body).To(ContainSubstring("TEST_HOME_PATH == /home/vcap/app/test/path"))
		})
	})

	Context("deploying a PHP7 app with custom conf files in fpm.d dir in app root", func() {
		It("sets custom configurations", func() {
			app = cutlass.New(filepath.Join(bpDir, "fixtures", "php_7_with_fpm_d"))
			app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))
			PushAppAndConfirm(app)

			body, err := app.GetBody("/")
			Expect(err).ToNot(HaveOccurred())

			Expect(body).To(ContainSubstring("TEST_WEBDIR == htdocs"))
			Expect(body).To(ContainSubstring("TEST_HOME_PATH == /home/vcap/app/test/path"))
		})
	})

	Context("deploying a PHP71 app with custom conf files in fpm.d dir in app root", func() {
		It("sets custom configurations", func() {
			app = cutlass.New(filepath.Join(bpDir, "fixtures", "php_71_with_fpm_d"))
			app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))
			PushAppAndConfirm(app)

			body, err := app.GetBody("/")
			Expect(err).ToNot(HaveOccurred())

			Expect(body).To(ContainSubstring("TEST_WEBDIR == htdocs"))
			Expect(body).To(ContainSubstring("TEST_HOME_PATH == /home/vcap/app/test/path"))
		})
	})
})
