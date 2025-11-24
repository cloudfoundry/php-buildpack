package sessions

import (
	"fmt"
	"strings"

	"github.com/cloudfoundry/php-buildpack/src/php/extensions"
)

// SessionsExtension configures Redis or Memcached for session sharing
type SessionsExtension struct{}

// Name returns the extension name
func (e *SessionsExtension) Name() string {
	return "sessions"
}

// BaseSetup is the interface for session store configurations
type BaseSetup interface {
	SessionStoreKey() string
	SessionSavePath() string
	ExtensionName() string
	CustomConfigPHPIni(phpIni *extensions.ConfigFileEditor)
}

// RedisSetup configures Redis for session storage
type RedisSetup struct {
	ctx         *extensions.Context
	credentials map[string]interface{}
}

const (
	redisDefaultTrigger     = "redis-sessions"
	redisCustomKeyName      = "REDIS_SESSION_STORE_SERVICE_NAME"
	memcachedDefaultTrigger = "memcached-sessions"
	memcachedCustomKeyName  = "MEMCACHED_SESSION_STORE_SERVICE_NAME"
)

// NewRedisSetup creates a new Redis setup
func NewRedisSetup(ctx *extensions.Context, credentials map[string]interface{}) *RedisSetup {
	return &RedisSetup{
		ctx:         ctx,
		credentials: credentials,
	}
}

// SessionStoreKey returns the service name key to look for
func (r *RedisSetup) SessionStoreKey() string {
	if customKey := r.ctx.GetString(redisCustomKeyName); customKey != "" {
		return customKey
	}
	return redisDefaultTrigger
}

// SessionSavePath returns the Redis session save path
func (r *RedisSetup) SessionSavePath() string {
	hostname := ""
	if h, ok := r.credentials["hostname"]; ok {
		hostname = fmt.Sprintf("%v", h)
	} else if h, ok := r.credentials["host"]; ok {
		hostname = fmt.Sprintf("%v", h)
	} else {
		hostname = "not-found"
	}

	port := "not-found"
	if p, ok := r.credentials["port"]; ok {
		port = fmt.Sprintf("%v", p)
	}

	password := ""
	if pw, ok := r.credentials["password"]; ok {
		password = fmt.Sprintf("%v", pw)
	}

	return fmt.Sprintf("tcp://%s:%s?auth=%s", hostname, port, password)
}

// ExtensionName returns the PHP extension name
func (r *RedisSetup) ExtensionName() string {
	return "redis"
}

// CustomConfigPHPIni adds custom PHP ini configuration (no-op for Redis)
func (r *RedisSetup) CustomConfigPHPIni(phpIni *extensions.ConfigFileEditor) {
	// Redis doesn't need custom config
}

// MemcachedSetup configures Memcached for session storage
type MemcachedSetup struct {
	ctx         *extensions.Context
	credentials map[string]interface{}
}

// NewMemcachedSetup creates a new Memcached setup
func NewMemcachedSetup(ctx *extensions.Context, credentials map[string]interface{}) *MemcachedSetup {
	return &MemcachedSetup{
		ctx:         ctx,
		credentials: credentials,
	}
}

// SessionStoreKey returns the service name key to look for
func (m *MemcachedSetup) SessionStoreKey() string {
	if customKey := m.ctx.GetString(memcachedCustomKeyName); customKey != "" {
		return customKey
	}
	return memcachedDefaultTrigger
}

// SessionSavePath returns the Memcached session save path
func (m *MemcachedSetup) SessionSavePath() string {
	servers := "not-found"
	if s, ok := m.credentials["servers"]; ok {
		servers = fmt.Sprintf("%v", s)
	}
	return fmt.Sprintf("PERSISTENT=app_sessions %s", servers)
}

// ExtensionName returns the PHP extension name
func (m *MemcachedSetup) ExtensionName() string {
	return "memcached"
}

