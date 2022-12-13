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

	It("deploying a Laminas app with locally-vendored dependencies", func() {
		app = cutlass.New(Fixtures("laminas-local-deps"))
		PushAppAndConfirm(app)

		Expect(app.GetBody("/")).To(ContainSubstring("Laminas MVC Skeleton Application"))
	})

	AssertNoInternetTraffic("laminas-local-deps")

	It("deploying a Laminas app with remote dependencies", func() {
		app = cutlass.New(Fixtures("laminas-remote-deps"))
		app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))
		PushAppAndConfirm(app)

		Expect(app.GetBody("/")).To(ContainSubstring("Laminas MVC Skeleton Application"))
	})
})
