package integration_test

import (
	"os"
	"path/filepath"
	"time"

	"github.com/cloudfoundry/libbuildpack/cutlass"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("Composer", func() {
	var app *cutlass.App
	AfterEach(func() { app = DestroyApp(app) })

	BeforeEach(func() {
		SkipUnlessUncached()

		app = cutlass.New(filepath.Join(bpDir, "fixtures", "local_dependencies"))
	})

	It("deploying an app with valid $COMPOSER_GITHUB_OAUTH_TOKEN variable set", func() {
		app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))
		PushAppAndConfirm(app)

		Eventually(app.Stdout.String, 10*time.Second).Should(ContainSubstring("-----> Using custom GitHub OAuth token in $COMPOSER_GITHUB_OAUTH_TOKEN"))
	})

	It("deploying an app with an invalid $COMPOSER_GITHUB_OAUTH_TOKEN", func() {
		app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", "badtoken123123")
		PushAppAndConfirm(app)

		Eventually(app.Stdout.String, 10*time.Second).Should(ContainSubstring("-----> The GitHub OAuth token supplied from $COMPOSER_GITHUB_OAUTH_TOKEN is invalid"))
	})
})
