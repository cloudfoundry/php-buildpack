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

	Context("deploying a Cake application with local dependencies", func() {
		It("", func() {
			SkipUnlessCached()
			app = cutlass.New(Fixtures("cake_local_deps"))
			app.StartCommand = "$HOME/bin/cake migrations migrate && $HOME/.bp/bin/start"
			PushAppAndConfirm(app)

			body, err := app.GetBody("/")
			Expect(err).ToNot(HaveOccurred())
			Expect(body).To(ContainSubstring("CakePHP"))
			Expect(body).ToNot(ContainSubstring("Missing Database Table"))

			Expect(app.GetBody("/users")).To(ContainSubstring("List Users"))
		})

		AssertNoInternetTraffic("cake_local_deps")
	})

	Context("deploying a Cake application with remote dependencies", func() {
		It("", func() {
			SkipUnlessUncached()
			app = cutlass.New(Fixtures("cake_remote_deps"))
			app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))
			app.StartCommand = "$HOME/bin/cake migrations migrate && $HOME/.bp/bin/start"
			PushAppAndConfirm(app)

			body, err := app.GetBody("/")
			Expect(err).ToNot(HaveOccurred())
			Expect(body).To(ContainSubstring("CakePHP"))
			Expect(body).ToNot(ContainSubstring("Missing Database Table"))

			Expect(app.GetBody("/users/add")).To(ContainSubstring("Add User"))
		})
	})
})
