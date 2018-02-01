package integration_test

import (
	"path/filepath"

	"github.com/cloudfoundry/libbuildpack/cutlass"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("CF PHP Buildpack", func() {
	var app *cutlass.App
	AfterEach(func() { app = DestroyApp(app) })

	Context("app has a custom extension", func() {
		BeforeEach(func() {
			app = cutlass.New(filepath.Join(bpDir, "fixtures", "custom_extension"))
			PushAppAndConfirm(app)
		})
		It("deploys successfully", func() {
			Expect(app.Stdout.String()).To(ContainSubstring("https://files.phpmyadmin.net//phpMyAdmin/4.3.12/phpMyAdmin-4.3.12-english.tar.gz"))
		})
	})
})
