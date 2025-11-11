package sessions_test

import (
	"os"
	"path/filepath"

	"github.com/cloudfoundry/php-buildpack/src/php/extensions"
	"github.com/cloudfoundry/php-buildpack/src/php/extensions/sessions"
	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("SessionsExtension", func() {
	var (
		ext      *sessions.SessionsExtension
		ctx      *extensions.Context
		err      error
		buildDir string
	)

	BeforeEach(func() {
		ext = &sessions.SessionsExtension{}
		ctx, err = extensions.NewContext()
		Expect(err).NotTo(HaveOccurred())

		// Create temp build directory for file operations
		buildDir, err = os.MkdirTemp("", "sessions-test")
		Expect(err).NotTo(HaveOccurred())

		// Set BuildDir directly on the struct field (not via Set() which uses Data map)
		ctx.BuildDir = buildDir
		ctx.Set("BP_DIR", "/tmp/bp")
	})

	AfterEach(func() {
		if buildDir != "" {
			os.RemoveAll(buildDir)
		}
	})

	Describe("Name", func() {
		It("should return 'sessions'", func() {
			Expect(ext.Name()).To(Equal("sessions"))
		})
	})

	Describe("ShouldCompile", func() {
		Context("when no session service is found", func() {
			It("should return false", func() {
				ctx.VcapServices = map[string][]extensions.Service{}
				Expect(ext.ShouldCompile(ctx)).To(BeFalse())
			})
		})

		Context("when redis-sessions service exists", func() {
			It("should return true", func() {
				ctx.VcapServices = map[string][]extensions.Service{
					"p-redis": {
						{
							Name: "my-redis-sessions",
							Credentials: map[string]interface{}{
								"hostname": "redis.example.com",
								"port":     6379,
								"password": "secret",
							},
						},
					},
				}
				Expect(ext.ShouldCompile(ctx)).To(BeTrue())
			})
		})

		Context("when memcached-sessions service exists", func() {
			It("should return true", func() {
				ctx.VcapServices = map[string][]extensions.Service{
					"p-memcached": {
						{
							Name: "my-memcached-sessions",
							Credentials: map[string]interface{}{
								"servers":  "memcached.example.com:11211",
								"username": "admin",
								"password": "secret",
							},
						},
					},
				}
				Expect(ext.ShouldCompile(ctx)).To(BeTrue())
			})
		})

		Context("when custom Redis service name is set", func() {
			It("should detect the custom name", func() {
				ctx.Set("REDIS_SESSION_STORE_SERVICE_NAME", "custom-redis")
				ctx.VcapServices = map[string][]extensions.Service{
					"redis": {
						{
							Name: "my-custom-redis-service",
							Credentials: map[string]interface{}{
								"hostname": "redis.example.com",
								"port":     6379,
							},
						},
					},
				}
				Expect(ext.ShouldCompile(ctx)).To(BeTrue())
			})
		})

		Context("when custom Memcached service name is set", func() {
			It("should detect the custom name", func() {
				ctx.Set("MEMCACHED_SESSION_STORE_SERVICE_NAME", "custom-memcached")
				ctx.VcapServices = map[string][]extensions.Service{
					"memcached": {
						{
							Name: "my-custom-memcached-service",
							Credentials: map[string]interface{}{
								"servers": "memcached.example.com:11211",
							},
						},
					},
				}
				Expect(ext.ShouldCompile(ctx)).To(BeTrue())
			})
		})

		Context("when service name doesn't match", func() {
			It("should return false", func() {
				ctx.VcapServices = map[string][]extensions.Service{
					"redis": {
						{
							Name: "regular-redis",
							Credentials: map[string]interface{}{
								"hostname": "redis.example.com",
							},
						},
					},
				}
				Expect(ext.ShouldCompile(ctx)).To(BeFalse())
			})
		})
	})

	Describe("Configure", func() {
		Context("when no session service is found", func() {
			It("should return nil without error", func() {
				ctx.VcapServices = map[string][]extensions.Service{}
				err := ext.Configure(ctx)
				Expect(err).NotTo(HaveOccurred())
			})
		})

		Context("when Redis session service is found", func() {
			BeforeEach(func() {
				ctx.VcapServices = map[string][]extensions.Service{
					"redis": {
						{
							Name: "my-redis-sessions",
							Credentials: map[string]interface{}{
								"hostname": "redis.example.com",
								"port":     6379,
							},
						},
					},
				}
			})

			It("should add 'redis' to PHP_EXTENSIONS", func() {
				err := ext.Configure(ctx)
				Expect(err).NotTo(HaveOccurred())

				phpExtensions := ctx.GetStringSlice("PHP_EXTENSIONS")
				Expect(phpExtensions).To(ContainElement("redis"))
			})

			It("should preserve existing PHP_EXTENSIONS", func() {
				ctx.Set("PHP_EXTENSIONS", []string{"bz2", "zlib"})

				err := ext.Configure(ctx)
				Expect(err).NotTo(HaveOccurred())

				phpExtensions := ctx.GetStringSlice("PHP_EXTENSIONS")
				Expect(phpExtensions).To(ContainElement("bz2"))
				Expect(phpExtensions).To(ContainElement("zlib"))
				Expect(phpExtensions).To(ContainElement("redis"))
			})
		})

		Context("when Memcached session service is found", func() {
			BeforeEach(func() {
				ctx.VcapServices = map[string][]extensions.Service{
					"memcached": {
						{
							Name: "my-memcached-sessions",
							Credentials: map[string]interface{}{
								"servers": "memcached.example.com:11211",
							},
						},
					},
				}
			})

			It("should add 'memcached' to PHP_EXTENSIONS", func() {
				err := ext.Configure(ctx)
				Expect(err).NotTo(HaveOccurred())

				phpExtensions := ctx.GetStringSlice("PHP_EXTENSIONS")
				Expect(phpExtensions).To(ContainElement("memcached"))
			})
		})
	})

	Describe("Compile", func() {
		var phpDir string

		BeforeEach(func() {
			phpDir = filepath.Join(buildDir, "php")
			err := os.MkdirAll(filepath.Join(phpDir, "etc"), 0755)
			Expect(err).NotTo(HaveOccurred())

			// Create a basic php.ini file with session config
			phpIniContent := `session.name = JSESSIONID
session.save_handler = files
session.save_path = "@{TMPDIR}"
`
			phpIniPath := filepath.Join(phpDir, "etc", "php.ini")
			err = os.WriteFile(phpIniPath, []byte(phpIniContent), 0644)
			Expect(err).NotTo(HaveOccurred())

			// Create a basic php-fpm.conf file (required by PHPConfigHelper)
			phpFpmContent := `[global]
pid = @{HOME}/php/etc/php-fpm.pid
error_log = @{HOME}/php/var/log/php-fpm.log
`
			phpFpmPath := filepath.Join(phpDir, "etc", "php-fpm.conf")
			err = os.WriteFile(phpFpmPath, []byte(phpFpmContent), 0644)
			Expect(err).NotTo(HaveOccurred())

			ctx.Set("PHP_DIR", phpDir)
		})

		Context("when no session service is found", func() {
			It("should return nil without error", func() {
				ctx.VcapServices = map[string][]extensions.Service{}
				err := ext.Compile(ctx, nil)
				Expect(err).NotTo(HaveOccurred())
			})
		})

		Context("when Redis session service is found", func() {
			BeforeEach(func() {
				ctx.VcapServices = map[string][]extensions.Service{
					"redis": {
						{
							Name: "my-redis-sessions",
							Credentials: map[string]interface{}{
								"hostname": "redis.example.com",
								"port":     6379,
								"password": "mysecret",
							},
						},
					},
				}
			})

			It("should modify php.ini with Redis configuration", func() {
				err := ext.Compile(ctx, nil)
				Expect(err).NotTo(HaveOccurred())

				phpIniPath := filepath.Join(phpDir, "etc", "php.ini")
				content, err := os.ReadFile(phpIniPath)
				Expect(err).NotTo(HaveOccurred())

				contentStr := string(content)
				Expect(contentStr).To(ContainSubstring("session.name = PHPSESSIONID"))
				Expect(contentStr).To(ContainSubstring("session.save_handler = redis"))
				Expect(contentStr).To(ContainSubstring("tcp://redis.example.com:6379?auth=mysecret"))
			})

			It("should handle missing password gracefully", func() {
				ctx.VcapServices = map[string][]extensions.Service{
					"redis": {
						{
							Name: "my-redis-sessions",
							Credentials: map[string]interface{}{
								"hostname": "redis.example.com",
								"port":     6379,
							},
						},
					},
				}

				err := ext.Compile(ctx, nil)
				Expect(err).NotTo(HaveOccurred())

				phpIniPath := filepath.Join(phpDir, "etc", "php.ini")
				content, err := os.ReadFile(phpIniPath)
				Expect(err).NotTo(HaveOccurred())

				contentStr := string(content)
				Expect(contentStr).To(ContainSubstring("tcp://redis.example.com:6379?auth="))
			})

			It("should handle 'host' field instead of 'hostname'", func() {
				ctx.VcapServices = map[string][]extensions.Service{
					"redis": {
						{
							Name: "my-redis-sessions",
							Credentials: map[string]interface{}{
								"host": "redis2.example.com",
								"port": 6380,
							},
						},
					},
				}

				err := ext.Compile(ctx, nil)
				Expect(err).NotTo(HaveOccurred())

				phpIniPath := filepath.Join(phpDir, "etc", "php.ini")
				content, err := os.ReadFile(phpIniPath)
				Expect(err).NotTo(HaveOccurred())

				contentStr := string(content)
				Expect(contentStr).To(ContainSubstring("tcp://redis2.example.com:6380"))
			})
		})

		Context("when Memcached session service is found", func() {
			BeforeEach(func() {
				ctx.VcapServices = map[string][]extensions.Service{
					"memcached": {
						{
							Name: "my-memcached-sessions",
							Credentials: map[string]interface{}{
								"servers":  "memcached.example.com:11211",
								"username": "admin",
								"password": "mysecret",
							},
						},
					},
				}
			})

			It("should modify php.ini with Memcached configuration", func() {
				err := ext.Compile(ctx, nil)
				Expect(err).NotTo(HaveOccurred())

				phpIniPath := filepath.Join(phpDir, "etc", "php.ini")
				content, err := os.ReadFile(phpIniPath)
				Expect(err).NotTo(HaveOccurred())

				contentStr := string(content)
				Expect(contentStr).To(ContainSubstring("session.name = PHPSESSIONID"))
				Expect(contentStr).To(ContainSubstring("session.save_handler = memcached"))
				Expect(contentStr).To(ContainSubstring("PERSISTENT=app_sessions memcached.example.com:11211"))
				Expect(contentStr).To(ContainSubstring("memcached.sess_binary=On"))
				Expect(contentStr).To(ContainSubstring("memcached.use_sasl=On"))
				Expect(contentStr).To(ContainSubstring("memcached.sess_sasl_username=admin"))
				Expect(contentStr).To(ContainSubstring("memcached.sess_sasl_password=mysecret"))
			})

			It("should handle missing credentials gracefully", func() {
				ctx.VcapServices = map[string][]extensions.Service{
					"memcached": {
						{
							Name: "my-memcached-sessions",
							Credentials: map[string]interface{}{
								"servers": "memcached.example.com:11211",
							},
						},
					},
				}

				err := ext.Compile(ctx, nil)
				Expect(err).NotTo(HaveOccurred())

				phpIniPath := filepath.Join(phpDir, "etc", "php.ini")
				content, err := os.ReadFile(phpIniPath)
				Expect(err).NotTo(HaveOccurred())

				contentStr := string(content)
				Expect(contentStr).To(ContainSubstring("memcached.sess_sasl_username="))
				Expect(contentStr).To(ContainSubstring("memcached.sess_sasl_password="))
			})
		})
	})

	Describe("PreprocessCommands", func() {
		It("should return empty array", func() {
			cmds, err := ext.PreprocessCommands(ctx)
			Expect(err).NotTo(HaveOccurred())
			Expect(cmds).To(Equal([]string{}))
		})
	})

	Describe("ServiceCommands", func() {
		It("should return empty map", func() {
			cmds, err := ext.ServiceCommands(ctx)
			Expect(err).NotTo(HaveOccurred())
			Expect(cmds).To(Equal(map[string]string{}))
		})
	})

	Describe("ServiceEnvironment", func() {
		It("should return empty map", func() {
			env, err := ext.ServiceEnvironment(ctx)
			Expect(err).NotTo(HaveOccurred())
			Expect(env).To(Equal(map[string]string{}))
		})
	})
})
