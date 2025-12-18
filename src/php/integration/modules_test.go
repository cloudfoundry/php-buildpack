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
			if t.Failed() && name != "" {
				t.Logf("❌ FAILED TEST - App/Container: %s", name)
				t.Logf("   Platform: %s", settings.Platform)
			}
			if name != "" && (!settings.KeepFailedContainers || !t.Failed()) {
				Expect(platform.Delete.Execute(name)).To(Succeed())
			}
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

		context("app with amqp module", func() {
			it("amqp module is loaded", func() {
				deployment, _, err := platform.Deploy.
					WithEnv(map[string]string{
						"COMPOSER_GITHUB_OAUTH_TOKEN": os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"),
					}).
					Execute(name, filepath.Join(fixtures, "with_amqp"))
				Expect(err).NotTo(HaveOccurred())

				Eventually(deployment).Should(Serve("").WithExpectedStatusCode(500))

				Eventually(func() string {
					logs, err := deployment.RuntimeLogs()
					Expect(err).NotTo(HaveOccurred())
					return logs
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

		context("app with phpredis module", func() {
			it("logs that phpredis could not connect to server", func() {
				deployment, _, err := platform.Deploy.
					WithEnv(map[string]string{
						"COMPOSER_GITHUB_OAUTH_TOKEN": os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"),
					}).
					Execute(name, filepath.Join(fixtures, "with_phpredis"))
				Expect(err).NotTo(HaveOccurred())

				Eventually(deployment).Should(Serve(
					ContainSubstring("<title>Redis Connection with phpredis</title>"),
				).WithExpectedStatusCode(500))

				Eventually(func() string {
					logs, err := deployment.RuntimeLogs()
					Expect(err).NotTo(HaveOccurred())
					return logs
				}).Should(Or(
					ContainSubstring("PHP message: PHP Fatal error:  Uncaught RedisException: Connection refused"),
					ContainSubstring("PHP message: PHP Fatal error:  Uncaught RedisException: Cannot assign requested address"),
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

		context("app with unsupported extensions", func() {
			it("logs the unsupported exts and loads the supported ones", func() {
				deployment, logs, err := platform.Deploy.
					Execute(name, filepath.Join(fixtures, "unsupported_extensions"))
				Expect(err).NotTo(HaveOccurred())

				Eventually(logs).Should(SatisfyAll(
					ContainSubstring("The extension 'meatball' is not provided by this buildpack"),
					ContainSubstring("The extension 'hotdog' is not provided by this buildpack"),
					Not(ContainSubstring("The extension 'curl' is not provided by this buildpack")),
				))

				Eventually(deployment).Should(Serve(SatisfyAll(
					ContainSubstring("curl module has been loaded successfully"),
				)))
			})
		})
	}
}
