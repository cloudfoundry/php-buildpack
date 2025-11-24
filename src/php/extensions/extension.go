package extensions

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"

	"github.com/cloudfoundry/libbuildpack"
)

// Extension defines the interface that all buildpack extensions must implement.
// This is the Go equivalent of Python's ExtensionHelper class.
type Extension interface {
	// Name returns the unique name of the extension
	Name() string

	// ShouldCompile determines if the extension should install its payload
	ShouldCompile(ctx *Context) bool

	// Configure configures the extension (called early in build)
	Configure(ctx *Context) error

	// Compile installs/compiles the extension payload
	Compile(ctx *Context, installer *Installer) error

	// PreprocessCommands returns list of commands to run once before app starts
	PreprocessCommands(ctx *Context) ([]string, error)

	// ServiceCommands returns map of long-running service commands (name -> command)
	ServiceCommands(ctx *Context) (map[string]string, error)

	// ServiceEnvironment returns map of environment variables for services
	ServiceEnvironment(ctx *Context) (map[string]string, error)
}

// Context contains the buildpack context (environment, paths, VCAP data, etc.)
// This is the Go equivalent of Python's ctx dict.
type Context struct {
	// Core directories
	BuildDir string
	CacheDir string
	DepsDir  string
	DepsIdx  string
	BPDir    string // Buildpack directory

	// Environment
	Env map[string]string

	// Cloud Foundry VCAP data
	VcapServices    map[string][]Service
	VcapApplication Application

	// Additional context data (configuration options, etc.)
	Data map[string]interface{}
}

// Service represents a Cloud Foundry bound service
type Service struct {
	Name        string                 `json:"name"`
	Label       string                 `json:"label"`
	Tags        []string               `json:"tags"`
	Plan        string                 `json:"plan"`
	Credentials map[string]interface{} `json:"credentials"`
}

// Application represents the Cloud Foundry application metadata
type Application struct {
	ApplicationID    string   `json:"application_id"`
	ApplicationName  string   `json:"application_name"`
	ApplicationURIs  []string `json:"application_uris"`
	Name             string   `json:"name"`
	SpaceName        string   `json:"space_name"`
	SpaceID          string   `json:"space_id"`
	OrganizationID   string   `json:"organization_id"`
	OrganizationName string   `json:"organization_name"`
}

// NewContext creates a new Context from the environment
func NewContext() (*Context, error) {
	ctx := &Context{
		BuildDir: os.Getenv("BUILD_DIR"),
		CacheDir: os.Getenv("CACHE_DIR"),
		DepsDir:  os.Getenv("DEPS_DIR"),
		DepsIdx:  os.Getenv("DEPS_IDX"),
		BPDir:    os.Getenv("BP_DIR"),
		Env:      make(map[string]string),
		Data:     make(map[string]interface{}),
	}

	// Parse VCAP_SERVICES
	if vcapServicesJSON := os.Getenv("VCAP_SERVICES"); vcapServicesJSON != "" {
		if err := json.Unmarshal([]byte(vcapServicesJSON), &ctx.VcapServices); err != nil {
			return nil, fmt.Errorf("failed to parse VCAP_SERVICES: %w", err)
		}
	} else {
		ctx.VcapServices = make(map[string][]Service)
	}

	// Parse VCAP_APPLICATION
	if vcapAppJSON := os.Getenv("VCAP_APPLICATION"); vcapAppJSON != "" {
		if err := json.Unmarshal([]byte(vcapAppJSON), &ctx.VcapApplication); err != nil {
			return nil, fmt.Errorf("failed to parse VCAP_APPLICATION: %w", err)
		}
	}

	// Copy environment variables
	for _, env := range os.Environ() {
		ctx.Env[env] = os.Getenv(env)
	}

	return ctx, nil
}

// Get retrieves a value from the context data
func (c *Context) Get(key string) (interface{}, bool) {
	val, ok := c.Data[key]
	return val, ok
}

// Set stores a value in the context data
func (c *Context) Set(key string, value interface{}) {
	c.Data[key] = value
}

// GetString retrieves a string value from the context data
func (c *Context) GetString(key string) string {
	if val, ok := c.Data[key]; ok {
		if str, ok := val.(string); ok {
			return str
		}
	}
	return ""
}

// GetStringSlice retrieves a string slice from the context data
func (c *Context) GetStringSlice(key string) []string {
	if val, ok := c.Data[key]; ok {
		if slice, ok := val.([]string); ok {
			return slice
		}
	}
	return nil
}

// FindServiceByName searches for a service by name
func (c *Context) FindServiceByName(name string) *Service {
	for _, services := range c.VcapServices {
		for i := range services {
			if services[i].Name == name {
				return &services[i]
			}
		}
	}
	return nil
}

// FindServicesByLabel searches for services by label
func (c *Context) FindServicesByLabel(label string) []Service {
	if services, ok := c.VcapServices[label]; ok {
		return services
	}
	return nil
}

