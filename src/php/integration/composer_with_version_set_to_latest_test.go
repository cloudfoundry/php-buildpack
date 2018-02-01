package integration_test

import (
	"os"
	"path/filepath"

	"github.com/cloudfoundry/libbuildpack/cutlass"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("Composer with version set to 'latest'", func() {
	var app *cutlass.App
	AfterEach(func() { app = DestroyApp(app) })

	It("", func() {
		app = cutlass.New(filepath.Join(bpDir, "fixtures", "composer_latest_version"))
		app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))

		if cutlass.Cached {
			Expect(app.Push()).ToNot(Succeed())
			Expect(app.ConfirmBuildpack(buildpackVersion)).To(Succeed())
			Eventually(app.Stdout.String).Should(ContainSubstring(`"COMPOSER_VERSION": "latest" is not supported in the cached buildpack. Please vendor your preferred version of composer with your app, or use the provided default composer version.`))
		} else {
			PushAppAndConfirm(app)
			Eventually(app.Stdout.String).Should(ContainSubstring("Downloaded [https://getcomposer.org/composer.phar] to [/tmp/composer.phar]"))
		}
	})
})
