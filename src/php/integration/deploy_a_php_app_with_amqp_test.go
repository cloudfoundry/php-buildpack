package integration_test

import (
	"os"
	"path/filepath"
	"time"

	"github.com/cloudfoundry/libbuildpack/cutlass"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("CF PHP Buildpack", func() {
	var app *cutlass.App
	AfterEach(func() { app = DestroyApp(app) })

	Context("deploying a basic PHP app using AMQP module", func() {
		Context("after the AMQP module has been loaded into PHP", func() {
			It("succeeds", func() {
				app = cutlass.New(filepath.Join(bpDir, "fixtures", "with_amqp"))
				app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))
				PushAppAndConfirm(app)

				By("logs that AMQP could not connect to a server", func() {
					_, headers, err := app.Get("/", nil)
					Expect(err).ToNot(HaveOccurred())
					Expect(headers["StatusCode"]).To(Equal([]string{"500"}))

					Eventually(app.Stdout.String, 10*time.Second).Should(ContainSubstring("PHP message: PHP Fatal error:  Uncaught exception 'AMQPConnectionException'"))
				})
			})
		})
	})
})