// HasService checks if a service with the given name exists
func (c *Context) HasService(name string) bool {
	return c.FindServiceByName(name) != nil
}

// Installer provides methods for downloading and installing dependencies.
// This is the Go equivalent of Python's install object.
type Installer struct {
	ctx              *Context
	libbuildpackInst LibbuildpackInstaller
}

// LibbuildpackInstaller interface for libbuildpack dependency installation
type LibbuildpackInstaller interface {
	InstallDependency(dep libbuildpack.Dependency, outputDir string) error
	InstallOnlyVersion(depName, installDir string) error
}

// NewInstaller creates a new Installer
func NewInstaller(ctx *Context) *Installer {
	return &Installer{ctx: ctx, libbuildpackInst: nil}
}

// NewInstallerWithLibbuildpack creates an Installer with a libbuildpack installer
func NewInstallerWithLibbuildpack(ctx *Context, libbuildpackInst LibbuildpackInstaller) *Installer {
	return &Installer{ctx: ctx, libbuildpackInst: libbuildpackInst}
}

// InstallDependency installs a dependency using the libbuildpack installer
func (i *Installer) InstallDependency(dep libbuildpack.Dependency, outputDir string) error {
	if i.libbuildpackInst == nil {
		return fmt.Errorf("libbuildpack installer not available")
	}
	return i.libbuildpackInst.InstallDependency(dep, outputDir)
}

// Package downloads and installs a package based on a key in the context
// This mimics Python's install.package('PACKAGENAME') method
func (i *Installer) Package(packageKey string) error {
	// Context keys are typically uppercase (e.g., PHP_VERSION, COMPOSER_VERSION)
	// Convert packageKey to uppercase for context lookups
	upperKey := strings.ToUpper(packageKey)

	// Get the version and URI from context
	versionKey := fmt.Sprintf("%s_VERSION", upperKey)
	version, ok := i.ctx.Get(versionKey)
	if !ok {
		return fmt.Errorf("package version not found for key: %s", versionKey)
	}

	versionStr, ok := version.(string)
	if !ok {
		return fmt.Errorf("package version is not a string: %s", versionKey)
	}

	// Use libbuildpack installer if available
	if i.libbuildpackInst != nil {
		// Construct dependency object - use lowercase for dependency name
		dep := libbuildpack.Dependency{
			Name:    packageKey,
			Version: versionStr,
		}

		// Determine output directory
		buildDir := i.ctx.GetString("BUILD_DIR")
		outputDir := filepath.Join(buildDir, packageKey)

		// Install the dependency
		return i.libbuildpackInst.InstallDependency(dep, outputDir)
	}

	// Fallback: just log what would be done (shouldn't happen in production)
	urlKey := fmt.Sprintf("%s_DOWNLOAD_URL", upperKey)
	url, ok := i.ctx.Get(urlKey)
	if !ok {
		return fmt.Errorf("package URL not found for key: %s", urlKey)
	}

	urlStr, ok := url.(string)
	if !ok {
		return fmt.Errorf("package URL is not a string: %s", urlKey)
	}

	fmt.Printf("Would download package %s from %s\n", packageKey, urlStr)
	return nil
}

// Registry manages all registered extensions
type Registry struct {
	extensions []Extension
}

// NewRegistry creates a new extension registry
func NewRegistry() *Registry {
	return &Registry{
		extensions: make([]Extension, 0),
	}
}

// Register adds an extension to the registry
func (r *Registry) Register(ext Extension) {
	r.extensions = append(r.extensions, ext)
}

// Extensions returns all registered extensions
func (r *Registry) Extensions() []Extension {
	return r.extensions
}

// ProcessExtensions runs the specified method on all extensions
func (r *Registry) ProcessExtensions(ctx *Context, method string) error {
	for _, ext := range r.extensions {
		if !ext.ShouldCompile(ctx) {
			continue
		}

		switch method {
		case "configure":
			if err := ext.Configure(ctx); err != nil {
				return fmt.Errorf("extension %s configure failed: %w", ext.Name(), err)
			}
		default:
			return fmt.Errorf("unknown extension method: %s", method)
		}
	}
	return nil
}

// GetPreprocessCommands collects preprocess commands from all extensions
func (r *Registry) GetPreprocessCommands(ctx *Context) ([]string, error) {
	var allCommands []string
	for _, ext := range r.extensions {
		if !ext.ShouldCompile(ctx) {
			continue
		}

		commands, err := ext.PreprocessCommands(ctx)
		if err != nil {
			return nil, fmt.Errorf("extension %s preprocess commands failed: %w", ext.Name(), err)
		}
		allCommands = append(allCommands, commands...)
	}
	return allCommands, nil
}

