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

	BeforeEach(func() {
		app = cutlass.New(filepath.Join(bpDir, "fixtures", "with_mssql"))
		app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))
	})

	Context("deploying a basic PHP app using mssql/freetds/pdo-dblib modules", func() {
		Context("after these module has been loaded into PHP", func() {
			It("logs that dblib could not connect to the server", func() {
				PushAppAndConfirm(app)

				_, headers, err := app.Get("/", map[string]string{})
				Expect(err).ToNot(HaveOccurred())
				Expect(headers).To(HaveKeyWithValue("StatusCode", []string{"500"}))
				Eventually(app.Stdout.String, 10*time.Second).Should(ContainSubstring("PHP message: PHP Fatal error:  Uncaught exception 'PDOException'"))
				Eventually(app.Stdout.String, time.Second).Should(ContainSubstring("Unable to connect: Adaptive Server is unavailable or does not exist"))
			})
		})
	})
})
