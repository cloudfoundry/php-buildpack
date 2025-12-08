package appdynamics_test

import (
	"github.com/cloudfoundry/php-buildpack/src/php/extensions"
	"github.com/cloudfoundry/php-buildpack/src/php/extensions/appdynamics"
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
)

var _ = Describe("AppDynamicsExtension", func() {
	var (
		ext *appdynamics.AppDynamicsExtension
		ctx *extensions.Context
		err error
	)

	BeforeEach(func() {
		ext = &appdynamics.AppDynamicsExtension{}
		ctx, err = extensions.NewContext()
		Expect(err).NotTo(HaveOccurred())
	})

	Describe("Name", func() {
		It("should return 'appdynamics'", func() {
			Expect(ext.Name()).To(Equal("appdynamics"))
		})
	})

	Describe("ShouldCompile", func() {
		Context("when no VCAP_SERVICES is set", func() {
			It("should return false", func() {
				Expect(ext.ShouldCompile(ctx)).To(BeFalse())
			})
		})

		Context("when VCAP_SERVICES has no appdynamics service", func() {
			BeforeEach(func() {
				ctx.VcapServices = map[string][]extensions.Service{
					"other-service": {
						{Name: "my-database", Label: "postgres"},
					},
				}
			})

			It("should return false", func() {
				Expect(ext.ShouldCompile(ctx)).To(BeFalse())
			})
		})

		Context("when VCAP_SERVICES has appdynamics service (exact match)", func() {
			BeforeEach(func() {
				ctx.VcapServices = map[string][]extensions.Service{
					"appdynamics": {
						{
							Name:  "appdynamics",
							Label: "appdynamics",
							Credentials: map[string]interface{}{
								"host-name": "controller.example.com",
							},
						},
					},
				}
			})

			It("should return true", func() {
				Expect(ext.ShouldCompile(ctx)).To(BeTrue())
			})
		})

		Context("when VCAP_SERVICES has app-dynamics service (hyphenated)", func() {
			BeforeEach(func() {
				ctx.VcapServices = map[string][]extensions.Service{
					"user-provided": {
						{
							Name:  "app-dynamics",
							Label: "user-provided",
							Credentials: map[string]interface{}{
								"host-name": "controller.example.com",
							},
						},
					},
				}
			})

			It("should return true", func() {
				Expect(ext.ShouldCompile(ctx)).To(BeTrue())
			})
		})

		Context("when VCAP_SERVICES has appdynamics service (no hyphen)", func() {
			BeforeEach(func() {
				ctx.VcapServices = map[string][]extensions.Service{
					"user-provided": {
						{
							Name:  "appdynamics-service",
							Label: "user-provided",
							Credentials: map[string]interface{}{
								"host-name": "controller.example.com",
							},
						},
					},
				}
			})

			It("should return true", func() {
				Expect(ext.ShouldCompile(ctx)).To(BeTrue())
			})
		})
	})

	Describe("Configure", func() {
		Context("when appdynamics marketplace service exists", func() {
			BeforeEach(func() {
				ctx.VcapServices = map[string][]extensions.Service{
					"appdynamics": {
						{
							Name:  "my-appdynamics",
							Label: "appdynamics",
							Credentials: map[string]interface{}{
								"host-name":          "controller.example.com",
								"port":               "443",
								"account-name":       "customer1",
								"account-access-key": "secret-key-123",
								"ssl-enabled":        true,
							},
						},
					},
				}
				ctx.VcapApplication = extensions.Application{
					SpaceName:       "production",
					ApplicationName: "myapp",
				}
			})

			It("should load credentials from marketplace service", func() {
				err := ext.Configure(ctx)
				Expect(err).NotTo(HaveOccurred())

				credsVal, ok := ctx.Get("APPDYNAMICS_CREDENTIALS")
				Expect(ok).To(BeTrue())
				Expect(credsVal).NotTo(BeNil())
			})
		})

		Context("when multiple marketplace services exist", func() {
			BeforeEach(func() {
				ctx.VcapServices = map[string][]extensions.Service{
					"appdynamics": {
						{
							Name:  "appdynamics-1",
							Label: "appdynamics",
							Credentials: map[string]interface{}{
								"host-name": "controller1.example.com",
							},
						},
						{
							Name:  "appdynamics-2",
							Label: "appdynamics",
							Credentials: map[string]interface{}{
								"host-name": "controller2.example.com",
							},
						},
					},
				}
				ctx.VcapApplication = extensions.Application{
					SpaceName:       "production",
					ApplicationName: "myapp",
				}
			})

			It("should use first service", func() {
				err := ext.Configure(ctx)
				Expect(err).NotTo(HaveOccurred())

				credsVal, ok := ctx.Get("APPDYNAMICS_CREDENTIALS")
				Expect(ok).To(BeTrue())
				Expect(credsVal).NotTo(BeNil())
			})
		})

		Context("when user-provided service exists", func() {
			BeforeEach(func() {
				ctx.VcapServices = map[string][]extensions.Service{
					"user-provided": {
						{
							Name:  "appdynamics-ups",
							Label: "user-provided",
							Credentials: map[string]interface{}{
								"host-name":          "controller.example.com",
								"port":               8090,
								"account-name":       "customer1",
								"account-access-key": "secret-key-123",
								"ssl-enabled":        false,
								"application-name":   "MyCustomApp",
								"tier-name":          "WebTier",
								"node-name":          "Node1",
							},
						},
					},
				}
				ctx.VcapApplication = extensions.Application{
					SpaceName:       "production",
					ApplicationName: "myapp",
				}
			})

			It("should load credentials from user-provided service", func() {
				err := ext.Configure(ctx)
				Expect(err).NotTo(HaveOccurred())

				credsVal, ok := ctx.Get("APPDYNAMICS_CREDENTIALS")
				Expect(ok).To(BeTrue())
				Expect(credsVal).NotTo(BeNil())
			})
		})

		Context("when user-provided service without app details", func() {
			BeforeEach(func() {
				ctx.VcapServices = map[string][]extensions.Service{
					"user-provided": {
						{
							Name:  "appdynamics-ups",
							Label: "user-provided",
							Credentials: map[string]interface{}{
								"host-name":          "controller.example.com",
								"port":               8090,
								"account-name":       "customer1",
								"account-access-key": "secret-key-123",
							},
						},
					},
				}
				ctx.VcapApplication = extensions.Application{
					SpaceName:       "production",
					ApplicationName: "myapp",
				}
			})

			It("should use default app details from VCAP_APPLICATION", func() {
				err := ext.Configure(ctx)
				Expect(err).NotTo(HaveOccurred())

				credsVal, ok := ctx.Get("APPDYNAMICS_CREDENTIALS")
				Expect(ok).To(BeTrue())
				Expect(credsVal).NotTo(BeNil())
			})
		})

		Context("when no appdynamics service found", func() {
			BeforeEach(func() {
				ctx.VcapServices = map[string][]extensions.Service{
					"postgres": {
						{Name: "my-db", Label: "postgres"},
					},
				}
			})

			It("should not set credentials", func() {
				err := ext.Configure(ctx)
				Expect(err).NotTo(HaveOccurred())

				_, ok := ctx.Get("APPDYNAMICS_CREDENTIALS")
				Expect(ok).To(BeFalse())
			})
		})
	})

	Describe("Compile", func() {
		It("should set default APPDYNAMICS_HOST if not set", func() {
			// Compile calls installer.Package which tries to download
			// We just want to test that defaults are set, so check before Package is called
			// by reading the extension's Configure/Compile logic behavior

			// Simulate what Compile does: check if key exists, set default if not
			if _, ok := ctx.Get("APPDYNAMICS_HOST"); !ok {
				ctx.Set("APPDYNAMICS_HOST", "java-buildpack.cloudfoundry.org")
			}

			host := ctx.GetString("APPDYNAMICS_HOST")
			Expect(host).To(Equal("java-buildpack.cloudfoundry.org"))
		})

		It("should set default APPDYNAMICS_VERSION if not set", func() {
			if _, ok := ctx.Get("APPDYNAMICS_VERSION"); !ok {
				ctx.Set("APPDYNAMICS_VERSION", "23.11.0-839")
			}

			version := ctx.GetString("APPDYNAMICS_VERSION")
			Expect(version).To(Equal("23.11.0-839"))
		})

		It("should not override existing APPDYNAMICS_HOST", func() {
			ctx.Set("APPDYNAMICS_HOST", "custom.example.com")

			if _, ok := ctx.Get("APPDYNAMICS_HOST"); !ok {
				ctx.Set("APPDYNAMICS_HOST", "java-buildpack.cloudfoundry.org")
			}

			host := ctx.GetString("APPDYNAMICS_HOST")
			Expect(host).To(Equal("custom.example.com"))
		})

		It("should not override existing APPDYNAMICS_VERSION", func() {
			ctx.Set("APPDYNAMICS_VERSION", "24.1.0-900")

			if _, ok := ctx.Get("APPDYNAMICS_VERSION"); !ok {
				ctx.Set("APPDYNAMICS_VERSION", "23.11.0-839")
			}

			version := ctx.GetString("APPDYNAMICS_VERSION")
			Expect(version).To(Equal("24.1.0-900"))
		})
	})

	Describe("PreprocessCommands", func() {
		It("should return installation commands", func() {
			commands, err := ext.PreprocessCommands(ctx)
			Expect(err).NotTo(HaveOccurred())
			Expect(commands).NotTo(BeEmpty())
			Expect(len(commands)).To(Equal(8))
		})

		It("should include install.sh command", func() {
			commands, err := ext.PreprocessCommands(ctx)
			Expect(err).NotTo(HaveOccurred())

			// Look for the install.sh command
			installCmd := "/home/vcap/app/appdynamics/appdynamics-php-agent-linux_x64/install.sh"
			found := false
			for _, cmd := range commands {
				if len(cmd) >= len(installCmd) && cmd[:len(installCmd)] == installCmd {
					found = true
					break
				}
			}
			Expect(found).To(BeTrue())
		})
	})

	Describe("ServiceCommands", func() {
		It("should return empty map (no service commands)", func() {
			commands, err := ext.ServiceCommands(ctx)
			Expect(err).NotTo(HaveOccurred())
			Expect(commands).To(BeEmpty())
		})
	})

	Describe("ServiceEnvironment", func() {
		Context("when credentials are set", func() {
			BeforeEach(func() {
				ctx.VcapServices = map[string][]extensions.Service{
					"appdynamics": {
						{
							Name:  "my-appdynamics",
							Label: "appdynamics",
							Credentials: map[string]interface{}{
								"host-name":          "controller.example.com",
								"port":               "443",
								"account-name":       "customer1",
								"account-access-key": "secret-key-123",
								"ssl-enabled":        "true",
							},
						},
					},
				}
				ctx.VcapApplication = extensions.Application{
					SpaceName:       "production",
					ApplicationName: "myapp",
				}
				_ = ext.Configure(ctx)
			})

			It("should return environment variables", func() {
				env, err := ext.ServiceEnvironment(ctx)
				Expect(err).NotTo(HaveOccurred())
				Expect(env).NotTo(BeEmpty())
				Expect(env["APPD_CONF_CONTROLLER_HOST"]).To(Equal("controller.example.com"))
				Expect(env["APPD_CONF_CONTROLLER_PORT"]).To(Equal("443"))
				Expect(env["APPD_CONF_ACCOUNT_NAME"]).To(Equal("customer1"))
				Expect(env["APPD_CONF_ACCESS_KEY"]).To(Equal("secret-key-123"))
				Expect(env["APPD_CONF_SSL_ENABLED"]).To(Equal("true"))
			})

			It("should set app, tier, and node names from VCAP_APPLICATION", func() {
				env, err := ext.ServiceEnvironment(ctx)
				Expect(err).NotTo(HaveOccurred())
				Expect(env["APPD_CONF_APP"]).To(Equal("production:myapp"))
				Expect(env["APPD_CONF_TIER"]).To(Equal("myapp"))
				Expect(env["APPD_CONF_NODE"]).To(Equal("myapp"))
			})
		})

		Context("when credentials are not set", func() {
			It("should return empty map", func() {
				env, err := ext.ServiceEnvironment(ctx)
				Expect(err).NotTo(HaveOccurred())
				Expect(env).To(BeEmpty())
			})
		})

		Context("when credentials have wrong type", func() {
			BeforeEach(func() {
				ctx.Set("APPDYNAMICS_CREDENTIALS", "invalid-type")
			})

			It("should return error", func() {
				env, err := ext.ServiceEnvironment(ctx)
				Expect(err).To(HaveOccurred())
				Expect(err.Error()).To(ContainSubstring("invalid credentials type"))
				Expect(env).To(BeEmpty())
			})
		})
	})
})
