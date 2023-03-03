package integration_test

import (
	"github.com/cloudfoundry/libbuildpack/cutlass"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("CF PHP Buildpack", func() {
	var app *cutlass.App
	AfterEach(func() {
		app = DestroyApp(app)
	})

	Context("app has a custom extension", func() {
		BeforeEach(func() {
			app = cutlass.New(Fixtures("custom_extension"))
			PushAppAndConfirm(app)
		})
		It("deploys successfully", func() {
			Expect(app.Stdout.String()).To(ContainSubstring("Installing PHPMyAdmin 4.3.12"))
		})
	})
})
