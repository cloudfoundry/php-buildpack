package integration_test

import (
	"os"
	"path/filepath"
	"strings"

	"github.com/cloudfoundry/libbuildpack"
	"github.com/cloudfoundry/libbuildpack/cutlass"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

func ItLoadsAllTheModules(app *cutlass.App, phpVersion string) {
	var manifest struct {
		Dependencies []struct {
			Name    string   `json:"name"`
			Version string   `json:"version"`
			Modules []string `json:"modules"`
		} `json:"dependencies"`
	}
	Expect((&libbuildpack.YAML{}).Load(filepath.Join(bpDir, "manifest.yml"), &manifest)).To(Succeed())
	var modules []string
	for _, d := range manifest.Dependencies {
		if d.Name == "php" && strings.HasPrefix(d.Version, phpVersion) {
			modules = d.Modules
			break
		}
	}

	By("logs each module on the info page", func() {
		Expect(app.Stdout.String()).To(ContainSubstring("PHP " + phpVersion))
		body, err := app.GetBody("/")
		Expect(err).ToNot(HaveOccurred())

		for _, moduleName := range modules {
			if moduleName == "ioncube" {
				Expect(body).To(ContainSubstring("ionCube&nbsp;PHP&nbsp;Loader&nbsp;(enabled)"))
			} else {
				Expect(body).To(MatchRegexp("(?i)module_(Zend[+ ])?%s", moduleName))
			}
		}
	})
}

var _ = Describe("CF PHP Buildpack", func() {
	var app *cutlass.App
	AfterEach(func() { app = DestroyApp(app) })

	Context("extensions are specified in .bp-config", func() {
		It("deploying a basic PHP5 app that loads all prepackaged extensions", func() {
			app = cutlass.New(filepath.Join(bpDir, "fixtures", "php_5_all_modules"))
			app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))

			By("warns about deprecated PHP_EXTENSIONS", func() {
				PushAppAndConfirm(app)
				Expect(app.Stdout.String()).To(ContainSubstring("Warning: PHP_EXTENSIONS in options.json is deprecated."))
			})

			ItLoadsAllTheModules(app, "5")
		})

		It("deploying a basic PHP7.0 app that loads all prepackaged extensions", func() {
			app = cutlass.New(filepath.Join(bpDir, "fixtures", "php_7_all_modules"))
			app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))

			By("warns about deprecated PHP_EXTENSIONS", func() {
				PushAppAndConfirm(app)
				Expect(app.Stdout.String()).To(ContainSubstring("Warning: PHP_EXTENSIONS in options.json is deprecated."))
			})

			ItLoadsAllTheModules(app, "7.0")
		})

		It("deploying a basic PHP7.1 app that loads all prepackaged extensions", func() {
			app = cutlass.New(filepath.Join(bpDir, "fixtures", "php_71_all_modules"))
			app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))

			By("warns about deprecated PHP_EXTENSIONS", func() {
				PushAppAndConfirm(app)
				Expect(app.Stdout.String()).To(ContainSubstring("Warning: PHP_EXTENSIONS in options.json is deprecated."))
			})

			ItLoadsAllTheModules(app, "7.1")
		})
	})

	Context("extensions are specified in composer.json", func() {
		It("deploying a basic PHP5 app that loads all prepackaged extensions", func() {
			app = cutlass.New(filepath.Join(bpDir, "fixtures", "php_5_all_modules_composer"))
			PushAppAndConfirm(app)

			ItLoadsAllTheModules(app, "5")

			By("does not warn about deprecated PHP_EXTENSIONS", func() {
				Expect(app.Stdout.String()).ToNot(ContainSubstring("Warning: PHP_EXTENSIONS in options.json is deprecated."))
			})
		})

		It("deploying a basic PHP7.0 app that loads all prepackaged extensions", func() {
			app = cutlass.New(filepath.Join(bpDir, "fixtures", "php_7_all_modules_composer"))
			PushAppAndConfirm(app)

			ItLoadsAllTheModules(app, "7.0")

			By("does not warn about deprecated PHP_EXTENSIONS", func() {
				Expect(app.Stdout.String()).ToNot(ContainSubstring("Warning: PHP_EXTENSIONS in options.json is deprecated."))
			})
		})

		It("deploying a basic PHP7.1 app that loads all prepackaged extensions", func() {
			app = cutlass.New(filepath.Join(bpDir, "fixtures", "php_71_all_modules_composer"))
			PushAppAndConfirm(app)

			ItLoadsAllTheModules(app, "7.1")

			By("does not warn about deprecated PHP_EXTENSIONS", func() {
				Expect(app.Stdout.String()).ToNot(ContainSubstring("Warning: PHP_EXTENSIONS in options.json is deprecated."))
			})
		})
	})
})
