package integration_test

import (
	"os"
	"os/exec"

	"github.com/cloudfoundry/libbuildpack/cutlass"
	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("When composer.json is invalid JSON", func() {
	var app *cutlass.App
	AfterEach(func() { app = DestroyApp(app) })

	It("fails to stage", func() {
		app = cutlass.New(Fixtures("composer_invalid_json"))
		app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))
		Expect(app.Push()).ToNot(Succeed())

		logs := exec.Command("cf", "logs", "--recent", app.Name)
		out, err := logs.CombinedOutput()
		Expect(err).ToNot(HaveOccurred())

		Expect(out).To(ContainSubstring("-------> Buildpack version " + buildpackVersion))

		Expect(out).To(ContainSubstring("Invalid JSON present in composer.json. Parser said"))
	})
})
