package integration_test

import (
	"os"
	"path/filepath"
	"time"

	"github.com/cloudfoundry/libbuildpack/cutlass"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("Composer failures", func() {
	var app *cutlass.App
	AfterEach(func() { app = DestroyApp(app) })

	It("deploying an app with an impossible dependency in composer.json", func() {
		SkipUnlessCached()

		app = cutlass.New(filepath.Join(bpDir, "fixtures", "composer_invalid_dependency"))
		app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))
		Expect(app.Push()).ToNot(Succeed())
		Expect(app.ConfirmBuildpack(buildpackVersion)).To(Succeed())

		Eventually(app.Stdout.String, 10*time.Second).Should(ContainSubstring("-----> Composer command failed"))
	})
})
