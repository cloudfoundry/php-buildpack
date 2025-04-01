package integration_test

import (
	"fmt"
	"net/http"
	"os"
	"os/exec"
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
					WithEnv(map[string]string{
						"COMPOSER_GITHUB_OAUTH_TOKEN": os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"),
					}).
					Execute(name, filepath.Join(fixtures, "php_all_modules_composer"))
				Expect(err).NotTo(HaveOccurred())

				ItLoadsAllTheModules(deployment)
			})
		})

		context("app with custom conf files in php.ini.d dir in app root", func() {
			it("app sets custom conf", func() {
				deployment, _, err := platform.Deploy.
					Execute(name, filepath.Join(fixtures, "php_with_php_ini_d"))
				Expect(err).NotTo(HaveOccurred())

				Eventually(deployment).Should(Serve(
					ContainSubstring("teststring"),
				))
			})
		})

		// TODO
		context.Pend("app with amqp module", func() {
			it("amqp module is loaded", func() {
				deployment, _, err := platform.Deploy.
					WithEnv(map[string]string{
						"COMPOSER_GITHUB_OAUTH_TOKEN": os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"),
					}).
					Execute(name, filepath.Join(fixtures, "with_amqp"))
				Expect(err).NotTo(HaveOccurred())

				response, _ := http.Get(deployment.ExternalURL)
				// _ = err
				// Expect(err).NotTo(HaveOccurred())
				defer response.Body.Close()
				// Expect(response.StatusCode).To(Equal(501))

				Eventually(func() string {
					cmd := exec.Command("docker", "container", "logs", deployment.Name)
					output, err := cmd.CombinedOutput()
					Expect(err).NotTo(HaveOccurred())
					return string(output)
				}).Should(
					ContainSubstring("PHP message: PHP Fatal error:  Uncaught AMQPConnectionException"),
				)
			})
		})

		context("app with APCu module", func() {
			it("apcu module is loaded", func() {
				deployment, _, err := platform.Deploy.
					WithEnv(map[string]string{
						"COMPOSER_GITHUB_OAUTH_TOKEN": os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"),
					}).
					Execute(name, filepath.Join(fixtures, "with_apcu"))
				Expect(err).NotTo(HaveOccurred())

				Eventually(deployment).Should(Serve(
					ContainSubstring("I'm an apcu cached variable"),
				))
			})
		})

		context("app with argon2 module", func() {
			it("argon2 module is loaded", func() {
				deployment, _, err := platform.Deploy.
					WithEnv(map[string]string{
						"COMPOSER_GITHUB_OAUTH_TOKEN": os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"),
					}).
					Execute(name, filepath.Join(fixtures, "with_argon2"))
				Expect(err).NotTo(HaveOccurred())

				Eventually(deployment).Should(Serve(
					ContainSubstring(`password hash of "hello-world": $argon2i$v=19$m=1024,t=2`),
				))
			})
		})

		context("app with compiled modules in PHP_EXTENSIONS", func() {
			it("loads the modules", func() {
				deployment, logs, err := platform.Deploy.
					Execute(name, filepath.Join(fixtures, "with_compiled_modules"))
				Expect(err).NotTo(HaveOccurred())

				Eventually(logs).Should(SatisfyAll(
					Not(ContainSubstring("The extension 'libxml' is not provided by this buildpack")),
					Not(ContainSubstring("The extension 'SimpleXML' is not provided by this buildpack")),
					Not(ContainSubstring("The extension 'sqlite3' is not provided by this buildpack")),
					Not(ContainSubstring("The extension 'SPL' is not provided by this buildpack")),
				))

				Eventually(deployment).Should(Serve(SatisfyAll(
					ContainSubstring("module_libxml"),
					ContainSubstring("module_simplexml"),
					ContainSubstring("module_sqlite3"),
					ContainSubstring("module_spl"),
				)))
			})
		})
	}
}
