package integration_test

import (
	"os"
	"time"

	"github.com/cloudfoundry/libbuildpack/cutlass"
	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("When composer.json is invalid JSON", func() {
	var app *cutlass.App
	AfterEach(func() { app = DestroyApp(app) })

	It("fails to stage", func() {
		app = cutlass.New(Fixtures("composer_invalid_json"))
		app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))
		Expect(app.Push()).ToNot(Succeed())

		Eventually(app.Stdout.String, 10*time.Second).Should(ContainSubstring("-------> Buildpack version " + buildpackVersion))
		Eventually(app.Stdout.String, 10*time.Second).Should(ContainSubstring("Invalid JSON present in composer.json. Parser said"))
	})
})
