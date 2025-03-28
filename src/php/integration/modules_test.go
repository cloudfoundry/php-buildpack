package integration_test

import (
	"fmt"
	"os"
	"path/filepath"
	"testing"

	"github.com/cloudfoundry/switchblade"
	"github.com/sclevine/spec"

	. "github.com/cloudfoundry/switchblade/matchers"
	. "github.com/onsi/gomega"
	"gopkg.in/yaml.v2"
)

func testModules(platform switchblade.Platform, fixtures string) func(*testing.T, spec.G, spec.S) {
	return func(t *testing.T, context spec.G, it spec.S) {
		var (
			Expect     = NewWithT(t).Expect
			Eventually = NewWithT(t).Eventually

			name string
		)

		it.Before(func() {
			var err error
			name, err = switchblade.RandomName()
			Expect(err).NotTo(HaveOccurred())
		})

		it.After(func() {
			Expect(platform.Delete.Execute(name)).To(Succeed())
		})

		ItLoadsAllTheModules := func(deployment switchblade.Deployment) {
			type SubDependency struct {
				Name    string
				Version string
			}
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

			manifestData, err := os.ReadFile(filepath.Join(fixtures, "..", "manifest.yml"))
			Expect(err).NotTo(HaveOccurred())

			err = yaml.Unmarshal(manifestData, &manifest)
			Expect(err).NotTo(HaveOccurred())

			var phpVersion string
			for _, v := range manifest.DefaultVersions {
				if v.Name == "php" {
					phpVersion = v.Version
				}
			}

			var modules []SubDependency
			for _, d := range manifest.Dependencies {
				if d.Name == "php" && d.Version == phpVersion {
					modules = d.Modules
					break
				}
			}

			Eventually(deployment).Should(Serve(
				ContainSubstring(fmt.Sprintf("PHP %s", phpVersion)),
			))

			for _, module := range modules {
				Eventually(deployment).Should(Serve(
					ContainLines(MatchRegexp("(?i)module_(Zend[+ ])?%s", module.Name)),
				))
			}
		}

		context("app with extensions listed in .bp-config", func() {
			it("app loads all listed extensions", func() {
				deployment, logs, err := platform.Deploy.
					Execute(name, filepath.Join(fixtures, "php_all_modules"))
				Expect(err).NotTo(HaveOccurred())

				Eventually(logs).Should(
					ContainSubstring("Warning: PHP_EXTENSIONS in options.json is deprecated."),
				)

				ItLoadsAllTheModules(deployment)
			})
		})

		context("app with extensions listed composer.json", func() {
			it("app loads all listed extensions", func() {
				deployment, _, err := platform.Deploy.
					Execute(name, filepath.Join(fixtures, "php_all_modules_composer"))
				Expect(err).NotTo(HaveOccurred())

				ItLoadsAllTheModules(deployment)
			})
		})

	}
}
