package integration_test

import (
	"os"
	"path/filepath"

	"github.com/cloudfoundry/libbuildpack"
	"github.com/cloudfoundry/libbuildpack/cutlass"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

// TODO remove this file, it is pointless (see brats and other similar integration tests)
// It used to be relevant due to data inside options.json which is no longer there
var _ = PDescribe("CF PHP Buildpack", func() {
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

			Expect(log(app)).To(ContainSubstring("Installing php"))
			Expect(log(app)).To(ContainSubstring("php " + php.Version70))
		})
	})
})
