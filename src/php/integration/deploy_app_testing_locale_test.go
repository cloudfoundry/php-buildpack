package integration_test

import (
	"os"

	"github.com/cloudfoundry/libbuildpack/cutlass"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("CF PHP Buildpack", func() {
	var app *cutlass.App
	AfterEach(func() { app = DestroyApp(app) })

	Context("the application should run and emit the translated string", func() {
		BeforeEach(func() {
			app = cutlass.New(Fixtures("testing_locale"))
			app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))
			PushAppAndConfirm(app)
		})
		It("expects the app to respond to GET request", func() {
			Expect(app.GetBody("/")).To(ContainSubstring("Hello, world"))
		})
	})
})
