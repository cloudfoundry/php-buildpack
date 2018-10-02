package integration_test

import (
	"os"
	"path/filepath"

	"github.com/cloudfoundry/libbuildpack/cutlass"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("deploying a basic PHP app using Argon2", func() {
	var app *cutlass.App
	AfterEach(func() { app = DestroyApp(app) })

	Context("when PHP has been compiled with argon2", func() {
		BeforeEach(func() {
			app = cutlass.New(filepath.Join(bpDir, "fixtures", "with_argon2"))
			app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))
			PushAppAndConfirm(app)
		})

		It("prints a password hash", func() {
			Expect(app.GetBody("/")).To(ContainSubstring(`password hash of "hello-world": $argon2i$v=19$m=1024,t=2`))
		})
	})
})
