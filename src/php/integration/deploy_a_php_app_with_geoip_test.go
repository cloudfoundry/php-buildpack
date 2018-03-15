package integration_test

import (
	"os"
	"path/filepath"

	"github.com/cloudfoundry/libbuildpack/cutlass"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("CF PHP Buildpack", func() {
	BeforeEach(SkipNotYetImplementedFunctionality)
	var app *cutlass.App
	AfterEach(func() { app = DestroyApp(app) })

	It("deploying a basic PHP app", func() {
		app = cutlass.New(filepath.Join(bpDir, "fixtures", "php_geoip_app"))
		app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))
		PushAppAndConfirm(app)

		By("is able to use the geoip databases")
		body, err := app.GetBody("/")
		Expect(err).ToNot(HaveOccurred())

		Expect(body).To(ContainSubstring("Avail: 1"))
		Expect(body).To(ContainSubstring("Info: GEO-106FREE"))
		Expect(body).To(ContainSubstring("Country: US"))

		By("has downloaded geoip dbs")
		Expect(log(app)).To(ContainSubstring("Downloading Geoip Databases."))
		Expect(log(app)).To(ContainSubstring("file_name: GeoLiteCityv6.dat"))
		Expect(log(app)).To(ContainSubstring("file_name: GeoIPv6.dat"))
		Expect(log(app)).To(ContainSubstring("file_name: GeoLiteCountry.dat"))
		Expect(log(app)).To(ContainSubstring("file_name: GeoLiteASNum.dat"))
		Expect(log(app)).To(ContainSubstring("file_name: GeoLiteCity.dat"))
	})

	Context("in offline mode", func() {
		BeforeEach(func() { SkipUnlessCached() })

		It("downloads the binaries directly from the buildpack", func() {
			app = cutlass.New(filepath.Join(bpDir, "fixtures", "php_geoip_app_local_deps"))
			app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))
			PushAppAndConfirm(app)
			Expect(log(app)).To(ContainSubstring("Copying Geoip Databases from App."))
		})

		AssertNoInternetTraffic("php_geoip_app_local_deps")
	})
})