// CustomConfigPHPIni adds custom PHP ini configuration for Memcached
func (m *MemcachedSetup) CustomConfigPHPIni(phpIni *extensions.ConfigFileEditor) {
	username := ""
	if u, ok := m.credentials["username"]; ok {
		username = fmt.Sprintf("%v", u)
	}

	password := ""
	if pw, ok := m.credentials["password"]; ok {
		password = fmt.Sprintf("%v", pw)
	}

	phpIni.AppendLines([]string{
		"memcached.sess_binary=On\n",
		"memcached.use_sasl=On\n",
		fmt.Sprintf("memcached.sess_sasl_username=%s\n", username),
		fmt.Sprintf("memcached.sess_sasl_password=%s\n", password),
	})
}

// sessionService holds the detected session service configuration
type sessionService struct {
	service BaseSetup
}

// ShouldCompile checks if the extension should be compiled
func (e *SessionsExtension) ShouldCompile(ctx *extensions.Context) bool {
	service := e.loadSession(ctx)
	return service != nil
}

// loadSession searches for a Redis or Memcached session service
func (e *SessionsExtension) loadSession(ctx *extensions.Context) BaseSetup {
	// Search for appropriately named session store in VCAP_SERVICES
	for _, services := range ctx.VcapServices {
		for _, service := range services {
			serviceName := service.Name

			// Try Redis
			redisSetup := NewRedisSetup(ctx, service.Credentials)
			if strings.Contains(serviceName, redisSetup.SessionStoreKey()) {
				return redisSetup
			}

			// Try Memcached
			memcachedSetup := NewMemcachedSetup(ctx, service.Credentials)
			if strings.Contains(serviceName, memcachedSetup.SessionStoreKey()) {
				return memcachedSetup
			}
		}
	}
	return nil
}

// Configure configures the extension
func (e *SessionsExtension) Configure(ctx *extensions.Context) error {
	service := e.loadSession(ctx)
	if service == nil {
		return nil
	}

	// Add the PHP extension that provides the session save handler
	phpExtensions := ctx.GetStringSlice("PHP_EXTENSIONS")
	if phpExtensions == nil {
		phpExtensions = make([]string, 0)
	}
	phpExtensions = append(phpExtensions, service.ExtensionName())
	ctx.Set("PHP_EXTENSIONS", phpExtensions)

	return nil
}

// Compile installs/compiles the extension payload
func (e *SessionsExtension) Compile(ctx *extensions.Context, installer *extensions.Installer) error {
	service := e.loadSession(ctx)
	if service == nil {
		return nil
	}

	// Load PHP configuration helper
	helper := extensions.NewPHPConfigHelper(ctx)
	if err := helper.LoadConfig(); err != nil {
		return fmt.Errorf("failed to load PHP config: %w", err)
	}

	phpIni := helper.PHPIni()

	// Modify php.ini to contain the right session config
	phpIni.UpdateLines(
		"^session\\.name = JSESSIONID$",
		"session.name = PHPSESSIONID")

	phpIni.UpdateLines(
		"^session\\.save_handler = files$",
		fmt.Sprintf("session.save_handler = %s", service.ExtensionName()))

	phpIni.UpdateLines(
		"^session\\.save_path = \"@{TMPDIR}\"$",
		fmt.Sprintf("session.save_path = \"%s\"", service.SessionSavePath()))

	// Apply custom configuration
	service.CustomConfigPHPIni(phpIni)

	// Save the modified php.ini
	if err := phpIni.Save(helper.PHPIniPath()); err != nil {
		return fmt.Errorf("failed to save php.ini: %w", err)
	}

	return nil
}

// PreprocessCommands returns commands to run before app starts
func (e *SessionsExtension) PreprocessCommands(ctx *extensions.Context) ([]string, error) {
	// Sessions extension doesn't need preprocess commands
	return []string{}, nil
}

// ServiceCommands returns long-running service commands
func (e *SessionsExtension) ServiceCommands(ctx *extensions.Context) (map[string]string, error) {
	// Sessions extension doesn't provide service commands
	return map[string]string{}, nil
}

// ServiceEnvironment returns environment variables for services
func (e *SessionsExtension) ServiceEnvironment(ctx *extensions.Context) (map[string]string, error) {
	// Sessions extension doesn't provide service environment
	return map[string]string{}, nil
}
