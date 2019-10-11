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

	Context("in offline mode", func() {
		BeforeEach(func() { SkipUnlessCached() })

		It("downloads the binaries directly from the buildpack", func() {
			app = cutlass.New(Fixtures("php_geoip_app_local_deps"))
			app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))
			PushAppAndConfirm(app)
			Expect(app.Stdout.String()).To(ContainSubstring("Copying Geoip Databases from App."))
		})

		AssertNoInternetTraffic("php_geoip_app_local_deps")
	})
})
