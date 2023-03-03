package integration_test

import (
	"os"

	"github.com/cloudfoundry/libbuildpack/cutlass"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("CF PHP Buildpack", func() {
	var app *cutlass.App
	AfterEach(func() {
		app = DestroyApp(app)
	})

	It("deploying a symfony 5 app with locally-vendored dependencies", func() {
		SkipUnlessCached()

		app = cutlass.New(Fixtures("symfony_5_local_deps"))
		app.Buildpacks = []string{"php_buildpack"}
		PushAppAndConfirm(app)

		By("dynamically generates the content for the root route")
		Expect(app.GetBody("/")).To(ContainSubstring("Welcome to the <strong>Symfony Demo</strong> application"))
	})

	It("deploying a symfony 5 app with remotely-sourced dependencies", func() {
		SkipUnlessUncached()

		app = cutlass.New(Fixtures("symfony_5_remote_deps"))
		app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))
		app.Buildpacks = []string{"php_buildpack"}
		PushAppAndConfirm(app)

		By("dynamically generates the content for the root route")
		Expect(app.GetBody("/")).To(ContainSubstring("Welcome to the <strong>Symfony Demo</strong> application"))
	})

})
