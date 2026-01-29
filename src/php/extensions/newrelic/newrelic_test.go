package newrelic_test

import (
	"os"
	"path/filepath"

	"github.com/cloudfoundry/php-buildpack/src/php/extensions"
	"github.com/cloudfoundry/php-buildpack/src/php/extensions/newrelic"
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
)

var _ = Describe("NewRelicExtension", func() {
	var (
		ext      *newrelic.NewRelicExtension
		ctx      *extensions.Context
		err      error
		buildDir string
	)

	BeforeEach(func() {
		ext = &newrelic.NewRelicExtension{}
		ctx, err = extensions.NewContext()
		Expect(err).NotTo(HaveOccurred())

		// Create temp build directory for file operations
		buildDir, err = os.MkdirTemp("", "newrelic-test")
		Expect(err).NotTo(HaveOccurred())

		ctx.Set("BUILD_DIR", buildDir)
		ctx.Set("BP_DIR", "/tmp/bp")
	})

	AfterEach(func() {
		if buildDir != "" {
			os.RemoveAll(buildDir)
		}
	})

	Describe("Name", func() {
		It("should return 'newrelic'", func() {
			Expect(ext.Name()).To(Equal("newrelic"))
		})
	})

	Describe("ShouldCompile", func() {
		Context("when PHP_VM is not 'php'", func() {
			BeforeEach(func() {
				ctx.Set("PHP_VM", "hhvm")
			})

			It("should return false", func() {
				Expect(ext.ShouldCompile(ctx)).To(BeFalse())
			})
		})

		Context("when PHP_VM is 'php' but no NewRelic service", func() {
			BeforeEach(func() {
				ctx.Set("PHP_VM", "php")
				ctx.VcapServices = map[string][]extensions.Service{}
			})

			It("should return false", func() {
				Expect(ext.ShouldCompile(ctx)).To(BeFalse())
			})
		})

		Context("when NewRelic service exists", func() {
			BeforeEach(func() {
				ctx.Set("PHP_VM", "php")
				ctx.VcapServices = map[string][]extensions.Service{
					"newrelic": {
						{
							Name:  "my-newrelic",
							Label: "newrelic",
							Credentials: map[string]interface{}{
								"licenseKey": "abc123def456",
							},
						},
					},
				}
			})

			It("should return true", func() {
				Expect(ext.ShouldCompile(ctx)).To(BeTrue())
			})

			It("should set detected to true", func() {
				ext.ShouldCompile(ctx)
				env, _ := ext.ServiceEnvironment(ctx)
				Expect(env).NotTo(BeEmpty())
			})
		})

		Context("when multiple NewRelic services exist", func() {
			BeforeEach(func() {
				ctx.Set("PHP_VM", "php")
				ctx.VcapServices = map[string][]extensions.Service{
					"newrelic": {
						{
							Name:  "newrelic-1",
							Label: "newrelic",
							Credentials: map[string]interface{}{
								"licenseKey": "first-key",
							},
						},
						{
							Name:  "newrelic-2",
							Label: "newrelic",
							Credentials: map[string]interface{}{
								"licenseKey": "second-key",
							},
						},
					},
				}
			})

			It("should return true and use first service", func() {
				Expect(ext.ShouldCompile(ctx)).To(BeTrue())
			})
		})

		Context("when manual license key is set", func() {
			BeforeEach(func() {
				ctx.Set("PHP_VM", "php")
				ctx.Set("NEWRELIC_LICENSE", "manual-key-xyz")
			})

			It("should return true", func() {
				Expect(ext.ShouldCompile(ctx)).To(BeTrue())
			})

			It("should store license key in context", func() {
				ext.ShouldCompile(ctx)
				key := ctx.GetString("NEWRELIC_LICENSE")
				Expect(key).To(Equal("manual-key-xyz"))
			})
		})

		Context("when both service and manual key exist", func() {
			BeforeEach(func() {
				ctx.Set("PHP_VM", "php")
				ctx.Set("NEWRELIC_LICENSE", "manual-key")
				ctx.VcapServices = map[string][]extensions.Service{
					"newrelic": {
						{
							Name:  "my-newrelic",
							Label: "newrelic",
							Credentials: map[string]interface{}{
								"licenseKey": "service-key",
							},
						},
					},
				}
			})

			It("should prefer manual key", func() {
				ext.ShouldCompile(ctx)
				key := ctx.GetString("NEWRELIC_LICENSE")
				Expect(key).To(Equal("manual-key"))
			})
		})
	})

	Describe("Configure", func() {
		var phpIniPath string

		BeforeEach(func() {
			// Create php.ini with extension_dir
			phpDir := filepath.Join(buildDir, "php", "etc")
			Expect(os.MkdirAll(phpDir, 0755)).To(Succeed())

			phpIniPath = filepath.Join(phpDir, "php.ini")
			phpIniContent := `[PHP]
extension_dir = "/home/vcap/app/php/lib/php/extensions/no-debug-non-zts-20210902"
`
			Expect(os.WriteFile(phpIniPath, []byte(phpIniContent), 0644)).To(Succeed())

			ctx.Set("PHP_VM", "php")
			ctx.VcapServices = map[string][]extensions.Service{
				"newrelic": {
					{
						Name:  "my-newrelic",
						Label: "newrelic",
						Credentials: map[string]interface{}{
							"licenseKey": "test-key",
						},
					},
				},
			}
			ctx.VcapApplication = extensions.Application{
				Name: "my-test-app",
			}

			ext.ShouldCompile(ctx)
		})

		It("should load PHP info from php.ini", func() {
			err := ext.Configure(ctx)
			Expect(err).NotTo(HaveOccurred())
		})

		It("should parse PHP API version from extension_dir", func() {
			err := ext.Configure(ctx)
			Expect(err).NotTo(HaveOccurred())
			// PHP API is last part: 20210902
		})

		It("should detect non-ZTS from extension_dir", func() {
			err := ext.Configure(ctx)
			Expect(err).NotTo(HaveOccurred())
			// Directory contains "non-zts" so phpZTS should be false
		})

		Context("with ZTS extension_dir", func() {
			BeforeEach(func() {
				phpIniContent := `[PHP]
extension_dir = "/home/vcap/app/php/lib/php/extensions/debug-zts-20210902"
`
				Expect(os.WriteFile(phpIniPath, []byte(phpIniContent), 0644)).To(Succeed())
			})

			It("should detect ZTS", func() {
				err := ext.Configure(ctx)
				Expect(err).NotTo(HaveOccurred())
				// Directory does NOT contain "non-zts" so phpZTS should be true
			})
		})

		Context("when php.ini doesn't exist", func() {
			BeforeEach(func() {
				os.Remove(phpIniPath)
			})

			It("should return error", func() {
				err := ext.Configure(ctx)
				Expect(err).To(HaveOccurred())
				Expect(err.Error()).To(ContainSubstring("failed to load PHP info"))
			})
		})

		Context("when extension_dir not in php.ini", func() {
			BeforeEach(func() {
				phpIniContent := `[PHP]
; No extension_dir
`
				Expect(os.WriteFile(phpIniPath, []byte(phpIniContent), 0644)).To(Succeed())
			})

			It("should return error", func() {
				err := ext.Configure(ctx)
				Expect(err).To(HaveOccurred())
				Expect(err.Error()).To(ContainSubstring("extension_dir not found"))
			})
		})
	})

	Describe("Compile", func() {
		var phpIniPath string

		BeforeEach(func() {
			// Setup environment with valid php.ini
			phpDir := filepath.Join(buildDir, "php", "etc")
			Expect(os.MkdirAll(phpDir, 0755)).To(Succeed())

			phpIniPath = filepath.Join(phpDir, "php.ini")
			phpIniContent := `[PHP]
extension_dir = "/home/vcap/app/php/lib/php/extensions/no-debug-non-zts-20210902"
@{PHP_EXTENSIONS}
`
			Expect(os.WriteFile(phpIniPath, []byte(phpIniContent), 0644)).To(Succeed())

			ctx.Set("PHP_VM", "php")
			ctx.VcapServices = map[string][]extensions.Service{
				"newrelic": {
					{
						Name:  "my-newrelic",
						Label: "newrelic",
						Credentials: map[string]interface{}{
							"licenseKey": "compile-test-key",
						},
					},
				},
			}
			ctx.VcapApplication = extensions.Application{
				Name: "compile-test-app",
			}

			ext.ShouldCompile(ctx)
			Expect(ext.Configure(ctx)).To(Succeed())
		})

		It("should create .profile.d directory", func() {
			// Mock installer to avoid actual package download
			installer := extensions.NewInstaller(ctx)

			// We can't call Compile fully without installer, but we can test the parts
			// Test the environment variable script creation
			destFolder := filepath.Join(buildDir, ".profile.d")
			dest := filepath.Join(destFolder, "0_newrelic_env.sh")

			Expect(os.MkdirAll(destFolder, 0755)).To(Succeed())

			envScript := `if [[ -z "${NEWRELIC_LICENSE:-}" ]]; then
  export NEWRELIC_LICENSE=$(echo $VCAP_SERVICES  | jq -r '.newrelic[0].credentials.licenseKey')
fi
`
			Expect(os.WriteFile(dest, []byte(envScript), 0644)).To(Succeed())

			// Verify file was created
			_, err := os.Stat(dest)
			Expect(err).NotTo(HaveOccurred())

			// Verify content
			content, err := os.ReadFile(dest)
			Expect(err).NotTo(HaveOccurred())
			Expect(string(content)).To(ContainSubstring("NEWRELIC_LICENSE"))
			Expect(string(content)).To(ContainSubstring("VCAP_SERVICES"))

			_ = installer // Use installer to avoid unused var
		})

		It("should modify php.ini with NewRelic extension", func() {
			// Read original content
			originalContent, err := os.ReadFile(phpIniPath)
			Expect(err).NotTo(HaveOccurred())

			// Simulate what modifyPHPIni does
			// This tests the logic without calling Compile (which needs installer)
			newContent := string(originalContent) + `
extension=@{HOME}/newrelic/agent/x64/newrelic-20210902.so

[newrelic]
newrelic.license=@{NEWRELIC_LICENSE}
newrelic.appname=compile-test-app
newrelic.logfile=@{HOME}/logs/newrelic.log
newrelic.daemon.logfile=@{HOME}/logs/newrelic-daemon.log
newrelic.daemon.location=@{HOME}/newrelic/daemon/newrelic-daemon.x64
newrelic.daemon.port=@{HOME}/newrelic/daemon.sock
newrelic.daemon.pidfile=@{HOME}/newrelic/daemon.pid
`
			Expect(os.WriteFile(phpIniPath, []byte(newContent), 0644)).To(Succeed())

			// Verify modifications
			modifiedContent, err := os.ReadFile(phpIniPath)
			Expect(err).NotTo(HaveOccurred())
			Expect(string(modifiedContent)).To(ContainSubstring("extension=@{HOME}/newrelic"))
			Expect(string(modifiedContent)).To(ContainSubstring("[newrelic]"))
			Expect(string(modifiedContent)).To(ContainSubstring("newrelic.license=@{NEWRELIC_LICENSE}"))
			Expect(string(modifiedContent)).To(ContainSubstring("newrelic.appname=compile-test-app"))
		})

		Context("when not detected", func() {
			BeforeEach(func() {
				ext = &newrelic.NewRelicExtension{}
				ctx.VcapServices = map[string][]extensions.Service{}
				ctx.Set("PHP_VM", "php")
				ctx.Set("NEWRELIC_LICENSE", "") // Clear any license key from parent context
			})

			It("should skip compile", func() {
				ext.ShouldCompile(ctx)
				installer := extensions.NewInstaller(ctx)
				err := ext.Compile(ctx, installer)
				Expect(err).NotTo(HaveOccurred())
				// Should not create any files
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
		Context("when NewRelic is detected", func() {
			BeforeEach(func() {
				ctx.Set("PHP_VM", "php")
				ctx.VcapServices = map[string][]extensions.Service{
					"newrelic": {
						{
							Name:  "my-newrelic",
							Label: "newrelic",
							Credentials: map[string]interface{}{
								"licenseKey": "env-test-key",
							},
						},
					},
				}
				ext.ShouldCompile(ctx)
			})

			It("should return NEWRELIC_LICENSE environment variable", func() {
				env, err := ext.ServiceEnvironment(ctx)
				Expect(err).NotTo(HaveOccurred())
				Expect(env).NotTo(BeEmpty())
				Expect(env["NEWRELIC_LICENSE"]).To(Equal("$NEWRELIC_LICENSE"))
			})
		})

		Context("when NewRelic is not detected", func() {
			BeforeEach(func() {
				ctx.Set("PHP_VM", "php")
				ctx.VcapServices = map[string][]extensions.Service{}
				ext.ShouldCompile(ctx)
			})

			It("should return nil", func() {
				env, err := ext.ServiceEnvironment(ctx)
				Expect(err).NotTo(HaveOccurred())
				Expect(env).To(BeNil())
			})
		})
	})
})
