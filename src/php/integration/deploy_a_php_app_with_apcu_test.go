package integration_test

import (
	"os"
	"path/filepath"

	"github.com/cloudfoundry/libbuildpack/cutlass"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("deploying a basic PHP app using APCu module", func() {
	var app *cutlass.App
	AfterEach(func() { app = DestroyApp(app) })

	Context("after the APCu module has been loaded into PHP", func() {
		It("caches a variable using APCu", func() {
			app = cutlass.New(filepath.Join(bpDir, "fixtures", "with_apcu"))
			app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))
			PushAppAndConfirm(app)

			Expect(app.GetBody("/")).To(ContainSubstring("I'm an apcu cached variable"))
		})
	})
})
