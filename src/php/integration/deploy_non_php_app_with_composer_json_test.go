package integration_test

import (
	"path/filepath"
	"time"

	"github.com/cloudfoundry/libbuildpack/cutlass"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("CF PHP Buildpack", func() {
	var app *cutlass.App
	AfterEach(func() { app = DestroyApp(app) })

	Context("deploying a non php app with composer.json file", func() {
		BeforeEach(func() {
			app = cutlass.New(filepath.Join(bpDir, "fixtures", "non_php_composer_json"))
		})
		It("does not detect the app", func() {
			Expect(app.Push()).ToNot(Succeed())
			Eventually(app.Stdout.String, 10*time.Second).Should(ContainSubstring("None of the buildpacks detected a compatible application"))
		})
	})
})
