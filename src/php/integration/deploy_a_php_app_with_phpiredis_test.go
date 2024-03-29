package integration_test

import (
	"os"
	"time"

	"github.com/cloudfoundry/libbuildpack/cutlass"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("CF PHP Buildpack", func() {
	var app *cutlass.App
	AfterEach(func() { app = DestroyApp(app) })

	Context("deploying a basic PHP app using phpiredis module", func() {
		Context("after the phpiredis module has been loaded into PHP", func() {
			BeforeEach(func() {
				app = cutlass.New(Fixtures("with_phpiredis"))
				app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))
				PushAppAndConfirm(app)
			})

			It("logs that the approrpiate phpiredis method was invoked", func() {
				Expect(app.GetBody("/")).To(ContainSubstring("Redis Connection with phpiredis"))

				Eventually(app.Stdout.String, 10*time.Second).Should(ContainSubstring("PHP Fatal error:  Uncaught TypeError: phpiredis_command_bs(): Argument #1 ($connection) must be of type resource"))
			})
		})
	})
})
