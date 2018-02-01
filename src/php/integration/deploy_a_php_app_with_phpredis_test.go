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

	Context("deploying a basic PHP app using phpredis module", func() {
		Context("after the phpredis module has been loaded into PHP", func() {
			BeforeEach(func() {
				app = cutlass.New(filepath.Join(bpDir, "fixtures", "with_phpredis"))
				app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))
				PushAppAndConfirm(app)
			})

			It("logs that phpredis could not connect to a server", func() {
				body, headers, err := app.Get("/", nil)
				Expect(err).ToNot(HaveOccurred())
				Expect(headers).To(HaveKeyWithValue("StatusCode", []string{"500"}))
				Expect(body).To(ContainSubstring("Redis Connection with phpredis"))

				// Eventually(app.Stdout.String, 10*time.Second).Should(ContainSubstring("PHP message: PHP Fatal error:  Uncaught exception 'RedisException' with message 'Redis server went away'"))
				Eventually(app.Stdout.String, 10*time.Second).Should(ContainSubstring("PHP message: PHP Fatal error:  Uncaught RedisException: Redis server went away"))
			})
		})
	})
})
