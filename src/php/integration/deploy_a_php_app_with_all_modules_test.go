package integration_test

import (
	"os"
	"path/filepath"

	"github.com/cloudfoundry/libbuildpack"
	"github.com/cloudfoundry/libbuildpack/cutlass"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

type SubDependency struct {
	Name    string
	Version string
}

func ItLoadsAllTheModules(app *cutlass.App) {
	var manifest struct {
		Dependencies []struct {
			Name    string          `yaml:"name"`
			Version string          `yaml:"version"`
			Modules []SubDependency `yaml:"dependencies"`
		} `yaml:"dependencies"`
		DefaultVersions []struct {
			Name    string `yaml:"name"`
			Version string `yaml:"version"`
		} `yaml:"default_versions"`
	}
	Expect((&libbuildpack.YAML{}).Load(filepath.Join(bpDir, "manifest.yml"), &manifest)).To(Succeed())
	var phpVersion string
	for _, v := range manifest.DefaultVersions {
		if v.Name == "php" {
			phpVersion = v.Version
		}
	}

	var subDependencies []SubDependency
	for _, d := range manifest.Dependencies {
		if d.Name == "php" && d.Version == phpVersion {
			subDependencies = d.Modules
			break
		}
	}

	By("logs each module on the info page", func() {
		Expect(app.Stdout.String()).To(ContainSubstring("PHP " + phpVersion))
		body, err := app.GetBody("/")
		Expect(err).ToNot(HaveOccurred())

		for _, dependency := range subDependencies {
			Expect(body).To(MatchRegexp("(?i)module_(Zend[+ ])?%s", dependency.Name))
		}
	})
}

var _ = Describe("CF PHP Buildpack", func() {
	var app *cutlass.App
	AfterEach(func() {
		app = DestroyApp(app)
	})

	Context("extensions are specified in .bp-config", func() {
		It("deploying a basic PHP app that loads all prepackaged extensions", func() {
			app = cutlass.New(Fixtures("php_all_modules"))
			app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))

			By("warns about deprecated PHP_EXTENSIONS", func() {
				PushAppAndConfirm(app)
				Expect(app.Stdout.String()).To(ContainSubstring("Warning: PHP_EXTENSIONS in options.json is deprecated."))
			})

			ItLoadsAllTheModules(app)
			body, err := app.GetBody("/")
			Expect(err).ToNot(HaveOccurred())
			Expect(body).To(MatchRegexp("(?i)module_(Zend[+ ])?%s", "sqlsrv"))
			Expect(body).To(MatchRegexp("(?i)module_(Zend[+ ])?%s", "pdo_sqlsrv"))
			Expect(body).To(MatchRegexp("(?i)module_(Zend[+ ])?%s", "maxminddb"))
		})

		It("deploying a basic PHP app with cflinuxfs3 extensions", func() {
			SkipUnlessCflinuxfs3()

			app = cutlass.New(Fixtures("php_fs3_extensions"))
			app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))

			By("warns about deprecated PHP_EXTENSIONS", func() {
				PushAppAndConfirm(app)
				Expect(app.Stdout.String()).To(ContainSubstring("Warning: PHP_EXTENSIONS in options.json is deprecated."))
			})

			body, err := app.GetBody("/")
			Expect(err).ToNot(HaveOccurred())

			Expect(body).To(MatchRegexp("(?i)module_(Zend[+ ])?%s", "sqlsrv"))
			Expect(body).To(MatchRegexp("(?i)module_(Zend[+ ])?%s", "pdo_sqlsrv"))
			Expect(body).To(MatchRegexp("(?i)module_(Zend[+ ])?%s", "maxminddb"))
		})
	})

	Context("extensions are specified in composer.json", func() {
		It("deploying a basic PHP app that loads all prepackaged extensions", func() {
			app = cutlass.New(Fixtures("php_all_modules_composer"))
			PushAppAndConfirm(app)

			ItLoadsAllTheModules(app)

			By("does not warn about deprecated PHP_EXTENSIONS", func() {
				Expect(app.Stdout.String()).ToNot(ContainSubstring("Warning: PHP_EXTENSIONS in options.json is deprecated."))
			})
		})
	})
})
