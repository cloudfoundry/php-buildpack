package composer_test

import (
	"os"
	"path/filepath"

	"github.com/cloudfoundry/php-buildpack/src/php/extensions"
	"github.com/cloudfoundry/php-buildpack/src/php/extensions/composer"
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
)

var _ = Describe("ComposerExtension", func() {
	var (
		ext      *composer.ComposerExtension
		ctx      *extensions.Context
		buildDir string
		tempDir  string
	)

	BeforeEach(func() {
		var err error
		buildDir, err = os.MkdirTemp("", "composer-test-build")
		Expect(err).NotTo(HaveOccurred())

		tempDir, err = os.MkdirTemp("", "composer-test-temp")
		Expect(err).NotTo(HaveOccurred())

		ctx, err = extensions.NewContext()
		Expect(err).NotTo(HaveOccurred())
		ctx.Set("BUILD_DIR", buildDir)
		ctx.Set("BP_DIR", "/tmp/bp")
		ctx.Set("WEBDIR", "htdocs")
		ctx.Set("PHP_DEFAULT", "8.1.32")
		ctx.Set("ALL_PHP_VERSIONS", "8.1.31,8.1.32,8.2.26,8.2.28,8.3.19,8.3.21")

		ext = &composer.ComposerExtension{}
	})

	AfterEach(func() {
		if buildDir != "" {
			os.RemoveAll(buildDir)
		}
		if tempDir != "" {
			os.RemoveAll(tempDir)
		}
	})

	Describe("Name", func() {
		It("should return 'composer'", func() {
			Expect(ext.Name()).To(Equal("composer"))
		})
	})

	Describe("ShouldCompile", func() {
		Context("when composer.json exists in build directory", func() {
			BeforeEach(func() {
				composerJSON := filepath.Join(buildDir, "composer.json")
				err := os.WriteFile(composerJSON, []byte(`{"name":"test/app"}`), 0644)
				Expect(err).NotTo(HaveOccurred())
			})

			It("should return true", func() {
				Expect(ext.ShouldCompile(ctx)).To(BeTrue())
			})
		})

		Context("when composer.lock exists in build directory", func() {
			BeforeEach(func() {
				composerLock := filepath.Join(buildDir, "composer.lock")
				err := os.WriteFile(composerLock, []byte(`{}`), 0644)
				Expect(err).NotTo(HaveOccurred())
			})

			It("should return true", func() {
				Expect(ext.ShouldCompile(ctx)).To(BeTrue())
			})
		})

		Context("when composer files exist in webdir", func() {
			BeforeEach(func() {
				webDir := filepath.Join(buildDir, "htdocs")
				err := os.MkdirAll(webDir, 0755)
				Expect(err).NotTo(HaveOccurred())

				composerJSON := filepath.Join(webDir, "composer.json")
				err = os.WriteFile(composerJSON, []byte(`{"name":"test/app"}`), 0644)
				Expect(err).NotTo(HaveOccurred())
			})

			It("should return true", func() {
				Expect(ext.ShouldCompile(ctx)).To(BeTrue())
			})
		})

		Context("when no composer files exist", func() {
			It("should return false", func() {
				Expect(ext.ShouldCompile(ctx)).To(BeFalse())
			})
		})

		Context("when COMPOSER_PATH is set", func() {
			BeforeEach(func() {
				os.Setenv("COMPOSER_PATH", "customdir")

				customDir := filepath.Join(buildDir, "customdir")
				err := os.MkdirAll(customDir, 0755)
				Expect(err).NotTo(HaveOccurred())

				composerJSON := filepath.Join(customDir, "composer.json")
				err = os.WriteFile(composerJSON, []byte(`{"name":"test/app"}`), 0644)
				Expect(err).NotTo(HaveOccurred())
			})

			AfterEach(func() {
				os.Unsetenv("COMPOSER_PATH")
			})

			It("should find composer.json in custom path", func() {
				Expect(ext.ShouldCompile(ctx)).To(BeTrue())
			})
		})
	})

	Describe("Configure - Extension Detection", func() {
		Context("when composer.json has ext-* requirements", func() {
			BeforeEach(func() {
				composerJSON := filepath.Join(buildDir, "composer.json")
				content := `{
					"name": "test/app",
					"require": {
						"php": ">=7.4",
						"ext-mbstring": "*",
						"ext-pdo": "*",
						"ext-json": "*"
					}
				}`
				err := os.WriteFile(composerJSON, []byte(content), 0644)
				Expect(err).NotTo(HaveOccurred())

				ext.ShouldCompile(ctx)
			})

			It("should extract PHP extensions from composer.json", func() {
				err := ext.Configure(ctx)
				Expect(err).NotTo(HaveOccurred())

				phpExts := ctx.GetStringSlice("PHP_EXTENSIONS")
				Expect(phpExts).To(ContainElement("openssl")) // Always added for Composer
				Expect(phpExts).To(ContainElement("mbstring"))
				Expect(phpExts).To(ContainElement("pdo"))
				Expect(phpExts).To(ContainElement("json"))
			})

			It("should set PHP_VM to 'php'", func() {
				err := ext.Configure(ctx)
				Expect(err).NotTo(HaveOccurred())

				Expect(ctx.GetString("PHP_VM")).To(Equal("php"))
			})
		})

		Context("when composer.lock has ext-* requirements", func() {
			BeforeEach(func() {
				composerJSON := filepath.Join(buildDir, "composer.json")
				err := os.WriteFile(composerJSON, []byte(`{"name":"test/app"}`), 0644)
				Expect(err).NotTo(HaveOccurred())

				composerLock := filepath.Join(buildDir, "composer.lock")
				content := `{
					"packages": [],
					"packages-dev": [],
					"require": {
						"ext-redis": "*",
						"ext-memcached": "*"
					}
				}`
				err = os.WriteFile(composerLock, []byte(content), 0644)
				Expect(err).NotTo(HaveOccurred())

				ext.ShouldCompile(ctx)
			})

			It("should extract PHP extensions from composer.lock", func() {
				err := ext.Configure(ctx)
				Expect(err).NotTo(HaveOccurred())

				phpExts := ctx.GetStringSlice("PHP_EXTENSIONS")
				Expect(phpExts).To(ContainElement("redis"))
				Expect(phpExts).To(ContainElement("memcached"))
			})
		})

		Context("when existing PHP_EXTENSIONS are set", func() {
			BeforeEach(func() {
				ctx.Set("PHP_EXTENSIONS", []string{"curl", "gd"})

				composerJSON := filepath.Join(buildDir, "composer.json")
				content := `{
					"require": {
						"ext-mbstring": "*"
					}
				}`
				err := os.WriteFile(composerJSON, []byte(content), 0644)
				Expect(err).NotTo(HaveOccurred())

				ext.ShouldCompile(ctx)
			})

			It("should merge with existing extensions", func() {
				err := ext.Configure(ctx)
				Expect(err).NotTo(HaveOccurred())

				phpExts := ctx.GetStringSlice("PHP_EXTENSIONS")
				Expect(phpExts).To(ContainElement("curl"))     // Existing
				Expect(phpExts).To(ContainElement("gd"))       // Existing
				Expect(phpExts).To(ContainElement("mbstring")) // From composer.json
				Expect(phpExts).To(ContainElement("openssl"))  // Always added
			})
		})
	})

	Describe("Configure - PHP Version Selection", func() {
		Context("when composer.json specifies >= constraint", func() {
			BeforeEach(func() {
				composerJSON := filepath.Join(buildDir, "composer.json")
				content := `{
					"require": {
						"php": ">=7.4"
					}
				}`
				err := os.WriteFile(composerJSON, []byte(content), 0644)
				Expect(err).NotTo(HaveOccurred())

				ext.ShouldCompile(ctx)
			})

			It("should select highest available version", func() {
				err := ext.Configure(ctx)
				Expect(err).NotTo(HaveOccurred())

				phpVersion := ctx.GetString("PHP_VERSION")
				Expect(phpVersion).To(Equal("8.3.21"))
			})
		})

		Context("when composer.json specifies > constraint", func() {
			BeforeEach(func() {
				composerJSON := filepath.Join(buildDir, "composer.json")
				content := `{
					"require": {
						"php": ">8.2.26"
					}
				}`
				err := os.WriteFile(composerJSON, []byte(content), 0644)
				Expect(err).NotTo(HaveOccurred())

				ext.ShouldCompile(ctx)
			})

			It("should select highest version greater than constraint", func() {
				err := ext.Configure(ctx)
				Expect(err).NotTo(HaveOccurred())

				phpVersion := ctx.GetString("PHP_VERSION")
				// Should be 8.2.28 or 8.3.19 or 8.3.21
				Expect([]string{"8.2.28", "8.3.19", "8.3.21"}).To(ContainElement(phpVersion))
				Expect(phpVersion).To(Equal("8.3.21")) // Highest
			})
		})

		Context("when composer.json specifies <= constraint", func() {
			BeforeEach(func() {
				composerJSON := filepath.Join(buildDir, "composer.json")
				content := `{
					"require": {
						"php": "<=8.2.28"
					}
				}`
				err := os.WriteFile(composerJSON, []byte(content), 0644)
				Expect(err).NotTo(HaveOccurred())

				ext.ShouldCompile(ctx)
			})

			It("should select highest version less than or equal to constraint", func() {
				err := ext.Configure(ctx)
				Expect(err).NotTo(HaveOccurred())

				phpVersion := ctx.GetString("PHP_VERSION")
				Expect(phpVersion).To(Equal("8.2.28"))
			})
		})

		Context("when composer.json specifies < constraint", func() {
			BeforeEach(func() {
				composerJSON := filepath.Join(buildDir, "composer.json")
				content := `{
					"require": {
						"php": "<8.2.0"
					}
				}`
				err := os.WriteFile(composerJSON, []byte(content), 0644)
				Expect(err).NotTo(HaveOccurred())

				ext.ShouldCompile(ctx)
			})

			It("should select highest version less than constraint", func() {
				err := ext.Configure(ctx)
				Expect(err).NotTo(HaveOccurred())

				phpVersion := ctx.GetString("PHP_VERSION")
				Expect(phpVersion).To(Equal("8.1.32"))
			})
		})

		Context("when composer.json specifies ^ (caret) constraint", func() {
			BeforeEach(func() {
				composerJSON := filepath.Join(buildDir, "composer.json")
				content := `{
					"require": {
						"php": "^8.1"
					}
				}`
				err := os.WriteFile(composerJSON, []byte(content), 0644)
				Expect(err).NotTo(HaveOccurred())

				ext.ShouldCompile(ctx)
			})

			It("should select highest compatible version (same major)", func() {
				err := ext.Configure(ctx)
				Expect(err).NotTo(HaveOccurred())

				phpVersion := ctx.GetString("PHP_VERSION")
				// In Composer, ^8.1 means >=8.1.0 <9.0.0, so 8.3.21 is valid
				Expect(phpVersion).To(Equal("8.3.21"))
			})
		})

		Context("when composer.json specifies ~ (tilde) constraint", func() {
			BeforeEach(func() {
				composerJSON := filepath.Join(buildDir, "composer.json")
				content := `{
					"require": {
						"php": "~8.1.30"
					}
				}`
				err := os.WriteFile(composerJSON, []byte(content), 0644)
				Expect(err).NotTo(HaveOccurred())

				ext.ShouldCompile(ctx)
			})

			It("should select highest approximately equivalent version (same major.minor)", func() {
				err := ext.Configure(ctx)
				Expect(err).NotTo(HaveOccurred())

				phpVersion := ctx.GetString("PHP_VERSION")
				Expect(phpVersion).To(Equal("8.1.32"))
			})
		})

		Context("when composer.json specifies || (OR) constraint", func() {
			BeforeEach(func() {
				composerJSON := filepath.Join(buildDir, "composer.json")
				content := `{
					"require": {
						"php": "~8.1.30 || ~8.2.26"
					}
				}`
				err := os.WriteFile(composerJSON, []byte(content), 0644)
				Expect(err).NotTo(HaveOccurred())

				ext.ShouldCompile(ctx)
			})

			It("should select highest version matching any constraint", func() {
				err := ext.Configure(ctx)
				Expect(err).NotTo(HaveOccurred())

				phpVersion := ctx.GetString("PHP_VERSION")
				// Should match either 8.1.x or 8.2.x, highest is 8.2.28
				Expect([]string{"8.1.31", "8.1.32", "8.2.26", "8.2.28"}).To(ContainElement(phpVersion))
			})
		})

		Context("when composer.json specifies AND constraints (space-separated)", func() {
			BeforeEach(func() {
				composerJSON := filepath.Join(buildDir, "composer.json")
				content := `{
					"require": {
						"php": ">=8.1.0 <8.3.0"
					}
				}`
				err := os.WriteFile(composerJSON, []byte(content), 0644)
				Expect(err).NotTo(HaveOccurred())

				ext.ShouldCompile(ctx)
			})

			It("should select highest version matching all constraints", func() {
				err := ext.Configure(ctx)
				Expect(err).NotTo(HaveOccurred())

				phpVersion := ctx.GetString("PHP_VERSION")
				Expect(phpVersion).To(Equal("8.2.28"))
			})
		})

		Context("when composer.json specifies wildcard pattern", func() {
			BeforeEach(func() {
				composerJSON := filepath.Join(buildDir, "composer.json")
				content := `{
					"require": {
						"php": "8.2.*"
					}
				}`
				err := os.WriteFile(composerJSON, []byte(content), 0644)
				Expect(err).NotTo(HaveOccurred())

				ext.ShouldCompile(ctx)
			})

			It("should select highest version matching wildcard", func() {
				err := ext.Configure(ctx)
				Expect(err).NotTo(HaveOccurred())

				phpVersion := ctx.GetString("PHP_VERSION")
				Expect(phpVersion).To(Equal("8.2.28"))
			})
		})

		Context("when composer.json specifies exact version", func() {
			BeforeEach(func() {
				composerJSON := filepath.Join(buildDir, "composer.json")
				content := `{
					"require": {
						"php": "8.1.32"
					}
				}`
				err := os.WriteFile(composerJSON, []byte(content), 0644)
				Expect(err).NotTo(HaveOccurred())

				ext.ShouldCompile(ctx)
			})

			It("should select exact version if available", func() {
				err := ext.Configure(ctx)
				Expect(err).NotTo(HaveOccurred())

				phpVersion := ctx.GetString("PHP_VERSION")
				Expect(phpVersion).To(Equal("8.1.32"))
			})
		})

		Context("when no matching version is found", func() {
			BeforeEach(func() {
				composerJSON := filepath.Join(buildDir, "composer.json")
				content := `{
					"require": {
						"php": "9.0.0"
					}
				}`
				err := os.WriteFile(composerJSON, []byte(content), 0644)
				Expect(err).NotTo(HaveOccurred())

				ext.ShouldCompile(ctx)
			})

			It("should fall back to default PHP version", func() {
				err := ext.Configure(ctx)
				Expect(err).NotTo(HaveOccurred())

				phpVersion := ctx.GetString("PHP_VERSION")
				Expect(phpVersion).To(Equal("8.1.32")) // PHP_DEFAULT
			})
		})

		// Regression test for https://github.com/cloudfoundry/php-buildpack/issues/1220
		// composer.json requires ^8.3, but composer.lock packages carry stale upper-bound
		// constraints (e.g. <8.3.0) written before PHP 8.3 was released. The buildpack must
		// not re-evaluate those package-level constraints — Composer already resolved them
		// when it wrote the lock file. Only the top-level require.php in composer.json matters.
		Context("when composer.json requires ^8.3 and composer.lock has packages with stale <8.3.0 constraints (issue #1220)", func() {
			BeforeEach(func() {
				composerJSON := filepath.Join(buildDir, "composer.json")
				jsonContent := `{
					"require": {
						"php": "^8.3"
					}
				}`
				err := os.WriteFile(composerJSON, []byte(jsonContent), 0644)
				Expect(err).NotTo(HaveOccurred())

				// Simulate a real-world lock file: 84 packages, many with conservative
				// upper-bound PHP constraints written before PHP 8.3 was released.
				composerLock := filepath.Join(buildDir, "composer.lock")
				lockContent := `{
					"packages": [
						{"name": "pkg/a", "version": "1.0.0", "require": {"php": ">=7.2.5 <8.3.0"}},
						{"name": "pkg/b", "version": "2.0.0", "require": {"php": ">=7.4 <8.3.0"}},
						{"name": "pkg/c", "version": "3.0.0", "require": {"php": ">=8.0 <8.3.0"}},
						{"name": "pkg/d", "version": "1.5.0", "require": {"php": "^7.2 || ^8.0"}},
						{"name": "pkg/e", "version": "1.0.0", "require": {"php": ">=8.1"}},
						{"name": "pkg/f", "version": "1.0.0", "require": {"php": ">=7.2.5 <8.3.0"}},
						{"name": "pkg/g", "version": "1.0.0", "require": {"php": ">=7.2.5 <8.3.0"}},
						{"name": "pkg/h", "version": "1.0.0", "require": {"php": ">=7.2.5 <8.3.0"}},
						{"name": "pkg/i", "version": "1.0.0", "require": {"php": ">=7.2.5 <8.3.0"}},
						{"name": "pkg/j", "version": "1.0.0", "require": {"php": ">=7.2.5 <8.3.0"}}
					]
				}`
				err = os.WriteFile(composerLock, []byte(lockContent), 0644)
				Expect(err).NotTo(HaveOccurred())

				ext.ShouldCompile(ctx)
			})

			It("should select 8.3.x, ignoring stale package constraints in composer.lock", func() {
				err := ext.Configure(ctx)
				Expect(err).NotTo(HaveOccurred())

				phpVersion := ctx.GetString("PHP_VERSION")
				// Must NOT fall back to default 8.1.32 — that is the regression.
				// Must select the highest 8.3.x version available.
				Expect(phpVersion).To(Equal("8.3.21"))
			})
		})
	})

	Describe("Configure - Edge Cases", func() {
		Context("when ALL_PHP_VERSIONS is not set", func() {
			BeforeEach(func() {
				ctx.Set("ALL_PHP_VERSIONS", "") // Clear it

				composerJSON := filepath.Join(buildDir, "composer.json")
				content := `{
					"require": {
						"php": ">=7.4"
					}
				}`
				err := os.WriteFile(composerJSON, []byte(content), 0644)
				Expect(err).NotTo(HaveOccurred())

				ext.ShouldCompile(ctx)
			})

			It("should fall back to PHP_DEFAULT", func() {
				err := ext.Configure(ctx)
				Expect(err).NotTo(HaveOccurred())

				phpVersion := ctx.GetString("PHP_VERSION")
				Expect(phpVersion).To(Equal("8.1.32"))
			})
		})

		Context("when composer.json has invalid JSON", func() {
			BeforeEach(func() {
				composerJSON := filepath.Join(buildDir, "composer.json")
				err := os.WriteFile(composerJSON, []byte(`{invalid json`), 0644)
				Expect(err).NotTo(HaveOccurred())

				ext.ShouldCompile(ctx)
			})

			It("should return error", func() {
				err := ext.Configure(ctx)
				Expect(err).To(HaveOccurred())
				Expect(err.Error()).To(ContainSubstring("JSON"))
			})
		})

		Context("when composer.json has no PHP requirement", func() {
			BeforeEach(func() {
				composerJSON := filepath.Join(buildDir, "composer.json")
				content := `{
					"name": "test/app",
					"require": {
						"vendor/package": "^1.0"
					}
				}`
				err := os.WriteFile(composerJSON, []byte(content), 0644)
				Expect(err).NotTo(HaveOccurred())

				ext.ShouldCompile(ctx)
			})

			It("should not set PHP_VERSION (use existing)", func() {
				// Set a version before Configure
				ctx.Set("PHP_VERSION", "8.2.26")

				err := ext.Configure(ctx)
				Expect(err).NotTo(HaveOccurred())

				// Should not change the version
				phpVersion := ctx.GetString("PHP_VERSION")
				Expect(phpVersion).To(Equal("8.2.26"))
			})
		})
	})

	Describe("PreprocessCommands", func() {
		It("should return nil (no preprocess commands)", func() {
			commands, err := ext.PreprocessCommands(ctx)
			Expect(err).NotTo(HaveOccurred())
			Expect(commands).To(BeNil())
		})
	})

	Describe("ServiceCommands", func() {
		It("should return nil (no service commands)", func() {
			commands, err := ext.ServiceCommands(ctx)
			Expect(err).NotTo(HaveOccurred())
			Expect(commands).To(BeNil())
		})
	})

	Describe("ServiceEnvironment", func() {
		It("should return nil (no service environment)", func() {
			env, err := ext.ServiceEnvironment(ctx)
			Expect(err).NotTo(HaveOccurred())
			Expect(env).To(BeNil())
		})
	})
})
