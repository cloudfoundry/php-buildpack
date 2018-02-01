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

	Context("deploying a PHP app with .profile.d directory", func() {
		BeforeEach(func() {
			app = cutlass.New(filepath.Join(bpDir, "fixtures", "with_profile_d"))
			app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))
			PushAppAndConfirm(app)
		})

		It("sets environment variables via .profile.d script", func() {
			Expect(app.GetBody("/")).To(ContainSubstring("TEST_ENV_VAR"))
		})
	})

	It("deploying a PHP app with .profile script", func() {
		if !ApiGreaterThan("2.75.0") {
			Skip(".profile script functionality not supported before CF API version 2.75.0")
		}

		app = cutlass.New(filepath.Join(bpDir, "fixtures", "with_profile_script"))
		app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))
		PushAppAndConfirm(app)

		By("sets environment variables via .profile script")
		Expect(app.GetBody("/")).To(ContainSubstring("PROFILE_SCRIPT_IS_PRESENT_AND_RAN"))

		By("does not let me view the .profile script")
		_, headers, err := app.Get("/.profile", nil)
		Expect(err).NotTo(HaveOccurred())
		Expect(headers).To(HaveKeyWithValue("StatusCode", []string{"404"}))
	})
})
