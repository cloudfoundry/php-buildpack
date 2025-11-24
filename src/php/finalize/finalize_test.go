package finalize_test

import (
	"bytes"
	"fmt"
	"io"
	"os"
	"path/filepath"

	"github.com/cloudfoundry/libbuildpack"
	"github.com/cloudfoundry/php-buildpack/src/php/finalize"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("Finalize", func() {
	var (
		buildDir  string
		depsDir   string
		depsIdx   string
		finalizer *finalize.Finalizer
		logger    *libbuildpack.Logger
		buffer    *bytes.Buffer
		err       error
	)

	BeforeEach(func() {
		buildDir, err = os.MkdirTemp("", "php-buildpack.build.")
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
		Expect(os.RemoveAll(depsDir)).To(Succeed())
	})

	Describe("Stager interface", func() {
		It("provides required buildpack directories", func() {
			stager := &testStager{
				buildDir: buildDir,
				depsDir:  depsDir,
				depsIdx:  depsIdx,
			}

			Expect(stager.BuildDir()).To(Equal(buildDir))
			Expect(stager.DepDir()).To(Equal(filepath.Join(depsDir, depsIdx)))
			Expect(stager.DepsIdx()).To(Equal(depsIdx))
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

		It("can set launch environment", func() {
			stager := &testStager{
				buildDir: buildDir,
				depsDir:  depsDir,
				depsIdx:  depsIdx,
			}

			// Create a test profile.d script
			err := stager.WriteProfileD("test.sh", "export TEST=value")
			Expect(err).To(BeNil())

			// SetLaunchEnvironment should copy profile.d scripts
			err = stager.SetLaunchEnvironment()
			Expect(err).To(BeNil())

			// Verify copy was made
			copiedScript := filepath.Join(buildDir, ".profile.d", "test.sh")
			Expect(copiedScript).To(BeAnExistingFile())
		})
	})

	Describe("Finalizer struct", func() {
		It("can be initialized with required fields", func() {
			manifest := &testManifest{
				versions: map[string][]string{
					"php": {"8.1.31", "8.1.32", "8.2.28"},
				},
				defaults: map[string]string{
					"php": "8.1.32",
				},
			}

			stager := &testStager{
				buildDir: buildDir,
				depsDir:  depsDir,
				depsIdx:  depsIdx,
			}

			finalizer = &finalize.Finalizer{
				Manifest: manifest,
				Stager:   stager,
				Command:  &testCommand{},
				Log:      logger,
			}

			Expect(finalizer.Manifest).NotTo(BeNil())
			Expect(finalizer.Stager).NotTo(BeNil())
			Expect(finalizer.Command).NotTo(BeNil())
			Expect(finalizer.Log).NotTo(BeNil())
		})
	})

	Describe("CreatePHPEnvironmentScript", func() {
		It("creates a profile.d script with PHP PATH setup", func() {
			stager := &testStager{
				buildDir: buildDir,
				depsDir:  depsDir,
				depsIdx:  depsIdx,
			}

			finalizer = &finalize.Finalizer{
				Stager: stager,
				Log:    logger,
			}

			err := finalizer.CreatePHPEnvironmentScript()
			Expect(err).To(BeNil())

			scriptFile := filepath.Join(depsDir, depsIdx, "profile.d", "php-env.sh")
			Expect(scriptFile).To(BeAnExistingFile())

			contents, err := os.ReadFile(scriptFile)
			Expect(err).To(BeNil())
			Expect(string(contents)).To(ContainSubstring("export PATH"))
			Expect(string(contents)).To(ContainSubstring("php/bin"))
			Expect(string(contents)).To(ContainSubstring(depsIdx))
		})
	})

	Describe("CreatePHPRuntimeDirectories", func() {
		It("creates PHP-FPM var/run directory", func() {
			stager := &testStager{
				buildDir: buildDir,
				depsDir:  depsDir,
				depsIdx:  depsIdx,
			}

			finalizer = &finalize.Finalizer{
				Stager: stager,
				Log:    logger,
			}

			err := finalizer.CreatePHPRuntimeDirectories()
			Expect(err).To(BeNil())

			phpVarRunDir := filepath.Join(depsDir, depsIdx, "php", "var", "run")
			Expect(phpVarRunDir).To(BeADirectory())
		})
	})

	Describe("SetupProcessTypes", func() {
		Context("when Procfile exists", func() {
			It("uses existing Procfile", func() {
				stager := &testStager{
					buildDir: buildDir,
					depsDir:  depsDir,
					depsIdx:  depsIdx,
				}

				finalizer = &finalize.Finalizer{
					Stager: stager,
					Log:    logger,
				}

				// Create existing Procfile
				procfile := filepath.Join(buildDir, "Procfile")
				err := os.WriteFile(procfile, []byte("web: custom-start\n"), 0644)
				Expect(err).To(BeNil())

				err = finalizer.SetupProcessTypes()
				Expect(err).To(BeNil())

				// Verify it wasn't overwritten
				contents, err := os.ReadFile(procfile)
				Expect(err).To(BeNil())
				Expect(string(contents)).To(Equal("web: custom-start\n"))
			})
		})

		Context("when Procfile does not exist", func() {
			It("creates default Procfile", func() {
				stager := &testStager{
					buildDir: buildDir,
					depsDir:  depsDir,
					depsIdx:  depsIdx,
				}

				finalizer = &finalize.Finalizer{
					Stager: stager,
					Log:    logger,
				}

				err = finalizer.SetupProcessTypes()
				Expect(err).To(BeNil())

				procfile := filepath.Join(buildDir, "Procfile")
				Expect(procfile).To(BeAnExistingFile())

				contents, err := os.ReadFile(procfile)
				Expect(err).To(BeNil())
				Expect(string(contents)).To(ContainSubstring("web: .bp/bin/start"))
			})
		})
	})

	Describe("CreateStartScript", func() {
		var (
			manifest *testManifest
			stager   *testStager
			command  *testCommand
		)

		BeforeEach(func() {
			manifest = &testManifest{
				versions: map[string][]string{
					"php": {"8.1.31", "8.1.32", "8.2.28"},
				},
				defaults: map[string]string{
					"php": "8.1.32",
				},
			}

			stager = &testStager{
				buildDir: buildDir,
				depsDir:  depsDir,
				depsIdx:  depsIdx,
			}

			command = &testCommand{}

			// Set required environment variables
			os.Setenv("BP_DIR", buildDir)
		})

		Context("when web server is httpd", func() {
			It("creates HTTPD start script", func() {
				// Create options.json with httpd
				optionsFile := filepath.Join(buildDir, ".bp-config", "options.json")
				err := os.MkdirAll(filepath.Dir(optionsFile), 0755)
				Expect(err).To(BeNil())

				optionsJSON := `{"WEB_SERVER": "httpd", "WEBDIR": "htdocs"}`
				err = os.WriteFile(optionsFile, []byte(optionsJSON), 0644)
				Expect(err).To(BeNil())

				// Create rewrite binary source (empty file for test)
				rewriteSrc := filepath.Join(buildDir, "bin", "rewrite")
				err = os.MkdirAll(filepath.Dir(rewriteSrc), 0755)
				Expect(err).To(BeNil())
				err = os.WriteFile(rewriteSrc, []byte("#!/bin/bash\n"), 0755)
				Expect(err).To(BeNil())

				finalizer = &finalize.Finalizer{
					Manifest: manifest,
					Stager:   stager,
					Command:  command,
					Log:      logger,
				}

				err = finalizer.CreateStartScript()
				Expect(err).To(BeNil())

				// Verify start script was created
				startScript := filepath.Join(buildDir, ".bp", "bin", "start")
				Expect(startScript).To(BeAnExistingFile())

				// Verify script content
				contents, err := os.ReadFile(startScript)
				Expect(err).To(BeNil())
				scriptContent := string(contents)
				Expect(scriptContent).To(ContainSubstring("HTTPD"))
				Expect(scriptContent).To(ContainSubstring("php-fpm"))
				Expect(scriptContent).To(ContainSubstring("httpd/bin/httpd"))
			})
		})

		Context("when web server is nginx", func() {
			It("creates Nginx start script", func() {
				// Create options.json with nginx
				optionsFile := filepath.Join(buildDir, ".bp-config", "options.json")
				err := os.MkdirAll(filepath.Dir(optionsFile), 0755)
				Expect(err).To(BeNil())

				optionsJSON := `{"WEB_SERVER": "nginx", "WEBDIR": "htdocs"}`
				err = os.WriteFile(optionsFile, []byte(optionsJSON), 0644)
				Expect(err).To(BeNil())

				// Create rewrite binary source
				rewriteSrc := filepath.Join(buildDir, "bin", "rewrite")
				err = os.MkdirAll(filepath.Dir(rewriteSrc), 0755)
				Expect(err).To(BeNil())
				err = os.WriteFile(rewriteSrc, []byte("#!/bin/bash\n"), 0755)
				Expect(err).To(BeNil())

				finalizer = &finalize.Finalizer{
					Manifest: manifest,
					Stager:   stager,
					Command:  command,
					Log:      logger,
				}

				err = finalizer.CreateStartScript()
				Expect(err).To(BeNil())

				// Verify start script was created
				startScript := filepath.Join(buildDir, ".bp", "bin", "start")
				Expect(startScript).To(BeAnExistingFile())

				// Verify script content
				contents, err := os.ReadFile(startScript)
				Expect(err).To(BeNil())
				scriptContent := string(contents)
				Expect(scriptContent).To(ContainSubstring("Nginx"))
				Expect(scriptContent).To(ContainSubstring("php-fpm"))
				Expect(scriptContent).To(ContainSubstring("nginx/sbin/nginx"))
			})
		})

		Context("when web server is none", func() {
			It("creates PHP-FPM only start script", func() {
				// Create options.json with none (PHP-FPM only)
				optionsFile := filepath.Join(buildDir, ".bp-config", "options.json")
				err := os.MkdirAll(filepath.Dir(optionsFile), 0755)
				Expect(err).To(BeNil())

				optionsJSON := `{"WEB_SERVER": "none", "WEBDIR": "htdocs"}`
				err = os.WriteFile(optionsFile, []byte(optionsJSON), 0644)
				Expect(err).To(BeNil())

				// Create rewrite binary source
				rewriteSrc := filepath.Join(buildDir, "bin", "rewrite")
				err = os.MkdirAll(filepath.Dir(rewriteSrc), 0755)
				Expect(err).To(BeNil())
				err = os.WriteFile(rewriteSrc, []byte("#!/bin/bash\n"), 0755)
				Expect(err).To(BeNil())

				finalizer = &finalize.Finalizer{
					Manifest: manifest,
					Stager:   stager,
					Command:  command,
					Log:      logger,
				}

				err = finalizer.CreateStartScript()
				Expect(err).To(BeNil())

				// Verify start script was created
				startScript := filepath.Join(buildDir, ".bp", "bin", "start")
				Expect(startScript).To(BeAnExistingFile())

				// Verify script content
				contents, err := os.ReadFile(startScript)
				Expect(err).To(BeNil())
				scriptContent := string(contents)
				Expect(scriptContent).To(ContainSubstring("PHP-FPM only"))
				Expect(scriptContent).To(ContainSubstring("php-fpm"))
				Expect(scriptContent).NotTo(ContainSubstring("httpd"))
				Expect(scriptContent).NotTo(ContainSubstring("nginx"))
			})
		})

		Context("when BP_DIR is not set", func() {
			It("returns an error", func() {
				os.Unsetenv("BP_DIR")

				finalizer = &finalize.Finalizer{
					Manifest: manifest,
					Stager:   stager,
					Command:  command,
					Log:      logger,
				}

				err = finalizer.CreateStartScript()
				Expect(err).NotTo(BeNil())
				Expect(err.Error()).To(ContainSubstring("BP_DIR"))
			})
		})

		Context("when rewrite binary doesn't exist", func() {
			It("returns an error", func() {
				finalizer = &finalize.Finalizer{
					Manifest: manifest,
					Stager:   stager,
					Command:  command,
					Log:      logger,
				}

				err = finalizer.CreateStartScript()
				Expect(err).NotTo(BeNil())
				Expect(err.Error()).To(ContainSubstring("rewrite"))
			})
		})
	})

	Describe("Start script file creation", func() {
		It("creates .bp/bin directory for scripts", func() {
			stager := &testStager{
				buildDir: buildDir,
				depsDir:  depsDir,
				depsIdx:  depsIdx,
			}

			manifest := &testManifest{
				versions: map[string][]string{"php": {"8.1.32"}},
				defaults: map[string]string{"php": "8.1.32"},
			}

			finalizer = &finalize.Finalizer{
				Manifest: manifest,
				Stager:   stager,
				Command:  &testCommand{},
				Log:      logger,
			}

			// Set BP_DIR and create necessary files
			os.Setenv("BP_DIR", buildDir)
			rewriteSrc := filepath.Join(buildDir, "bin", "rewrite")
			err = os.MkdirAll(filepath.Dir(rewriteSrc), 0755)
			Expect(err).To(BeNil())
			err = os.WriteFile(rewriteSrc, []byte("#!/bin/bash\n"), 0755)
			Expect(err).To(BeNil())

			optionsFile := filepath.Join(buildDir, ".bp-config", "options.json")
			err = os.MkdirAll(filepath.Dir(optionsFile), 0755)
			Expect(err).To(BeNil())
			err = os.WriteFile(optionsFile, []byte(`{"WEB_SERVER": "httpd"}`), 0644)
			Expect(err).To(BeNil())

			err = finalizer.CreateStartScript()
			Expect(err).To(BeNil())

			// Verify directory structure
			bpBinDir := filepath.Join(buildDir, ".bp", "bin")
			Expect(bpBinDir).To(BeADirectory())
		})

		It("copies rewrite binary to .bp/bin", func() {
			stager := &testStager{
				buildDir: buildDir,
				depsDir:  depsDir,
				depsIdx:  depsIdx,
			}

			manifest := &testManifest{
				versions: map[string][]string{"php": {"8.1.32"}},
				defaults: map[string]string{"php": "8.1.32"},
			}

			finalizer = &finalize.Finalizer{
				Manifest: manifest,
				Stager:   stager,
				Command:  &testCommand{},
				Log:      logger,
			}

			os.Setenv("BP_DIR", buildDir)
			rewriteSrc := filepath.Join(buildDir, "bin", "rewrite")
			err = os.MkdirAll(filepath.Dir(rewriteSrc), 0755)
			Expect(err).To(BeNil())
			err = os.WriteFile(rewriteSrc, []byte("#!/bin/bash\necho test\n"), 0755)
			Expect(err).To(BeNil())

			optionsFile := filepath.Join(buildDir, ".bp-config", "options.json")
			err = os.MkdirAll(filepath.Dir(optionsFile), 0755)
			Expect(err).To(BeNil())
			err = os.WriteFile(optionsFile, []byte(`{"WEB_SERVER": "httpd"}`), 0644)
			Expect(err).To(BeNil())

			err = finalizer.CreateStartScript()
			Expect(err).To(BeNil())

			// Verify rewrite binary was copied
			rewriteDst := filepath.Join(buildDir, ".bp", "bin", "rewrite")
			Expect(rewriteDst).To(BeAnExistingFile())

			contents, err := os.ReadFile(rewriteDst)
			Expect(err).To(BeNil())
			Expect(string(contents)).To(ContainSubstring("echo test"))
		})
	})

	Describe("Service commands and environment", func() {
		It("can write service commands to profile.d", func() {
			stager := &testStager{
				buildDir: buildDir,
				depsDir:  depsDir,
				depsIdx:  depsIdx,
			}

			finalizer = &finalize.Finalizer{
				Stager: stager,
				Log:    logger,
			}

			// Simulate writing service commands
			err := stager.WriteProfileD("extension-services.sh", "# Test service\ntest-command &\n")
			Expect(err).To(BeNil())

			scriptFile := filepath.Join(depsDir, depsIdx, "profile.d", "extension-services.sh")
			Expect(scriptFile).To(BeAnExistingFile())

			contents, err := os.ReadFile(scriptFile)
			Expect(err).To(BeNil())
			Expect(string(contents)).To(ContainSubstring("test-command"))
		})

		It("can write service environment variables", func() {
			stager := &testStager{
				buildDir: buildDir,
				depsDir:  depsDir,
				depsIdx:  depsIdx,
			}

			finalizer = &finalize.Finalizer{
				Stager: stager,
				Log:    logger,
			}

			// Simulate writing environment variables
			err := stager.WriteProfileD("extension-env.sh", "export TEST_VAR='test_value'\n")
			Expect(err).To(BeNil())

			scriptFile := filepath.Join(depsDir, depsIdx, "profile.d", "extension-env.sh")
			Expect(scriptFile).To(BeAnExistingFile())

			contents, err := os.ReadFile(scriptFile)
			Expect(err).To(BeNil())
			Expect(string(contents)).To(ContainSubstring("export TEST_VAR"))
		})
	})

	Describe("Web server configuration handling", func() {
		Context("with custom WEBDIR", func() {
			It("uses specified WEBDIR in start script", func() {
				stager := &testStager{
					buildDir: buildDir,
					depsDir:  depsDir,
					depsIdx:  depsIdx,
				}

				manifest := &testManifest{
					versions: map[string][]string{"php": {"8.1.32"}},
					defaults: map[string]string{"php": "8.1.32"},
				}

				finalizer = &finalize.Finalizer{
					Manifest: manifest,
					Stager:   stager,
					Command:  &testCommand{},
					Log:      logger,
				}

				os.Setenv("BP_DIR", buildDir)
				rewriteSrc := filepath.Join(buildDir, "bin", "rewrite")
				err = os.MkdirAll(filepath.Dir(rewriteSrc), 0755)
				Expect(err).To(BeNil())
				err = os.WriteFile(rewriteSrc, []byte("#!/bin/bash\n"), 0755)
				Expect(err).To(BeNil())

				// Create options with custom WEBDIR
				optionsFile := filepath.Join(buildDir, ".bp-config", "options.json")
				err = os.MkdirAll(filepath.Dir(optionsFile), 0755)
				Expect(err).To(BeNil())
				err = os.WriteFile(optionsFile, []byte(`{"WEB_SERVER": "httpd", "WEBDIR": "public"}`), 0644)
				Expect(err).To(BeNil())

				err = finalizer.CreateStartScript()
				Expect(err).To(BeNil())

				startScript := filepath.Join(buildDir, ".bp", "bin", "start")
				contents, err := os.ReadFile(startScript)
				Expect(err).To(BeNil())
				Expect(string(contents)).To(ContainSubstring("WEBDIR=\"public\""))
			})
		})

		Context("with default configuration", func() {
			It("uses default WEBDIR when not specified", func() {
				stager := &testStager{
					buildDir: buildDir,
					depsDir:  depsDir,
					depsIdx:  depsIdx,
				}

				manifest := &testManifest{
					versions: map[string][]string{"php": {"8.1.32"}},
					defaults: map[string]string{"php": "8.1.32"},
				}

				finalizer = &finalize.Finalizer{
					Manifest: manifest,
					Stager:   stager,
					Command:  &testCommand{},
					Log:      logger,
				}

				os.Setenv("BP_DIR", buildDir)
				rewriteSrc := filepath.Join(buildDir, "bin", "rewrite")
				err = os.MkdirAll(filepath.Dir(rewriteSrc), 0755)
				Expect(err).To(BeNil())
				err = os.WriteFile(rewriteSrc, []byte("#!/bin/bash\n"), 0755)
				Expect(err).To(BeNil())

				optionsFile := filepath.Join(buildDir, ".bp-config", "options.json")
				err = os.MkdirAll(filepath.Dir(optionsFile), 0755)
				Expect(err).To(BeNil())
				err = os.WriteFile(optionsFile, []byte(`{"WEB_SERVER": "httpd"}`), 0644)
				Expect(err).To(BeNil())

				err = finalizer.CreateStartScript()
				Expect(err).To(BeNil())

				startScript := filepath.Join(buildDir, ".bp", "bin", "start")
				contents, err := os.ReadFile(startScript)
				Expect(err).To(BeNil())
				// Should use default htdocs
				Expect(string(contents)).To(ContainSubstring("WEBDIR=\"htdocs\""))
			})
		})
	})

	Describe("Error handling", func() {
		Context("when options.json is invalid", func() {
			It("returns an error", func() {
				stager := &testStager{
					buildDir: buildDir,
					depsDir:  depsDir,
					depsIdx:  depsIdx,
				}

				manifest := &testManifest{
					versions: map[string][]string{"php": {"8.1.32"}},
					defaults: map[string]string{"php": "8.1.32"},
				}

				finalizer = &finalize.Finalizer{
					Manifest: manifest,
					Stager:   stager,
					Command:  &testCommand{},
					Log:      logger,
				}

				os.Setenv("BP_DIR", buildDir)

				// Create invalid JSON
				optionsFile := filepath.Join(buildDir, ".bp-config", "options.json")
				err = os.MkdirAll(filepath.Dir(optionsFile), 0755)
				Expect(err).To(BeNil())
				err = os.WriteFile(optionsFile, []byte(`{invalid json`), 0644)
				Expect(err).To(BeNil())

				err = finalizer.CreateStartScript()
				Expect(err).NotTo(BeNil())
			})
		})

		Context("when .bp/bin directory cannot be created", func() {
			It("returns an error", func() {
				// Create a file where directory should be
				bpPath := filepath.Join(buildDir, ".bp")
				err = os.WriteFile(bpPath, []byte("blocking file"), 0644)
				Expect(err).To(BeNil())

				stager := &testStager{
					buildDir: buildDir,
					depsDir:  depsDir,
					depsIdx:  depsIdx,
				}

				manifest := &testManifest{
					versions: map[string][]string{"php": {"8.1.32"}},
					defaults: map[string]string{"php": "8.1.32"},
				}

				finalizer = &finalize.Finalizer{
					Manifest: manifest,
					Stager:   stager,
					Command:  &testCommand{},
					Log:      logger,
				}

				os.Setenv("BP_DIR", buildDir)

				err = finalizer.CreateStartScript()
				Expect(err).NotTo(BeNil())
				Expect(err.Error()).To(ContainSubstring(".bp/bin"))
			})
		})
	})
})

// testStager is a simple test implementation of the Stager interface
type testStager struct {
	buildDir string
	depsDir  string
	depsIdx  string
}

func (t *testStager) BuildDir() string { return t.buildDir }
func (t *testStager) DepDir() string   { return filepath.Join(t.depsDir, t.depsIdx) }
func (t *testStager) DepsIdx() string  { return t.depsIdx }

func (t *testStager) WriteProfileD(scriptName, scriptContents string) error {
	profileDir := filepath.Join(t.depsDir, t.depsIdx, "profile.d")
	if err := os.MkdirAll(profileDir, 0755); err != nil {
		return err
	}
	return os.WriteFile(filepath.Join(profileDir, scriptName), []byte(scriptContents), 0644)
}

func (t *testStager) SetLaunchEnvironment() error {
	// Copy profile.d scripts from deps to BUILD_DIR/.profile.d
	profileSrc := filepath.Join(t.depsDir, t.depsIdx, "profile.d")
	profileDst := filepath.Join(t.buildDir, ".profile.d")

	if err := os.MkdirAll(profileDst, 0755); err != nil {
		return err
	}

	// Read all scripts from source
	entries, err := os.ReadDir(profileSrc)
	if err != nil {
		if os.IsNotExist(err) {
			return nil // No profile.d scripts to copy
		}
		return err
	}

	// Copy each script
	for _, entry := range entries {
		if !entry.IsDir() {
			src := filepath.Join(profileSrc, entry.Name())
			dst := filepath.Join(profileDst, entry.Name())

			data, err := os.ReadFile(src)
			if err != nil {
				return err
			}

			if err := os.WriteFile(dst, data, 0644); err != nil {
				return err
			}
		}
	}

	return nil
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

func (t *testManifest) IsCached() bool {
	return t.cached
}

// testCommand is a simple test implementation of the Command interface
type testCommand struct {
	executed []string
}

func (t *testCommand) Execute(dir string, stdout io.Writer, stderr io.Writer, program string, args ...string) error {
	t.executed = append(t.executed, program)
	return nil
}
