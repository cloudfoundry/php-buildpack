package supply_test

import (
	"bytes"
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"php/supply"

	"github.com/cloudfoundry/libbuildpack"
	"github.com/cloudfoundry/libbuildpack/ansicleaner"
	"github.com/golang/mock/gomock"
	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

//go:generate mockgen -source=supply.go --destination=mocks_test.go --package=supply_test

var _ = Describe("Supply", func() {
	var (
		err            error
		buildDir       string
		cacheDir       string
		depsDir        string
		depsIdx        string
		supplier       *supply.Supplier
		logger         *libbuildpack.Logger
		buffer         *bytes.Buffer
		mockCtrl       *gomock.Controller
		mockManifest   *MockManifest
		mockCommand    *MockCommand
		mockHttpClient *MockHttpClient
	)

	BeforeEach(func() {
		buildDir, err = ioutil.TempDir("", "php-buildpack.build.")
		Expect(err).To(BeNil())
		cacheDir, err = ioutil.TempDir("", "php-buildpack.cache.")
		Expect(err).To(BeNil())
		depsDir, err = ioutil.TempDir("", "php-buildpack.deps.")
		Expect(err).To(BeNil())

		depsIdx = "9"
		Expect(os.MkdirAll(filepath.Join(depsDir, depsIdx), 0755)).To(Succeed())

		buffer = new(bytes.Buffer)
		logger = libbuildpack.NewLogger(ansicleaner.New(buffer))

		mockCtrl = gomock.NewController(GinkgoT())
		mockManifest = NewMockManifest(mockCtrl)
		mockCommand = NewMockCommand(mockCtrl)
		mockHttpClient = NewMockHttpClient(mockCtrl)

		args := []string{buildDir, cacheDir, depsDir, depsIdx}
		stager := libbuildpack.NewStager(args, logger, &libbuildpack.Manifest{})

		supplier = &supply.Supplier{
			Stager:     stager,
			Manifest:   mockManifest,
			Log:        logger,
			Command:    mockCommand,
			JSON:       libbuildpack.NewJSON(),
			YAML:       libbuildpack.NewYAML(),
			HttpClient: mockHttpClient,
		}
	})

	AfterEach(func() {
		mockCtrl.Finish()
		Expect(os.RemoveAll(buildDir)).To(Succeed())
		Expect(os.RemoveAll(cacheDir)).To(Succeed())
		Expect(os.RemoveAll(depsDir)).To(Succeed())
	})

	Describe("ReadConfig", func() {
		Context("options.json exists in app", func() {
			Context("valid json", func() {
				BeforeEach(func() {
					Expect(os.MkdirAll(filepath.Join(buildDir, ".bp-config"), 0755)).To(Succeed())
					Expect(ioutil.WriteFile(filepath.Join(buildDir, ".bp-config", "options.json"), []byte(`{"mykey":"myval"}`), 0644)).To(Succeed())
				})
				It("sets ConfigJson", func() {
					Expect(supplier.ReadConfig()).To(Succeed())
					Expect(supplier.OptionsJson["mykey"]).To(Equal("myval"))
				})
			})
			Context("invalid json", func() {
				BeforeEach(func() {
					Expect(os.MkdirAll(filepath.Join(buildDir, ".bp-config"), 0755)).To(Succeed())
					Expect(ioutil.WriteFile(filepath.Join(buildDir, ".bp-config", "options.json"), []byte(`{`), 0644)).To(Succeed())
				})
				It("fail", func() {
					Expect(supplier.ReadConfig()).ToNot(Succeed())
					Expect(buffer.String()).To(ContainSubstring("Invalid JSON present in options.json."))
				})
			})
		})
		Context("app/composer.json exists", func() {
			BeforeEach(func() {
				Expect(ioutil.WriteFile(filepath.Join(buildDir, "composer.json"), []byte(`{"mykey":"myval"}`), 0644)).To(Succeed())
			})
			It("sets ComposerJson", func() {
				Expect(supplier.ReadConfig()).To(Succeed())
				Expect(supplier.ComposerJson["mykey"]).To(Equal("myval"))
			})
			Context("invalid json", func() {
				BeforeEach(func() {
					Expect(ioutil.WriteFile(filepath.Join(buildDir, "composer.json"), []byte(`invalid`), 0644)).To(Succeed())
				})
				It("fails", func() {
					Expect(supplier.ReadConfig()).ToNot(Succeed())
					Expect(buffer.String()).To(ContainSubstring("Invalid JSON present in composer.json."))
				})
			})
		})
		Context("ENV[COMPOSER_PATH]/composer.json exists", func() {
			BeforeEach(func() {
				Expect(ioutil.WriteFile(filepath.Join(buildDir, "composer.json"), []byte(`{"mykey":"myval"}`), 0644)).To(Succeed())
			})
			It("sets ComposerJson", func() {
				Expect(supplier.ReadConfig()).To(Succeed())
				Expect(supplier.ComposerJson["mykey"]).To(Equal("myval"))
			})
		})
	})
	Describe("SetupWebDir", func() {
		Context("specificd in options.json", func() {
			BeforeEach(func() {
				supplier.OptionsJson = map[string]interface{}{"WEBDIR": "my/dir"}
			})
			It("sets WebDir to value from options.json", func() {
				supplier.SetupWebDir()
				Expect(supplier.WebDir).To(Equal("my/dir"))
			})
		})
		Context("app has htdocs directory", func() {
			BeforeEach(func() {
				Expect(os.Mkdir(filepath.Join(buildDir, "htdocs"), 0755)).To(Succeed())
			})
			It("sets WebDir to old default htdocs", func() {
				supplier.SetupWebDir()
				Expect(supplier.WebDir).To(Equal("htdocs"))
			})
		})
		Context("default", func() {
			It("sets WebDir to app", func() {
				supplier.SetupWebDir()
				Expect(supplier.WebDir).To(Equal(""))
			})
		})
	})
	Describe("SetupPhpVersion", func() {
		BeforeEach(func() {
			mockManifest.EXPECT().AllDependencyVersions("php").
				AnyTimes().Return([]string{"1.3.5", "1.3.6", "2.3.4", "2.3.5", "3.4.5", "3.4.6", "3.4.7", "7.1.2"})
		})
		Context("no app settings files", func() {
			BeforeEach(func() {
				mockManifest.EXPECT().DefaultVersion("php").
					AnyTimes().Return(libbuildpack.Dependency{Version: "1.3.5"}, nil)
				Expect(supplier.SetupPhpVersion()).To(Succeed())
			})
			It("sets php version from default php version", func() {
				Expect(supplier.PhpVersion).To(Equal("1.3.5"))
			})
			It("does NOT emit warnings", func() {
				Expect(buffer.String()).ToNot(ContainSubstring("WARNING"))
			})
		})
		Context("app has settings files, but no requested versions in them", func() {
			BeforeEach(func() {
				mockManifest.EXPECT().DefaultVersion("php").Return(libbuildpack.Dependency{Version: "1.3.5"}, nil)
				supplier.OptionsJson = map[string]interface{}{}
				supplier.ComposerJson = map[string]interface{}{"require": map[string]interface{}{}}
				Expect(supplier.SetupPhpVersion()).To(Succeed())
			})
			It("sets php version from default php version", func() {
				Expect(supplier.PhpVersion).To(Equal("1.3.5"))
			})
			It("does NOT emit warnings", func() {
				Expect(buffer.String()).ToNot(ContainSubstring("WARNING"))
			})
		})
		Context("options.json has requested version", func() {
			BeforeEach(func() {
				supplier.OptionsJson = map[string]interface{}{"PHP_VERSION": "2.3.4"}
				Expect(supplier.SetupPhpVersion()).To(Succeed())
			})
			It("sets php version", func() {
				Expect(supplier.PhpVersion).To(Equal("2.3.4"))
			})
			It("does NOT emit warnings", func() {
				Expect(buffer.String()).ToNot(ContainSubstring("WARNING"))
			})
		})
		Context("options.json has requested version of PHP_71_LATEST", func() {
			BeforeEach(func() {
				supplier.OptionsJson = map[string]interface{}{"PHP_VERSION": "PHP_71_LATEST"}
				Expect(supplier.SetupPhpVersion()).To(Succeed())
			})
			It("sets php version", func() {
				Expect(supplier.PhpVersion).To(Equal("7.1.2"))
			})
		})
		Context("composer.json has requested version", func() {
			BeforeEach(func() {
				supplier.ComposerJson = map[string]interface{}{
					"require": map[string]interface{}{
						"php": "3.4.5",
					},
				}
				Expect(supplier.SetupPhpVersion()).To(Succeed())
			})
			It("sets php version", func() {
				Expect(supplier.PhpVersion).To(Equal("3.4.5"))
			})
			It("does NOT emit warnings", func() {
				Expect(buffer.String()).ToNot(ContainSubstring("WARNING"))
			})
		})
		Context("composer.json has requested version range (composer semver >=)", func() {
			BeforeEach(func() {
				supplier.ComposerJson = map[string]interface{}{
					"require": map[string]interface{}{
						"php": ">=3.4.5",
					},
				}
				Expect(supplier.SetupPhpVersion()).To(Succeed())
			})
			It("sets php version", func() {
				Expect(supplier.PhpVersion).To(Equal("3.4.7"))
			})
			It("does NOT emit warnings", func() {
				Expect(buffer.String()).ToNot(ContainSubstring("WARNING"))
			})
		})
		Context("both options.json and composer.json set versions", func() {
			BeforeEach(func() {
				supplier.OptionsJson = map[string]interface{}{"PHP_VERSION": "2.3.4"}
				supplier.ComposerJson = map[string]interface{}{
					"require": map[string]interface{}{
						"php": "3.4.5",
					},
				}
				Expect(supplier.SetupPhpVersion()).To(Succeed())
			})
			It("warns user", func() {
				Expect(buffer.String()).To(ContainSubstring("WARNING"))
				Expect(buffer.String()).To(ContainSubstring("A version of PHP has been specified in both `composer.json` and `./bp-config/options.json`."))
				Expect(buffer.String()).To(ContainSubstring("The version defined in `composer.json` will be used."))
			})
			It("chooses composer.json version", func() {
				Expect(supplier.PhpVersion).To(Equal("3.4.5"))
			})
		})
	})
	Describe("SetupExtensions", func() {
		It("has default extensions", func() {
			Expect(supplier.SetupExtensions()).To(Succeed())
			Expect(supplier.PhpExtensions).To(Equal(map[string]bool{"bz2": true, "zlib": true, "curl": true, "mcrypt": true}))
			Expect(supplier.ZendExtensions).To(Equal([]string{}))
		})
		Context("options.json has extenions", func() {
			BeforeEach(func() {
				supplier.OptionsJson = map[string]interface{}{
					"PHP_EXTENSIONS": []interface{}{"fred", "jane"},
				}
				Expect(supplier.SetupExtensions()).To(Succeed())
			})
			It("uses those extensions", func() {
				Expect(supplier.PhpExtensions).To(Equal(map[string]bool{"fred": true, "jane": true}))
			})
		})
		Context("options.json has zend extenions", func() {
			BeforeEach(func() {
				supplier.OptionsJson = map[string]interface{}{
					"ZEND_EXTENSIONS": []interface{}{"fred", "jane"},
				}
				Expect(supplier.SetupExtensions()).To(Succeed())
			})
			It("uses those zend extensions (in order)", func() {
				Expect(supplier.ZendExtensions).To(Equal([]string{"fred", "jane"}))
			})
		})
		Context("composer.json has extensions", func() {
			BeforeEach(func() {
				supplier.ComposerJson = map[string]interface{}{
					"require": map[string]interface{}{
						"thing":        "*",
						"ext-meatball": "*",
						"other":        "*",
						"ext-sub":      "*",
					},
				}
				Expect(supplier.SetupExtensions()).To(Succeed())
			})
			It("uses requires preceded by 'ext-'", func() {
				Expect(supplier.PhpExtensions).To(Equal(map[string]bool{"meatball": true, "sub": true}))
			})
		})
		Context("composer.lock has extensions", func() {
			BeforeEach(func() {
				supplier.ComposerJson = map[string]interface{}{
					"require": map[string]interface{}{
						"thing":        "*",
						"ext-meatball": "*",
					},
				}
				supplier.ComposerLock = map[string]interface{}{
					"packages": []interface{}{map[string]interface{}{
						"require": map[string]interface{}{
							"other":   "*",
							"ext-sub": "*",
						},
					}},
				}
				Expect(supplier.SetupExtensions()).To(Succeed())
			})
			It("merges with composer.json", func() {
				Expect(supplier.PhpExtensions).To(Equal(map[string]bool{"meatball": true, "sub": true}))
			})
		})
	})
	Describe("RemoveUnknownExtensions", func() {
		BeforeEach(func() {
			supplier.PhpExtensions = map[string]bool{
				"salami": true, "cheese": true, "bacon": true,
			}
			// Compiled Modules
			mockCommand.EXPECT().Output("", "php", "-m").Return("[section]\nsalami\nother\n", nil)
			// Available Modules
			Expect(os.MkdirAll(filepath.Join(depsDir, depsIdx, "php", "lib", "php", "extensions", "no-debug-non-zts-20180401"), 0755)).To(Succeed())
			Expect(ioutil.WriteFile(filepath.Join(depsDir, depsIdx, "php", "lib", "php", "extensions", "no-debug-non-zts-20180401", "cheese.so"), []byte(""), 0644)).To(Succeed())
			//Run
			Expect(supplier.RemoveUnknownExtensions()).To(Succeed())
		})
		It("removes compiled in modules (and issues debug message)", func() {
			Expect(supplier.PhpExtensions).ToNot(HaveKey("salami"))
		})
		It("removes unsuported modules (and issues warning)", func() {
			Expect(supplier.PhpExtensions).ToNot(HaveKey("bacon"))
		})
		It("leaves available modules in list (no output)", func() {
			Expect(supplier.PhpExtensions).To(HaveKey("cheese"))
		})
	})
	Describe("ValidatePhpIniExtensions", func() {
		BeforeEach(func() {
			// Compiled Modules
			mockCommand.EXPECT().Output("", "php", "-m").Return("[section]\nsalami\nother\n", nil)
			// Available Modules
			Expect(os.MkdirAll(filepath.Join(depsDir, depsIdx, "php", "lib", "php", "extensions", "no-debug-non-zts-20180401"), 0755)).To(Succeed())
			Expect(ioutil.WriteFile(filepath.Join(depsDir, depsIdx, "php", "lib", "php", "extensions", "no-debug-non-zts-20180401", "cheese.so"), []byte(""), 0644)).To(Succeed())
		})
		Context("all modules in file are available", func() {
			BeforeEach(func() {
				Expect(os.MkdirAll(filepath.Join(buildDir, ".bp-config", "php", "php.ini.d"), 0755)).To(Succeed())
				Expect(ioutil.WriteFile(filepath.Join(buildDir, ".bp-config", "php", "php.ini.d", "php.ini"), []byte(`
something
extension=salami.so
extension=cheese.so
other
`), 0644)).To(Succeed())
			})
			It("succeeds", func() {
				Expect(supplier.ValidatePhpIniExtensions()).To(Succeed())
			})
		})
		Context("any modules are not available", func() {
			BeforeEach(func() {
				Expect(os.MkdirAll(filepath.Join(buildDir, ".bp-config", "php", "php.ini.d"), 0755)).To(Succeed())
				Expect(ioutil.WriteFile(filepath.Join(buildDir, ".bp-config", "php", "php.ini.d", "php.ini"), []byte(`
something
extension=salami.so
extension=beef.so
extension=cheese.so
other
`), 0644)).To(Succeed())
			})
			It("tells the user and fails", func() {
				Expect(supplier.ValidatePhpIniExtensions()).To(MatchError("app requested unavailable extensions in php.ini.d files"))
				Expect(buffer).To(ContainSubstring("The extension 'beef' is not provided by this buildpack."))
			})
			It("looks at all inifiles", func() {
				Expect(ioutil.WriteFile(filepath.Join(buildDir, ".bp-config", "php", "php.ini.d", "otherfile.ini"), []byte(`
extension=pineapple.so
`), 0644)).To(Succeed())
				supplier.ValidatePhpIniExtensions()
				Expect(buffer).To(ContainSubstring("The extension 'pineapple' is not provided by this buildpack."))
			})
		})
	})

	Describe("InstallHTTPD", func() {
		BeforeEach(func() {
			mockManifest.EXPECT().InstallOnlyVersion("httpd", filepath.Join(depsDir, depsIdx)).Do(func(_, path string) error {
				os.MkdirAll(filepath.Join(path, "httpd", "bin"), 0755)
				ioutil.WriteFile(filepath.Join(path, "httpd", "bin", "apachectl"), []byte("stuff\nHTTPD='/app/httpd/bin/httpd'\nother\n"), 0755)
				os.MkdirAll(filepath.Join(path, "httpd", "lib"), 0755)
				ioutil.WriteFile(filepath.Join(path, "httpd", "lib", "thing.so"), []byte(""), 0644)
				return nil
			})
		})
		It("copies httpd to deps dir", func() {
			Expect(supplier.InstallHTTPD()).To(Succeed())
			Expect(filepath.Join(depsDir, depsIdx, "httpd", "bin", "apachectl")).To(BeAnExistingFile())
		})
		It("symlinks bin directory files", func() {
			Expect(supplier.InstallHTTPD()).To(Succeed())
			Expect(filepath.Join(depsDir, depsIdx, "bin", "apachectl")).To(BeAnExistingFile())
		})
		It("symlinks bin directory files", func() {
			Expect(supplier.InstallHTTPD()).To(Succeed())
			Expect(filepath.Join(depsDir, depsIdx, "lib", "thing.so")).To(BeAnExistingFile())
		})
		It("modifies apachectl to use $DEPS_DIR", func() {
			Expect(supplier.InstallHTTPD()).To(Succeed())
			txt, err := ioutil.ReadFile(filepath.Join(depsDir, depsIdx, "bin", "apachectl"))
			Expect(err).ToNot(HaveOccurred())
			Expect(string(txt)).To(Equal("stuff\nHTTPD=\"$DEPS_DIR/9/httpd/bin/httpd\"\nother\n"))
		})
	})

	Describe("InstallPHP", func() {
		BeforeEach(func() {
			supplier.PhpVersion = "3.4.5"
			mockManifest.EXPECT().InstallDependency(libbuildpack.Dependency{Name: "php", Version: "3.4.5"}, filepath.Join(depsDir, depsIdx)).Do(func(_ libbuildpack.Dependency, path string) error {
				os.MkdirAll(filepath.Join(path, "php", "bin"), 0755)
				ioutil.WriteFile(filepath.Join(path, "php", "bin", "php"), []byte(""), 0755)
				os.MkdirAll(filepath.Join(path, "php", "lib"), 0755)
				ioutil.WriteFile(filepath.Join(path, "php", "lib", "thing.so"), []byte(""), 0644)
				return nil
			})
		})
		It("copies php to deps dir", func() {
			Expect(supplier.InstallPHP()).To(Succeed())
			Expect(filepath.Join(depsDir, depsIdx, "php", "bin", "php")).To(BeAnExistingFile())
			Expect(filepath.Join(depsDir, depsIdx, "php", "lib", "thing.so")).To(BeAnExistingFile())
		})
		It("symlinks bin directory files", func() {
			Expect(supplier.InstallPHP()).To(Succeed())
			Expect(filepath.Join(depsDir, depsIdx, "bin", "php")).To(BeAnExistingFile())
		})
		It("symlinks bin directory files", func() {
			Expect(supplier.InstallPHP()).To(Succeed())
			Expect(filepath.Join(depsDir, depsIdx, "lib", "thing.so")).To(BeAnExistingFile())
		})
	})

	Describe("WriteConfigFiles", func() {
		BeforeEach(func() {
			supplier.PhpVersion = "7.1.1"
			Expect(os.MkdirAll(filepath.Join(depsDir, depsIdx, "php", "etc"), 0755)).To(Succeed())
		})
		It("Writes interpolated php-fpm.conf", func() {
			Expect(supplier.WriteConfigFiles()).To(Succeed())
			body, _ := ioutil.ReadFile(filepath.Join(depsDir, depsIdx, "php", "etc", "php-fpm.conf"))
			Expect(string(body)).To(ContainSubstring("pid = {{.DEPS_DIR}}/9/php/var/run/php-fpm.pid"))
		})
		It("Writes interpolated httpd.conf", func() {
			Expect(supplier.WriteConfigFiles()).To(Succeed())
			body, _ := ioutil.ReadFile(filepath.Join(depsDir, depsIdx, "httpd", "conf", "httpd.conf"))
			Expect(string(body)).To(ContainSubstring(`DocumentRoot "${HOME}/"`))
		})
		It("Writes interpolated httpd/extra/httpd-directories.conf", func() {
			Expect(supplier.WriteConfigFiles()).To(Succeed())
			body, _ := ioutil.ReadFile(filepath.Join(depsDir, depsIdx, "httpd", "conf", "extra", "httpd-directories.conf"))
			Expect(string(body)).To(ContainSubstring(`<Directory "${HOME}/">`))
		})
		It("writes fully interpolated files to staging config files", func() {
			Expect(supplier.WriteConfigFiles()).To(Succeed())

			body, _ := ioutil.ReadFile("/tmp/php_etc/php/etc/php-fpm.conf")
			Expect(string(body)).To(ContainSubstring(fmt.Sprintf("pid = %s/9/php/var/run/php-fpm.pid", depsDir)))

			body, _ = ioutil.ReadFile("/tmp/php_etc/httpd/conf/extra/httpd-directories.conf")
			Expect(string(body)).To(ContainSubstring(`<Directory "${HOME}/">`))
		})
	})

	Describe("InstallComposer", func() {
		Context("one version of composer in manifest.yml", func() {
			BeforeEach(func() {
				mockManifest.EXPECT().AllDependencyVersions("composer").Return([]string{"6.5.4"})
				mockManifest.EXPECT().FetchDependency(
					libbuildpack.Dependency{Name: "composer", Version: "6.5.4"},
					filepath.Join(depsDir, depsIdx, "bin", "composer"),
				)
				Expect(supplier.InstallComposer()).To(Succeed())
			})
			It("logs installing composer and version", func() {
				Expect(buffer.String()).To(ContainSubstring("Installing composer 6.5.4"))
			})
		})
		Context("multiple versions of composer in manifest.yml", func() {
			BeforeEach(func() {
				mockManifest.EXPECT().AllDependencyVersions("composer").Return([]string{"6.5.4", "1.2.3"})
			})
			It("fails", func() {
				Expect(supplier.InstallComposer()).To(MatchError("expected 1 version of composer, found 2"))
			})
		})
	})

	Describe("RunComposer", func() {
		Context("composer github token NOT provided", func() {
			It("runs composer using staging PHPRC", func() {
				mockCommand.EXPECT().Run(gomock.Any()).Do(func(cmd *exec.Cmd) error {
					Expect(cmd.Env).To(ContainElement("COMPOSER_NO_INTERACTION=1"))
					Expect(cmd.Env).To(ContainElement(fmt.Sprintf("COMPOSER_CACHE_DIR=%s/composer", cacheDir)))
					Expect(cmd.Env).To(ContainElement(fmt.Sprintf("COMPOSER_VENDOR_DIR=%s/vendor", buildDir)))
					Expect(cmd.Env).To(ContainElement(fmt.Sprintf("COMPOSER_BIN_DIR=%s/9/php/bin", depsDir)))
					Expect(cmd.Env).To(ContainElement("PHPRC=/tmp/php_etc/php/etc"))
					Expect(cmd.Path).To(Equal("php"))
					Expect(cmd.Args).To(Equal([]string{
						"php",
						filepath.Join(depsDir, depsIdx, "bin", "composer"),
						"install",
						"--no-progress",
						"--no-dev",
					}))
					return nil
				})
				Expect(supplier.RunComposer()).To(Succeed())
			})
		})
		Context("composer github token IS provided AND valid", func() {
			BeforeEach(func() {
				supplier.ComposerGithubToken = "abcdef"
				mockHttpClient.EXPECT().Do(gomock.Any()).Return(&http.Response{
					Body: ioutil.NopCloser(bytes.NewBufferString(`{"resources":{}}`)),
				}, nil)
			})
			It("sets composer github-oauth.github.com before running composer using staging PHPRC", func() {
				mockCommand.EXPECT().Run(gomock.Any()).Do(func(cmd *exec.Cmd) error {
					Expect(cmd.Args).To(Equal([]string{
						"php",
						filepath.Join(depsDir, depsIdx, "bin", "composer"),
						"config", "-g", "github-oauth.github.com", supplier.ComposerGithubToken,
					}))
					return nil
				})
				mockCommand.EXPECT().Run(gomock.Any()).Do(func(cmd *exec.Cmd) error {
					Expect(cmd.Args).To(Equal([]string{
						"php",
						filepath.Join(depsDir, depsIdx, "bin", "composer"),
						"install",
						"--no-progress",
						"--no-dev",
					}))
					return nil
				})
				Expect(supplier.RunComposer()).To(Succeed())
			})
		})

		Context("composer github token is provided BUT invalid", func() {
			BeforeEach(func() {
				supplier.ComposerGithubToken = "abcdef"
				mockHttpClient.EXPECT().Do(gomock.Any()).Return(&http.Response{
					Body: ioutil.NopCloser(bytes.NewBufferString(`{}`)),
				}, nil)
			})
			It("runs composer using staging PHPRC without github-oauth.github.com", func() {
				mockCommand.EXPECT().Run(gomock.Any()).Do(func(cmd *exec.Cmd) error {
					Expect(cmd.Args).To(Equal([]string{
						"php",
						filepath.Join(depsDir, depsIdx, "bin", "composer"),
						"install",
						"--no-progress",
						"--no-dev",
					}))
					return nil
				})
				Expect(supplier.RunComposer()).To(Succeed())
			})
		})
	})

	Describe("InstallVarify", func() {
		Context("buildpack is NOT built, thus bin/supply places varify in place", func() {
			BeforeEach(func() {
				Expect(os.MkdirAll(filepath.Join(depsDir, depsIdx, "bin"), 0755)).To(Succeed())
				Expect(ioutil.WriteFile(filepath.Join(depsDir, depsIdx, "bin", "varify"), []byte(""), 0755)).To(Succeed())
			})
			It("does nothing", func() {
				Expect(supplier.InstallVarify()).To(Succeed())
			})
		})
		Context("buildpack IS built", func() {
			BeforeEach(func() {
				buildpackDir, err := ioutil.TempDir("", "php-buildpack.build.")
				Expect(err).ToNot(HaveOccurred())
				mockManifest.EXPECT().RootDir().Return(buildpackDir)
				Expect(os.MkdirAll(filepath.Join(buildpackDir, "bin"), 0755)).To(Succeed())
				Expect(ioutil.WriteFile(filepath.Join(buildpackDir, "bin", "varify"), []byte("binary for varify"), 0755)).To(Succeed())
			})
			It("copies varify to depDir/bin", func() {
				Expect(supplier.InstallVarify()).To(Succeed())
				Expect(filepath.Join(depsDir, depsIdx, "bin", "varify")).To(BeAnExistingFile())
				Expect(ioutil.ReadFile(filepath.Join(depsDir, depsIdx, "bin", "varify"))).To(Equal([]byte("binary for varify")))
			})
		})
	})

	Describe("InstallProcfiled", func() {
		Context("buildpack is NOT built, thus bin/supply places procfiled in place", func() {
			BeforeEach(func() {
				Expect(os.MkdirAll(filepath.Join(depsDir, depsIdx, "bin"), 0755)).To(Succeed())
				Expect(ioutil.WriteFile(filepath.Join(depsDir, depsIdx, "bin", "procfiled"), []byte(""), 0755)).To(Succeed())
			})
			It("does nothing", func() {
				Expect(supplier.InstallProcfiled()).To(Succeed())
			})
		})
		Context("buildpack IS built", func() {
			BeforeEach(func() {
				buildpackDir, err := ioutil.TempDir("", "php-buildpack.build.")
				Expect(err).ToNot(HaveOccurred())
				mockManifest.EXPECT().RootDir().Return(buildpackDir)
				Expect(os.MkdirAll(filepath.Join(buildpackDir, "bin"), 0755)).To(Succeed())
				Expect(ioutil.WriteFile(filepath.Join(buildpackDir, "bin", "procfiled"), []byte("binary for procfiled"), 0755)).To(Succeed())
			})
			It("copies procfiled to depDir/bin", func() {
				Expect(supplier.InstallProcfiled()).To(Succeed())
				Expect(filepath.Join(depsDir, depsIdx, "bin", "procfiled")).To(BeAnExistingFile())
				Expect(ioutil.ReadFile(filepath.Join(depsDir, depsIdx, "bin", "procfiled"))).To(Equal([]byte("binary for procfiled")))
			})
		})
	})

	Describe("WriteProfileD", func() {
		It("sets PHPRC", func() {
			Expect(supplier.WriteProfileD()).To(Succeed())
			Expect(ioutil.ReadFile(filepath.Join(depsDir, depsIdx, "profile.d", "bp_env_vars.sh"))).
				To(ContainSubstring("export PHPRC=$DEPS_DIR/9/php/etc\n"))
		})
		Context("php.ini.d was supplied", func() {
			BeforeEach(func() {
				Expect(os.MkdirAll(filepath.Join(depsDir, depsIdx, "php/etc/php.ini.d"), 0755)).To(Succeed())
			})
			It("sets PHP_INI_SCAN_DIR", func() {
				Expect(supplier.WriteProfileD()).To(Succeed())
				Expect(ioutil.ReadFile(filepath.Join(depsDir, depsIdx, "profile.d", "bp_env_vars.sh"))).
					To(ContainSubstring("export PHP_INI_SCAN_DIR=$DEPS_DIR/9/php/etc/php.ini.d\n"))
			})
		})
		Context("php.ini.d was NOT supplied", func() {
			It("does NOT set PHP_INI_SCAN_DIR", func() {
				Expect(supplier.WriteProfileD()).To(Succeed())
				Expect(ioutil.ReadFile(filepath.Join(depsDir, depsIdx, "profile.d", "bp_env_vars.sh"))).
					ToNot(ContainSubstring("PHP_INI_SCAN_DIR"))
			})
		})
	})

	Describe("WriteStartFile", func() {
		BeforeEach(func() {
			Expect(os.MkdirAll(filepath.Join(depsDir, depsIdx, "bin"), 0755)).To(Succeed())
		})
		It("writes Procfile with httpd and php-fpm", func() {
			Expect(supplier.WriteStartFile()).To(Succeed())
			Expect(filepath.Join(depsDir, depsIdx, "Procfile")).To(BeAnExistingFile())
			Expect(ioutil.ReadFile(filepath.Join(depsDir, depsIdx, "Procfile"))).To(MatchYAML(`---
php-fpm: exec $DEPS_DIR/9/php/sbin/php-fpm -p "$DEPS_DIR/9/php/etc" -y "$DEPS_DIR/9/php/etc/php-fpm.conf" -c "$DEPS_DIR/9/php/etc"
httpd: exec $DEPS_DIR/9/httpd/bin/apachectl -f "$DEPS_DIR/9/httpd/conf/httpd.conf" -k start -DFOREGROUND`))
		})
		It("writes bin/php_buildpack_start", func() {
			Expect(supplier.WriteStartFile()).To(Succeed())
			Expect(filepath.Join(depsDir, depsIdx, "bin", "php_buildpack_start")).To(BeAnExistingFile())
			Expect(ioutil.ReadFile(filepath.Join(depsDir, depsIdx, "bin", "php_buildpack_start"))).To(Equal([]byte("#!/usr/bin/env bash\nexec $DEPS_DIR/9/bin/procfiled $DEPS_DIR/9/Procfile\n")))
		})
	})
})
