package integration_test

import (
	"path/filepath"

	"github.com/cloudfoundry/libbuildpack/cutlass"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("An app deployed specifying unsupported extensions and valid", func() {
	var app *cutlass.App
	AfterEach(func() { app = DestroyApp(app) })

	It("runs", func() {
		app = cutlass.New(filepath.Join(bpDir, "fixtures", "unsupported_extensions"))
		PushAppAndConfirm(app)

		By("should say which extensions are not supported")
		Expect(log(app)).To(ContainSubstring("The extension 'meatball' is not provided by this buildpack."))
		Expect(log(app)).To(ContainSubstring("The extension 'hotdog' is not provided by this buildpack."))

		By("should not display default php startup warning messages")
		Expect(log(app)).ToNot(ContainSubstring("PHP message: PHP Warning:  PHP Startup: Unable to load dynamic library"))

		By("should say which extensions are not supported")
		Expect(log(app)).ToNot(ContainSubstring("The extension 'curl' is not provided by this buildpack."))

		By("should load the module without issue")
		Expect(app.GetBody("/")).To(ContainSubstring("curl module has been loaded successfully"))
	})
})
