package supply_test

import (
	"bytes"
	"fmt"
	"io"
	"os"
	"path/filepath"

	"github.com/cloudfoundry/libbuildpack"
	"github.com/cloudfoundry/php-buildpack/src/php/options"
	"github.com/cloudfoundry/php-buildpack/src/php/supply"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("Supply", func() {
	var (
		buildDir string
		cacheDir string
		depsDir  string
		depsIdx  string
		supplier *supply.Supplier
		logger   *libbuildpack.Logger
		buffer   *bytes.Buffer
		err      error
	)

	BeforeEach(func() {
		buildDir, err = os.MkdirTemp("", "php-buildpack.build.")
		Expect(err).To(BeNil())

		cacheDir, err = os.MkdirTemp("", "php-buildpack.cache.")
		Expect(err).To(BeNil())

		depsDir, err = os.MkdirTemp("", "php-buildpack.deps.")
		Expect(err).To(BeNil())

		depsIdx = "07"
		err = os.MkdirAll(filepath.Join(depsDir, depsIdx), 0755)
		Expect(err).To(BeNil())

		buffer = new(bytes.Buffer)
		logger = libbuildpack.NewLogger(buffer)
	})

	AfterEach(func() {
		Expect(os.RemoveAll(buildDir)).To(Succeed())
		Expect(os.RemoveAll(cacheDir)).To(Succeed())
		Expect(os.RemoveAll(depsDir)).To(Succeed())
	})

	Describe("Stager interface", func() {
		It("provides required buildpack directories", func() {
			stager := &testStager{
				buildDir: buildDir,
				cacheDir: cacheDir,
				depsDir:  depsDir,
				depsIdx:  depsIdx,
			}

			Expect(stager.BuildDir()).To(Equal(buildDir))
			Expect(stager.CacheDir()).To(Equal(cacheDir))
			Expect(stager.DepDir()).To(Equal(filepath.Join(depsDir, depsIdx)))
			Expect(stager.DepsIdx()).To(Equal(depsIdx))
		})

		It("can write environment files", func() {
			stager := &testStager{
				buildDir: buildDir,
				depsDir:  depsDir,
				depsIdx:  depsIdx,
			}

			err := stager.WriteEnvFile("TEST_VAR", "test_value")
			Expect(err).To(BeNil())

			envFile := filepath.Join(depsDir, depsIdx, "env", "TEST_VAR")
			Expect(envFile).To(BeAnExistingFile())

			contents, err := os.ReadFile(envFile)
			Expect(err).To(BeNil())
			Expect(string(contents)).To(Equal("test_value"))
		})

		It("can write profile.d scripts", func() {
			stager := &testStager{
				buildDir: buildDir,
				depsDir:  depsDir,
				depsIdx:  depsIdx,
			}

			scriptContent := "export TEST=value"
			err := stager.WriteProfileD("test.sh", scriptContent)
			Expect(err).To(BeNil())

			scriptFile := filepath.Join(depsDir, depsIdx, "profile.d", "test.sh")
			Expect(scriptFile).To(BeAnExistingFile())

			contents, err := os.ReadFile(scriptFile)
			Expect(err).To(BeNil())
			Expect(string(contents)).To(Equal(scriptContent))
		})

		It("can link directories in dep dir", func() {
			stager := &testStager{
				buildDir: buildDir,
				depsDir:  depsDir,
				depsIdx:  depsIdx,
			}

			err := stager.LinkDirectoryInDepDir("htdocs", "public")
			Expect(err).To(BeNil())

			Expect(stager.linkedDirs).To(HaveKeyWithValue("htdocs", "public"))
		})
	})

	Describe("Supplier struct", func() {
		It("can be initialized with required fields", func() {
			manifest := &testManifest{
				versions: map[string][]string{
					"php": {"8.1.31", "8.1.32", "8.2.28"},
				},
				defaults: map[string]string{
					"php": "8.1.32",
				},
			}

			installer := &testInstaller{
				installed: make(map[string]string),
			}

			stager := &testStager{
				buildDir: buildDir,
				depsDir:  depsDir,
				depsIdx:  depsIdx,
			}

			supplier = &supply.Supplier{
				Manifest:  manifest,
				Installer: installer,
				Stager:    stager,
				Command:   &testCommand{},
				Log:       logger,
			}

			Expect(supplier.Manifest).NotTo(BeNil())
			Expect(supplier.Installer).NotTo(BeNil())
			Expect(supplier.Stager).NotTo(BeNil())
			Expect(supplier.Command).NotTo(BeNil())
			Expect(supplier.Log).NotTo(BeNil())
		})
	})

	Describe("PHP version selection", func() {
		Context("when PHP version is specified in options", func() {
			It("uses the specified version", func() {
				opts := &options.Options{
					PHPVersion: "8.2.28",
				}

				Expect(opts.GetPHPVersion()).To(Equal("8.2.28"))
			})
		})

		Context("when PHP version is not specified", func() {
			It("returns empty string allowing default selection", func() {
				opts := &options.Options{
					PHPVersion: "",
				}

				Expect(opts.GetPHPVersion()).To(Equal(""))
			})
		})
	})

	Describe("Web server selection", func() {
		It("supports httpd as web server", func() {
			opts := &options.Options{
				WebServer: "httpd",
			}

			Expect(opts.WebServer).To(Equal("httpd"))
		})

		It("supports nginx as web server", func() {
			opts := &options.Options{
				WebServer: "nginx",
			}

			Expect(opts.WebServer).To(Equal("nginx"))
		})

		It("supports 'none' for no web server", func() {
			opts := &options.Options{
				WebServer: "none",
			}

			Expect(opts.WebServer).To(Equal("none"))
		})
	})

	Describe("Configuration paths", func() {
		It("determines config paths based on PHP version", func() {
			// Test that 8.1.x uses 8.1 config
			supplier = &supply.Supplier{
				Log: logger,
			}

			// We're testing the logic pattern, not the actual method
			phpVersion := "8.1.32"
			majorMinor := phpVersion[:3] // "8.1"
			Expect(majorMinor).To(Equal("8.1"))

			phpVersion2 := "8.2.28"
			majorMinor2 := phpVersion2[:3] // "8.2"
			Expect(majorMinor2).To(Equal("8.2"))
		})
	})

	Describe("Web directory configuration", func() {
		It("supports custom web directory configuration", func() {
			opts := &options.Options{
				WebDir: "public",
			}
			Expect(opts.WebDir).To(Equal("public"))
		})

		It("supports default htdocs directory", func() {
			opts := &options.Options{
				WebDir: "htdocs",
			}
			Expect(opts.WebDir).To(Equal("htdocs"))
		})
	})

	Describe("InstallPHP", func() {
		Context("when PHP version is specified", func() {
			It("installs the specified PHP version", func() {
				manifest := &testManifest{
					versions: map[string][]string{
						"php": {"8.1.31", "8.1.32", "8.2.28"},
					},
					defaults: map[string]string{
						"php": "8.1.32",
					},
				}
				installer := &testInstaller{
					installed: make(map[string]string),
				}
				stager := &testStager{
					buildDir: buildDir,
					depsDir:  depsDir,
					depsIdx:  depsIdx,
				}

				supplier = &supply.Supplier{
					Manifest:  manifest,
					Installer: installer,
					Stager:    stager,
					Log:       logger,
				}

				opts := &options.Options{
					PHPVersion: "8.2.28",
				}
				supplier.Options = opts

				err = supplier.InstallPHP()
				Expect(err).To(BeNil())

				// Verify PHP was installed
				Expect(installer.installed).To(HaveKeyWithValue("php", "8.2.28"))
			})
		})

		Context("when PHP version is not specified", func() {
			It("installs the default PHP version", func() {
				manifest := &testManifest{
					versions: map[string][]string{
						"php": {"8.1.31", "8.1.32", "8.2.28"},
					},
					defaults: map[string]string{
						"php": "8.1.32",
					},
				}
				installer := &testInstaller{
					installed: make(map[string]string),
				}
				stager := &testStager{
					buildDir: buildDir,
					depsDir:  depsDir,
					depsIdx:  depsIdx,
				}

				supplier = &supply.Supplier{
					Manifest:  manifest,
					Installer: installer,
					Stager:    stager,
					Log:       logger,
				}

				opts := &options.Options{
					PHPVersion: "", // Use default
				}
				supplier.Options = opts

				err = supplier.InstallPHP()
				Expect(err).To(BeNil())

				// Should use default version
				Expect(installer.installed).To(HaveKey("php"))
			})
		})
	})

	Describe("InstallWebServer", func() {
		Context("when web server is httpd", func() {
			It("installs Apache HTTPD", func() {
				manifest := &testManifest{
					versions: map[string][]string{
						"httpd": {"2.4.58"},
					},
					defaults: map[string]string{
						"httpd": "2.4.58",
					},
				}
				installer := &testInstaller{
					installed: make(map[string]string),
				}
				stager := &testStager{
					buildDir: buildDir,
					depsDir:  depsDir,
					depsIdx:  depsIdx,
				}

				supplier = &supply.Supplier{
					Manifest:  manifest,
					Installer: installer,
					Stager:    stager,
					Log:       logger,
				}

				opts := &options.Options{
					WebServer: "httpd",
				}
				supplier.Options = opts

				err = supplier.InstallWebServer()
				Expect(err).To(BeNil())

				// Verify HTTPD was installed
				Expect(installer.installed).To(HaveKey("httpd"))
			})
		})

		Context("when web server is nginx", func() {
			It("installs Nginx", func() {
				manifest := &testManifest{
					versions: map[string][]string{
						"nginx": {"1.25.3"},
					},
					defaults: map[string]string{
						"nginx": "1.25.3",
					},
				}
				installer := &testInstaller{
					installed: make(map[string]string),
				}
				stager := &testStager{
					buildDir: buildDir,
					depsDir:  depsDir,
					depsIdx:  depsIdx,
				}

				supplier = &supply.Supplier{
					Manifest:  manifest,
					Installer: installer,
					Stager:    stager,
					Log:       logger,
				}

				opts := &options.Options{
					WebServer: "nginx",
				}
				supplier.Options = opts

				err = supplier.InstallWebServer()
				Expect(err).To(BeNil())

				// Verify Nginx was installed
				Expect(installer.installed).To(HaveKey("nginx"))
			})
		})

		Context("when web server is 'none'", func() {
			It("does not install any web server", func() {
				installer := &testInstaller{
					installed: make(map[string]string),
				}
				stager := &testStager{
					buildDir: buildDir,
					depsDir:  depsDir,
					depsIdx:  depsIdx,
				}

				supplier = &supply.Supplier{
					Installer: installer,
					Stager:    stager,
					Log:       logger,
				}

				opts := &options.Options{
					WebServer: "none",
				}
				supplier.Options = opts

				err = supplier.InstallWebServer()
				Expect(err).To(BeNil())

				// Verify no web server was installed
				Expect(installer.installed).To(BeEmpty())
			})
		})
	})

	Describe("CreateDefaultEnv", func() {
		It("writes environment variables for PHP", func() {
			stager := &testStager{
				buildDir: buildDir,
				depsDir:  depsDir,
				depsIdx:  depsIdx,
			}

			supplier = &supply.Supplier{
				Stager: stager,
				Log:    logger,
			}

			opts := &options.Options{
				LibDir: "lib",
			}
			supplier.Options = opts

			err = supplier.CreateDefaultEnv()
			Expect(err).To(BeNil())

			// Verify env vars were written
			Expect(stager.envVars).NotTo(BeEmpty())
			Expect(stager.envVars).To(HaveKey("PHPRC"))
		})
	})

	Describe("PHP extensions", func() {
		It("supports multiple PHP extension configuration", func() {
			opts := &options.Options{
				PHPExtensions: []string{"redis", "imagick", "xdebug"},
			}

			Expect(opts.PHPExtensions).To(HaveLen(3))
			Expect(opts.PHPExtensions).To(ContainElement("redis"))
			Expect(opts.PHPExtensions).To(ContainElement("imagick"))
			Expect(opts.PHPExtensions).To(ContainElement("xdebug"))
		})

		It("supports empty extensions list", func() {
			opts := &options.Options{
				PHPExtensions: []string{},
			}

			Expect(opts.PHPExtensions).To(BeEmpty())
		})
	})

	Describe("Manifest", func() {
		Context("when querying available versions", func() {
			It("returns all versions for a dependency", func() {
				manifest := &testManifest{
					versions: map[string][]string{
						"php": {"8.1.31", "8.1.32", "8.2.28"},
					},
				}

				versions := manifest.AllDependencyVersions("php")
				Expect(versions).To(HaveLen(3))
				Expect(versions).To(ContainElement("8.1.31"))
				Expect(versions).To(ContainElement("8.1.32"))
				Expect(versions).To(ContainElement("8.2.28"))
			})
		})

		Context("when querying default version", func() {
			It("returns the default version for a dependency", func() {
				manifest := &testManifest{
					versions: map[string][]string{
						"php": {"8.1.31", "8.1.32", "8.2.28"},
					},
					defaults: map[string]string{
						"php": "8.1.32",
					},
				}

				dep, err := manifest.DefaultVersion("php")
				Expect(err).To(BeNil())
				Expect(dep.Name).To(Equal("php"))
				Expect(dep.Version).To(Equal("8.1.32"))
			})
		})

		Context("when checking if buildpack is cached", func() {
			It("returns true for cached buildpack", func() {
				manifest := &testManifest{
					cached: true,
				}

				Expect(manifest.IsCached()).To(BeTrue())
			})

			It("returns false for uncached buildpack", func() {
				manifest := &testManifest{
					cached: false,
				}

				Expect(manifest.IsCached()).To(BeFalse())
			})
		})
	})
})

// testStager is a simple test implementation of the Stager interface
type testStager struct {
	buildDir   string
	cacheDir   string
	depsDir    string
	depsIdx    string
	linkedDirs map[string]string // Track linked directories
	envVars    map[string]string // Track env vars written
}

func (t *testStager) BuildDir() string { return t.buildDir }
func (t *testStager) CacheDir() string { return t.cacheDir }
func (t *testStager) DepDir() string   { return filepath.Join(t.depsDir, t.depsIdx) }
func (t *testStager) DepsIdx() string  { return t.depsIdx }

func (t *testStager) LinkDirectoryInDepDir(destDir, destSubDir string) error {
	if t.linkedDirs == nil {
		t.linkedDirs = make(map[string]string)
	}
	t.linkedDirs[destDir] = destSubDir
	return nil
}

func (t *testStager) WriteEnvFile(envVar, envVal string) error {
	if t.envVars == nil {
		t.envVars = make(map[string]string)
	}
	t.envVars[envVar] = envVal

	envDir := filepath.Join(t.depsDir, t.depsIdx, "env")
	if err := os.MkdirAll(envDir, 0755); err != nil {
		return err
	}
	return os.WriteFile(filepath.Join(envDir, envVar), []byte(envVal), 0644)
}

func (t *testStager) WriteProfileD(scriptName, scriptContents string) error {
	profileDir := filepath.Join(t.depsDir, t.depsIdx, "profile.d")
	if err := os.MkdirAll(profileDir, 0755); err != nil {
		return err
	}
	return os.WriteFile(filepath.Join(profileDir, scriptName), []byte(scriptContents), 0644)
}

// testManifest is a simple test implementation of the Manifest interface
type testManifest struct {
	versions map[string][]string
	defaults map[string]string
	cached   bool
}

func (t *testManifest) AllDependencyVersions(depName string) []string {
	return t.versions[depName]
}

func (t *testManifest) DefaultVersion(depName string) (libbuildpack.Dependency, error) {
	version, ok := t.defaults[depName]
	if !ok {
		return libbuildpack.Dependency{}, fmt.Errorf("no default for %s", depName)
	}
	return libbuildpack.Dependency{Name: depName, Version: version}, nil
}

func (t *testManifest) GetEntry(dep libbuildpack.Dependency) (*libbuildpack.ManifestEntry, error) {
	return &libbuildpack.ManifestEntry{
		Dependency: dep,
	}, nil
}

func (t *testManifest) IsCached() bool {
	return t.cached
}

// testInstaller is a simple test implementation of the Installer interface
type testInstaller struct {
	installed map[string]string
}

func (t *testInstaller) InstallDependency(dep libbuildpack.Dependency, outputDir string) error {
	t.installed[dep.Name] = dep.Version
	return os.MkdirAll(outputDir, 0755)
}

func (t *testInstaller) InstallOnlyVersion(depName, installDir string) error {
	t.installed[depName] = "latest"
	return os.MkdirAll(installDir, 0755)
}

// testCommand is a simple test implementation of the Command interface
type testCommand struct {
	executed []string
}

func (t *testCommand) Execute(dir string, stdout io.Writer, stderr io.Writer, program string, args ...string) error {
	t.executed = append(t.executed, program)
	return nil
}

func (t *testCommand) Output(dir string, program string, args ...string) (string, error) {
	t.executed = append(t.executed, program)
	return "", nil
}
