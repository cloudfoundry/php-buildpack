package integration_test

import (
	"path/filepath"

	"github.com/cloudfoundry/libbuildpack/cutlass"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("deploying a basic PHP app with compiled modules in PHP_EXTENSIONS", func() {
	var app *cutlass.App
	AfterEach(func() { app = DestroyApp(app) })

	It("starts", func() {
		app = cutlass.New(filepath.Join(bpDir, "fixtures", "with_compiled_modules"))
		PushAppAndConfirm(app)

		By("does not log an error metioning libxml, simplexml, spl or sqlite3", func() {
			Expect(app.Stdout.String()).ToNot(ContainSubstring("The extension 'libxml' is not provided by this buildpack"))
			Expect(app.Stdout.String()).ToNot(ContainSubstring("The extension 'SimpleXML' is not provided by this buildpack"))
			Expect(app.Stdout.String()).ToNot(ContainSubstring("The extension 'sqlite3' is not provided by this buildpack"))
			Expect(app.Stdout.String()).ToNot(ContainSubstring("The extension 'SPL' is not provided by this buildpack"))
		})

		By("has the desired modules", func() {
			body, err := app.GetBody("/")
			Expect(err).ToNot(HaveOccurred())

			Expect(body).To(ContainSubstring("module_libxml"))
			Expect(body).To(ContainSubstring("module_simplexml"))
			Expect(body).To(ContainSubstring("module_sqlite3"))
			Expect(body).To(ContainSubstring("module_spl"))
		})
	})
})
