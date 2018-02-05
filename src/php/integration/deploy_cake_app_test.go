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

	Context("deploying a Cake application with local dependencies", func() {
		BeforeEach(SkipUnlessCached)

		It("", func() {
			app = cutlass.New(filepath.Join(bpDir, "fixtures", "cake_local_deps"))
			app.StartCommand = "$HOME/app/Console/cake schema create -y && $HOME/.bp/bin/start"
			PushAppAndConfirm(app)

			body, err := app.GetBody("/")
			Expect(err).ToNot(HaveOccurred())
			Expect(body).To(ContainSubstring("CakePHP"))
			Expect(body).ToNot(ContainSubstring("Missing Database Table"))

			Expect(app.GetBody("/users/add")).To(ContainSubstring("Add New User"))
		})

		AssertNoInternetTraffic("cake_local_deps")
	})

	Context("deploying a Cake application with remote dependencies", func() {
		BeforeEach(SkipUnlessUncached)

		It("", func() {
			app = cutlass.New(filepath.Join(bpDir, "fixtures", "cake_remote_deps"))
			app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))
			app.StartCommand = "$HOME/app/Console/cake schema create -y && $HOME/.bp/bin/start"
			PushAppAndConfirm(app)

			body, err := app.GetBody("/")
			Expect(err).ToNot(HaveOccurred())
			Expect(body).To(ContainSubstring("CakePHP"))
			Expect(body).ToNot(ContainSubstring("Missing Database Table"))
		})
	})
})
