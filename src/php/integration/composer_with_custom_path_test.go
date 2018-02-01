package integration_test

import (
	"path/filepath"
	"time"

	"github.com/cloudfoundry/libbuildpack/cutlass"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("Composer with custom path", func() {
	var app *cutlass.App
	AfterEach(func() { app = DestroyApp(app) })

	It("succeeds", func() {
		app = cutlass.New(filepath.Join(bpDir, "fixtures", "composer_custom_path"))
		app.SetEnv("COMPOSER_PATH", "meatball/sub")
		PushAppAndConfirm(app)

		Eventually(app.Stdout.String, 10*time.Second).Should(ContainSubstring("Loading composer repositories with package information"))
	})
})
