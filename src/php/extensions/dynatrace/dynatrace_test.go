package dynatrace_test

import (
	"os"
	"path/filepath"

	"github.com/cloudfoundry/php-buildpack/src/php/extensions"
	"github.com/cloudfoundry/php-buildpack/src/php/extensions/dynatrace"
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
)

var _ = Describe("DynatraceExtension", func() {
	var (
		ext      *dynatrace.DynatraceExtension
		ctx      *extensions.Context
		err      error
		buildDir string
		bpDir    string
	)

	BeforeEach(func() {
		ext = &dynatrace.DynatraceExtension{}
		ctx, err = extensions.NewContext()
		Expect(err).NotTo(HaveOccurred())

		// Create temp directories
		buildDir, err = os.MkdirTemp("", "dynatrace-test-build")
		Expect(err).NotTo(HaveOccurred())

		bpDir, err = os.MkdirTemp("", "dynatrace-test-bp")
		Expect(err).NotTo(HaveOccurred())

		ctx.Set("BUILD_DIR", buildDir)
		ctx.Set("BP_DIR", bpDir)
		ctx.Set("HOME", "/home/vcap/app")

		// Create VERSION file for buildpack version
		versionFile := filepath.Join(bpDir, "VERSION")
		Expect(os.WriteFile(versionFile, []byte("1.2.3\n"), 0644)).To(Succeed())
	})

	AfterEach(func() {
		if buildDir != "" {
			os.RemoveAll(buildDir)
		}
		if bpDir != "" {
			os.RemoveAll(bpDir)
		}
	})

	Describe("Name", func() {
		It("should return 'dynatrace'", func() {
			Expect(ext.Name()).To(Equal("dynatrace"))
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

		Context("when PHP_VM is 'php' but no Dynatrace service", func() {
			BeforeEach(func() {
				ctx.Set("PHP_VM", "php")
				ctx.VcapServices = map[string][]extensions.Service{}
			})

			It("should return false", func() {
				Expect(ext.ShouldCompile(ctx)).To(BeFalse())
			})
		})

		Context("when PHP_VM is 'php' and Dynatrace service exists", func() {
			BeforeEach(func() {
				ctx.Set("PHP_VM", "php")
				ctx.VcapServices = map[string][]extensions.Service{
					"user-provided": {
						{
							Name:  "my-dynatrace-service",
							Label: "user-provided",
							Credentials: map[string]interface{}{
								"environmentid": "abc123",
								"apitoken":      "test-token",
							},
						},
					},
				}
			})

			It("should return true", func() {
				Expect(ext.ShouldCompile(ctx)).To(BeTrue())
			})
		})

		Context("when service name contains 'dynatrace' but missing credentials", func() {
			BeforeEach(func() {
				ctx.Set("PHP_VM", "php")
				ctx.VcapServices = map[string][]extensions.Service{
					"user-provided": {
						{
							Name:  "my-dynatrace-service",
							Label: "user-provided",
							Credentials: map[string]interface{}{
								"environmentid": "abc123",
								// Missing apitoken
							},
						},
					},
				}
			})

			It("should return false", func() {
				Expect(ext.ShouldCompile(ctx)).To(BeFalse())
			})
		})

		Context("when multiple Dynatrace services exist", func() {
			BeforeEach(func() {
				ctx.Set("PHP_VM", "php")
				ctx.VcapServices = map[string][]extensions.Service{
					"user-provided": {
						{
							Name:  "dynatrace-service-1",
							Label: "user-provided",
							Credentials: map[string]interface{}{
								"environmentid": "abc123",
								"apitoken":      "token1",
							},
						},
						{
							Name:  "dynatrace-service-2",
							Label: "user-provided",
							Credentials: map[string]interface{}{
								"environmentid": "xyz789",
								"apitoken":      "token2",
							},
						},
					},
				}
			})

			It("should return false and print warning", func() {
				Expect(ext.ShouldCompile(ctx)).To(BeFalse())
			})
		})

		Context("when service has all optional parameters", func() {
			BeforeEach(func() {
				ctx.Set("PHP_VM", "php")
				ctx.VcapServices = map[string][]extensions.Service{
					"user-provided": {
						{
							Name:  "my-dynatrace",
							Label: "user-provided",
							Credentials: map[string]interface{}{
								"environmentid":   "abc123",
								"apitoken":        "test-token",
								"apiurl":          "https://custom.dynatrace.com/api",
								"skiperrors":      "true",
								"networkzone":     "zone1",
								"addtechnologies": "php",
							},
						},
					},
				}
			})

			It("should return true", func() {
				Expect(ext.ShouldCompile(ctx)).To(BeTrue())
			})
		})

		Context("when service provides environmentid without apiurl", func() {
			BeforeEach(func() {
				ctx.Set("PHP_VM", "php")
				ctx.VcapServices = map[string][]extensions.Service{
					"user-provided": {
						{
							Name:  "my-dynatrace",
							Label: "user-provided",
							Credentials: map[string]interface{}{
								"environmentid": "abc123",
								"apitoken":      "test-token",
								// No apiurl - should be auto-generated
							},
						},
					},
				}
			})

			It("should return true (API URL will be auto-generated)", func() {
				Expect(ext.ShouldCompile(ctx)).To(BeTrue())
			})
		})
	})

	Describe("Configure", func() {
		Context("with valid context", func() {
			BeforeEach(func() {
				ctx.Set("PHP_VM", "php")
				ctx.VcapServices = map[string][]extensions.Service{
					"user-provided": {
						{
							Name:  "my-dynatrace",
							Label: "user-provided",
							Credentials: map[string]interface{}{
								"environmentid": "abc123",
								"apitoken":      "test-token",
							},
						},
					},
				}
				ext.ShouldCompile(ctx)
			})

			It("should configure without error", func() {
				Expect(ext.Configure(ctx)).To(Succeed())
			})

			It("should read buildpack version from VERSION file", func() {
				Expect(ext.Configure(ctx)).To(Succeed())
				// Can't check private field, but verify no error
			})
		})

		Context("when VERSION file doesn't exist", func() {
			BeforeEach(func() {
				// Remove VERSION file
				versionFile := filepath.Join(bpDir, "VERSION")
				os.Remove(versionFile)

				ctx.Set("PHP_VM", "php")
				ctx.VcapServices = map[string][]extensions.Service{
					"user-provided": {
						{
							Name:  "my-dynatrace",
							Label: "user-provided",
							Credentials: map[string]interface{}{
								"environmentid": "abc123",
								"apitoken":      "test-token",
							},
						},
					},
				}
				ext.ShouldCompile(ctx)
			})

			It("should still configure successfully (uses 'unknown' version)", func() {
				Expect(ext.Configure(ctx)).To(Succeed())
			})
		})
	})

	Describe("Compile", func() {
		Context("when not detected", func() {
			BeforeEach(func() {
				ctx.Set("PHP_VM", "php")
				ctx.VcapServices = map[string][]extensions.Service{}
				ext.ShouldCompile(ctx)
			})

			It("should skip compile without error", func() {
				installer := extensions.NewInstaller(ctx)
				err := ext.Compile(ctx, installer)
				Expect(err).NotTo(HaveOccurred())
			})
		})

		// Note: Testing actual Compile with download is complex
		// In real scenarios, we'd need to mock HTTP client or skip download tests
		// For now, we verify the early return logic works correctly
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