// GetServiceCommands collects service commands from all extensions
func (r *Registry) GetServiceCommands(ctx *Context) (map[string]string, error) {
	allCommands := make(map[string]string)
	for _, ext := range r.extensions {
		if !ext.ShouldCompile(ctx) {
			continue
		}

		commands, err := ext.ServiceCommands(ctx)
		if err != nil {
			return nil, fmt.Errorf("extension %s service commands failed: %w", ext.Name(), err)
		}
		for name, cmd := range commands {
			allCommands[name] = cmd
		}
	}
	return allCommands, nil
}

// GetServiceEnvironment collects service environment variables from all extensions
func (r *Registry) GetServiceEnvironment(ctx *Context) (map[string]string, error) {
	allEnv := make(map[string]string)
	for _, ext := range r.extensions {
		if !ext.ShouldCompile(ctx) {
			continue
		}

		env, err := ext.ServiceEnvironment(ctx)
		if err != nil {
			return nil, fmt.Errorf("extension %s service environment failed: %w", ext.Name(), err)
		}
		for key, val := range env {
			allEnv[key] = val
		}
	}
	return allEnv, nil
}

// CompileExtensions runs the compile method on all extensions
func (r *Registry) CompileExtensions(ctx *Context, installer *Installer) error {
	for _, ext := range r.extensions {
		if !ext.ShouldCompile(ctx) {
			continue
		}

		if err := ext.Compile(ctx, installer); err != nil {
			return fmt.Errorf("extension %s compile failed: %w", ext.Name(), err)
		}
	}
	return nil
}

// ConfigFileEditor provides methods for editing configuration files
// This is the Go equivalent of Python's utils.ConfigFileEditor
type ConfigFileEditor struct {
	path  string
	lines []string
}

// NewConfigFileEditor creates a new config file editor
func NewConfigFileEditor(path string) (*ConfigFileEditor, error) {
	content, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read config file %s: %w", path, err)
	}

	lines := make([]string, 0)
	currentLine := ""
	for _, b := range content {
		if b == '\n' {
			lines = append(lines, currentLine+"\n")
			currentLine = ""
		} else {
			currentLine += string(b)
		}
	}
	if currentLine != "" {
		lines = append(lines, currentLine)
	}

	return &ConfigFileEditor{
		path:  path,
		lines: lines,
	}, nil
}

// UpdateLines replaces lines matching a regex pattern with a new line
func (e *ConfigFileEditor) UpdateLines(pattern, replacement string) error {
	re, err := regexp.Compile(pattern)
	if err != nil {
		return fmt.Errorf("invalid regex pattern %q: %w", pattern, err)
	}

	for i, line := range e.lines {
		// Remove trailing newline for matching
		lineContent := strings.TrimSuffix(line, "\n")
		if re.MatchString(lineContent) {
			e.lines[i] = replacement + "\n"
		}
	}
	return nil
}

// AppendLines appends lines to the file
func (e *ConfigFileEditor) AppendLines(newLines []string) {
	e.lines = append(e.lines, newLines...)
}

// Save writes the modified content back to the file
func (e *ConfigFileEditor) Save(path string) error {
	content := ""
	for _, line := range e.lines {
		content += line
	}
	return os.WriteFile(path, []byte(content), 0644)
}

// PHPConfigHelper provides PHP-specific configuration helpers
type PHPConfigHelper struct {
	ctx        *Context
	phpIniPath string
	phpFpmPath string
	phpIni     *ConfigFileEditor
	phpFpm     *ConfigFileEditor
}

// NewPHPConfigHelper creates a new PHP config helper
func NewPHPConfigHelper(ctx *Context) *PHPConfigHelper {
	return &PHPConfigHelper{
		ctx:        ctx,
		phpIniPath: filepath.Join(ctx.BuildDir, "php", "etc", "php.ini"),
		phpFpmPath: filepath.Join(ctx.BuildDir, "php", "etc", "php-fpm.conf"),
	}
}

// LoadConfig loads the PHP configuration files
func (h *PHPConfigHelper) LoadConfig() error {
	var err error
	if h.phpIni == nil {
		h.phpIni, err = NewConfigFileEditor(h.phpIniPath)
		if err != nil {
			return fmt.Errorf("failed to load php.ini: %w", err)
		}
	}
	if h.phpFpm == nil {
		h.phpFpm, err = NewConfigFileEditor(h.phpFpmPath)
		if err != nil {
			return fmt.Errorf("failed to load php-fpm.conf: %w", err)
		}
	}
	return nil
}

// PHPIni returns the php.ini config editor
func (h *PHPConfigHelper) PHPIni() *ConfigFileEditor {
	return h.phpIni
}

// PHPFpm returns the php-fpm.conf config editor
func (h *PHPConfigHelper) PHPFpm() *ConfigFileEditor {
	return h.phpFpm
}

// PHPIniPath returns the path to php.ini
func (h *PHPConfigHelper) PHPIniPath() string {
	return h.phpIniPath
}
