package integration_test

import (
	"path/filepath"

	"github.com/cloudfoundry/libbuildpack/cutlass"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("Composer with unicode env variables", func() {
	var app *cutlass.App
	AfterEach(func() { app = DestroyApp(app) })

	It("", func() {
		app = cutlass.New(filepath.Join(bpDir, "fixtures", "strangechars"))
		app.SetEnv("BP_DEBUG", "1")

		PushAppAndConfirm(app)
		Eventually(app.Stdout.String).Should(ContainSubstring(`[DEBUG] composer - ENV IS: CLUSTERS_INFO={"dev01":{"env":"開発環境"`))
	})
})
