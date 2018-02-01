package integration_test

import (
	"os"
	"path/filepath"

	"github.com/cloudfoundry/libbuildpack"
	"github.com/cloudfoundry/libbuildpack/cutlass"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("CF PHP Buildpack", func() {
	var app *cutlass.App
	AfterEach(func() { app = DestroyApp(app) })

	Context("deploying a basic PHP app using the latest PHP7", func() {
		BeforeEach(func() {
			app = cutlass.New(filepath.Join(bpDir, "fixtures", "php_7_latest"))
			app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))
		})

		It("installs the latest version of PHP7", func() {
			var php struct {
				Version70 string `json:"PHP_70_LATEST"`
			}
			Expect((&libbuildpack.JSON{}).Load(filepath.Join(bpDir, "defaults", "options.json"), &php)).To(Succeed())

			PushAppAndConfirm(app)

			Expect(app.Stdout.String()).To(ContainSubstring("Installing PHP"))
			Expect(app.Stdout.String()).To(ContainSubstring("PHP " + php.Version70))
		})
	})
})
