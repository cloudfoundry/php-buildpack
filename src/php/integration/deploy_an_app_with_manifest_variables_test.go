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

	Context("deploying a composer app with post install commands", func() {
		BeforeEach(func() {
			app = cutlass.New(filepath.Join(bpDir, "fixtures", "composer_env_sniffer"))
			app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))
			PushAppAndConfirm(app)
		})
		It("logs variables from manifest.yml", func() {
			Expect(app.Stdout.String()).To(ContainSubstring("MANIFEST_VARIABLE: 'VARIABLE_IS_SET'"))
			Expect(app.Stdout.String()).To(ContainSubstring("PHP said MANIFEST_VARIABLE: VARIABLE_IS_SET"))
		})
	})
})
