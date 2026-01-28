package supply

import (
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"

	"github.com/cloudfoundry/libbuildpack"
	"github.com/cloudfoundry/php-buildpack/src/php/config"
	"github.com/cloudfoundry/php-buildpack/src/php/extensions"
	"github.com/cloudfoundry/php-buildpack/src/php/options"
	"github.com/cloudfoundry/php-buildpack/src/php/util"
)

// Stager interface abstracts buildpack staging operations
type Stager interface {
	BuildDir() string
	CacheDir() string
	DepDir() string
	DepsIdx() string
	LinkDirectoryInDepDir(destDir, destSubDir string) error
	WriteEnvFile(envVar, envVal string) error
	WriteProfileD(scriptName, scriptContents string) error
}

// Manifest interface abstracts buildpack manifest operations
type Manifest interface {
	AllDependencyVersions(depName string) []string
	DefaultVersion(depName string) (libbuildpack.Dependency, error)
	GetEntry(dep libbuildpack.Dependency) (*libbuildpack.ManifestEntry, error)
	IsCached() bool
}

// Installer interface abstracts dependency installation
type Installer interface {
	InstallDependency(dep libbuildpack.Dependency, outputDir string) error
	InstallOnlyVersion(depName, installDir string) error
}

// Command interface abstracts command execution
type Command interface {
	Execute(dir string, stdout io.Writer, stderr io.Writer, program string, args ...string) error
	Output(dir string, program string, args ...string) (string, error)
}

// Supplier contains the buildpack supply phase logic
type Supplier struct {
	Manifest  Manifest
	Installer Installer
	Stager    Stager
	Command   Command
	Log       *libbuildpack.Logger
	Logfile   *os.File
	Registry  *extensions.Registry
	Options   *options.Options
	Context   *extensions.Context // Extension context with PHP version and extensions
}

// Run executes the PHP buildpack supply phase
func Run(s *Supplier) error {
	s.Log.BeginStep("Supplying PHP")

	// Load options from defaults/options.json and .bp-config/options.json
	bpDir, err := libbuildpack.GetBuildpackDir()
	if err != nil {
		return fmt.Errorf("unable to determine buildpack directory: %w", err)
	}

	opts, err := options.LoadOptions(bpDir, s.Stager.BuildDir(), s.Manifest, s.Log)
	if err != nil {
		s.Log.Error("Failed to load options: %v", err)
		return err
	}
	s.Options = opts
	s.Log.Debug("Options loaded: WEB_SERVER=%s, WEBDIR=%s, LIBDIR=%s", opts.WebServer, opts.WebDir, opts.LibDir)

	// Setup web directory if needed
	if err := s.setupWebDir(); err != nil {
		s.Log.Error("Error setting up web directory: %v", err)
		return err
	}

	// Setup log directory
	if err := s.setupLogDir(); err != nil {
		s.Log.Error("Error setting up log directory: %v", err)
		return err
	}

	// Store bpDir for extension context
	s.Log.Debug("Buildpack directory: %s", bpDir)
	os.Setenv("BP_DIR", bpDir) // Set for extensions that expect it

	// Create extension context if registry is provided
	if s.Registry != nil {
		ctx, err := s.createExtensionContext()
		if err != nil {
			s.Log.Error("Failed to create extension context: %v", err)
			return err
		}
		// Store context for later use
		s.Context = ctx

		// Run Configure phase for all extensions
		// This allows extensions to set PHP version and extensions early
		s.Log.Info("Running extension Configure phase")
		if err := s.Registry.ProcessExtensions(ctx, "configure"); err != nil {
			s.Log.Error("Extension configuration failed: %v", err)
			return err
		}

		// Sync PHP version from context back to options
		// Extensions (like composer) may have updated PHP_VERSION during Configure
		if phpVersion := ctx.GetString("PHP_VERSION"); phpVersion != "" {
			s.Options.PHPVersion = phpVersion
			s.Log.Debug("Updated PHP version from extension context: %s", phpVersion)
		}
	}

	// Determine and install PHP version
	if err := s.InstallPHP(); err != nil {
		s.Log.Error("Could not install PHP: %v", err)
		return err
	}

	// Install web server (httpd/nginx/none)
	if err := s.InstallWebServer(); err != nil {
		s.Log.Error("Could not install web server: %v", err)
		return err
	}

	// Run extension Compile phase if registry is provided
	if s.Registry != nil {
		// Reuse the context from Configure phase if available
		var ctx *extensions.Context
		var err error
		if s.Context != nil {
			ctx = s.Context
		} else {
			ctx, err = s.createExtensionContext()
			if err != nil {
				s.Log.Error("Failed to create extension context: %v", err)
				return err
			}
		}

		// Create extensions installer with libbuildpack installer
		installer := extensions.NewInstallerWithLibbuildpack(ctx, s.Installer)

		// Run Compile phase for all extensions
		s.Log.Info("Running extension Compile phase")
		if err := s.Registry.CompileExtensions(ctx, installer); err != nil {
			s.Log.Error("Extension compilation failed: %v", err)
			return err
		}
	}

	// Setup environment variables
	if err := s.CreateDefaultEnv(); err != nil {
		s.Log.Error("Unable to setup default environment: %s", err.Error())
		return err
	}

	s.Log.Info("PHP buildpack supply phase complete")
	return nil
}

// createExtensionContext creates an extension context from the buildpack state
func (s *Supplier) createExtensionContext() (*extensions.Context, error) {
	ctx, err := extensions.NewContext()
	if err != nil {
		return nil, fmt.Errorf("failed to create context: %w", err)
	}

	// Set buildpack directories
	ctx.Set("BUILD_DIR", s.Stager.BuildDir())
	ctx.Set("CACHE_DIR", s.Stager.CacheDir())
	ctx.Set("BP_DIR", os.Getenv("BP_DIR"))
	ctx.Set("DEPS_DIR", s.Stager.DepDir())
	ctx.Set("DEPS_IDX", s.Stager.DepsIdx())

	// Set common paths from options
	ctx.Set("WEBDIR", s.Options.WebDir)
	ctx.Set("LIBDIR", s.Options.LibDir)
	ctx.Set("TMPDIR", os.TempDir())

	// Get default versions from manifest
	if err := s.populateDefaultVersions(ctx); err != nil {
		return nil, fmt.Errorf("failed to populate default versions: %w", err)
	}

	// Set PHP configuration from options
	ctx.Set("PHP_VERSION", s.Options.GetPHPVersion())
	ctx.Set("PHP_DEFAULT", s.Options.PHPDefault)
	ctx.Set("PHP_EXTENSIONS", s.Options.PHPExtensions)
	ctx.Set("ZEND_EXTENSIONS", s.Options.ZendExtensions)
	ctx.Set("WEB_SERVER", s.Options.WebServer)
	ctx.Set("COMPOSER_VERSION", ctx.GetString("COMPOSER_DEFAULT")) // Use default from manifest

	// Set additional options
	ctx.Set("ADMIN_EMAIL", s.Options.AdminEmail)
	ctx.Set("COMPOSER_VENDOR_DIR", s.Options.ComposerVendorDir)

	// Set dynamic PHP version variables
	for key, version := range s.Options.PHPVersions {
		ctx.Set(key, version)
	}

	return ctx, nil
}

// populateDefaultVersions reads default versions from manifest and sets download URL patterns
// This mimics the Python buildpack's update_default_version function
func (s *Supplier) populateDefaultVersions(ctx *extensions.Context) error {
	// Set default versions and download URL patterns for each dependency
	dependencies := []string{"php", "httpd", "nginx", "composer"}

	for _, depName := range dependencies {
		// Get default version from manifest
		dep, err := s.Manifest.DefaultVersion(depName)
		if err != nil {
			s.Log.Warning("Could not get default version for %s: %v", depName, err)
			continue
		}

		// Get the manifest entry to access the URI
		entry, err := s.Manifest.GetEntry(dep)
		if err != nil {
			s.Log.Warning("Could not get manifest entry for %s %s: %v", depName, dep.Version, err)
			continue
		}

		// Convert to uppercase for key names (e.g., php -> PHP)
		upperDepName := strings.ToUpper(depName)

		// Set version keys (e.g., PHP_VERSION, PHP_DEFAULT)
		versionKey := fmt.Sprintf("%s_VERSION", upperDepName)
		defaultKey := fmt.Sprintf("%s_DEFAULT", upperDepName)
		ctx.Set(versionKey, dep.Version)
		ctx.Set(defaultKey, dep.Version)

		// Set download URL pattern (e.g., PHP_DOWNLOAD_URL)
		// This pattern will be used by the Installer to look up the actual URL
		downloadKey := fmt.Sprintf("%s_DOWNLOAD_URL", upperDepName)
		ctx.Set(downloadKey, entry.URI)

		// For PHP, also set all available versions for version matching
		if depName == "php" {
			allVersions := s.Manifest.AllDependencyVersions("php")
			ctx.Set("ALL_PHP_VERSIONS", strings.Join(allVersions, ","))
			s.Log.Debug("Set ALL_PHP_VERSIONS = %s", strings.Join(allVersions, ","))
		}

		s.Log.Debug("Set %s = %s", defaultKey, dep.Version)
		s.Log.Debug("Set %s = %s", downloadKey, entry.URI)
	}

	return nil
}

// setupWebDir sets up the web directory, moving app files into it if needed
// This mimics the Python buildpack's setup_webdir_if_it_doesnt_exist function
func (s *Supplier) setupWebDir() error {
	// Only move files if web server is configured (not "none")
	if s.Options.WebServer == "none" {
		s.Log.Debug("Web server is 'none', skipping WEBDIR setup")
		return nil
	}

	buildDir := s.Stager.BuildDir()
	webDirName := s.Options.WebDir
	webDirPath := filepath.Join(buildDir, webDirName)

	// Check if WEBDIR already exists
	if exists, err := libbuildpack.FileExists(webDirPath); err != nil {
		return fmt.Errorf("failed to check WEBDIR existence: %w", err)
	} else if exists {
		s.Log.Debug("WEBDIR already exists: %s", webDirPath)
		return nil
	}

	// WEBDIR doesn't exist - need to create it and move app files into it
	s.Log.Info("WEBDIR '%s' not found, moving app files into it", webDirName)

	// Create WEBDIR
	if err := os.MkdirAll(webDirPath, 0755); err != nil {
		return fmt.Errorf("failed to create WEBDIR: %w", err)
	}

	// Get list of files/dirs to move (exclude buildpack metadata)
	entries, err := os.ReadDir(buildDir)
	if err != nil {
		return fmt.Errorf("failed to read build directory: %w", err)
	}

	// Define exclusions - don't move these into WEBDIR
	exclusions := map[string]bool{
		".bp":            true,
		".bp-config":     true,
		".extensions":    true,
		".cloudfoundry":  true,
		".profile.d":     true,
		".protodata":     true,
		"manifest.yml":   true,
		webDirName:       true, // Don't move WEBDIR into itself
		s.Options.LibDir: true, // Don't move LIBDIR (default: "lib")
	}

	// Move files into WEBDIR
	for _, entry := range entries {
		name := entry.Name()

		// Skip excluded files/dirs
		if exclusions[name] {
			s.Log.Debug("Skipping excluded path: %s", name)
			continue
		}

		// Skip hidden files (starting with .)
		if strings.HasPrefix(name, ".") {
			s.Log.Debug("Skipping hidden file: %s", name)
			continue
		}

		srcPath := filepath.Join(buildDir, name)
		destPath := filepath.Join(webDirPath, name)

		s.Log.Debug("Moving %s -> %s", name, filepath.Join(webDirName, name))
		if err := os.Rename(srcPath, destPath); err != nil {
			return fmt.Errorf("failed to move %s into WEBDIR: %w", name, err)
		}
	}

	s.Log.Info("Moved app files into WEBDIR: %s", webDirName)
	return nil
}

// setupLogDir creates the logs directory
func (s *Supplier) setupLogDir() error {
	logPath := filepath.Join(s.Stager.BuildDir(), "logs")
	if err := os.MkdirAll(logPath, 0755); err != nil {
		return fmt.Errorf("could not create logs directory: %v", err)
	}
	return nil
}

// InstallPHP installs the PHP runtime
func (s *Supplier) InstallPHP() error {
	var dep libbuildpack.Dependency

	// Get PHP version from options (user config or default)
	phpVersion := s.Options.GetPHPVersion()
	if phpVersion == "" {
		// Fallback to manifest default if not set
		var err error
		dep, err = s.Manifest.DefaultVersion("php")
		if err != nil {
			return err
		}
	} else {
		// Use specified version
		dep = libbuildpack.Dependency{
			Name:    "php",
			Version: phpVersion,
		}
	}

	s.Log.Info("Installing PHP %s", dep.Version)

	phpInstallDir := filepath.Join(s.Stager.DepDir(), "php")
	if err := s.Installer.InstallDependency(dep, phpInstallDir); err != nil {
		return err
	}

	// Link PHP binaries
	if err := s.Stager.LinkDirectoryInDepDir(filepath.Join(phpInstallDir, "bin"), "bin"); err != nil {
		return err
	}
	if err := s.Stager.LinkDirectoryInDepDir(filepath.Join(phpInstallDir, "lib"), "lib"); err != nil {
		return err
	}

	// Set environment variables
	if err := os.Setenv("PATH", fmt.Sprintf("%s:%s", filepath.Join(s.Stager.DepDir(), "bin"), os.Getenv("PATH"))); err != nil {
		return err
	}

	// Extract PHP config files from embedded defaults
	phpEtcDir := filepath.Join(phpInstallDir, "etc")
	phpConfigPath := s.getConfigPathForPHPVersion(dep.Version)
	s.Log.Debug("Extracting PHP config from %s to: %s", phpConfigPath, phpEtcDir)
	if err := config.ExtractConfig(phpConfigPath, phpEtcDir); err != nil {
		return fmt.Errorf("failed to extract PHP config: %w", err)
	}

	// Allow user overrides from .bp-config/php/php.ini and .bp-config/php/php-fpm.conf
	userConfDir := filepath.Join(s.Stager.BuildDir(), ".bp-config", "php")
	if exists, err := libbuildpack.FileExists(userConfDir); err != nil {
		return fmt.Errorf("failed to check for user PHP config: %w", err)
	} else if exists {
		s.Log.Info("Applying user PHP configuration overrides")
		if err := s.copyUserConfigs(userConfDir, phpEtcDir); err != nil {
			return fmt.Errorf("failed to apply user PHP config: %w", err)
		}
	}

	// Create php.ini.d directory for extension configs
	phpIniDir := filepath.Join(phpEtcDir, "php.ini.d")
	if err := os.MkdirAll(phpIniDir, 0755); err != nil {
		return fmt.Errorf("failed to create php.ini.d directory: %w", err)
	}

	// Process php.ini to replace build-time extension placeholders only
	// Runtime placeholders (@{HOME}, etc.) are replaced during finalize phase
	phpIniPath := filepath.Join(phpEtcDir, "php.ini")
	if err := s.processPhpIni(phpIniPath); err != nil {
		return fmt.Errorf("failed to process php.ini: %w", err)
	}

	// Process php-fpm.conf to set include directive if user has fpm.d configs
	phpFpmConfPath := filepath.Join(phpEtcDir, "php-fpm.conf")
	if err := s.processPhpFpmConf(phpFpmConfPath, phpEtcDir); err != nil {
		return fmt.Errorf("failed to process php-fpm.conf: %w", err)
	}

	// Create include-path.ini with @{HOME} placeholder for runtime rewriting
	phpIniDDir := filepath.Join(phpEtcDir, "php.ini.d")
	if err := s.createIncludePathIni(phpIniDDir); err != nil {
		return fmt.Errorf("failed to create include-path.ini: %w", err)
	}

	// Note: User's .bp-config/php/fpm.d/*.conf files are already copied by copyUserConfigs() above
	// They will be processed during the finalize phase (build-time placeholder replacement)

	return nil
}

func (s *Supplier) processPhpIni(phpIniPath string) error {
	var phpExtensions, zendExtensions []string
	if s.Context != nil {
		phpExtensions = s.Context.GetStringSlice("PHP_EXTENSIONS")
		zendExtensions = s.Context.GetStringSlice("ZEND_EXTENSIONS")
	} else {
		phpExtensions = s.Options.PHPExtensions
		zendExtensions = s.Options.ZendExtensions
	}

	phpInstallDir := filepath.Join(s.Stager.DepDir(), "php")

	logWarning := func(format string, args ...interface{}) {
		s.Log.Warning(format, args...)
	}

	return config.ProcessPhpIni(
		phpIniPath,
		phpInstallDir,
		phpExtensions,
		zendExtensions,
		nil,
		logWarning,
	)
}

// processPhpFpmConf processes php-fpm.conf to set the include directive for fpm.d configs
func (s *Supplier) processPhpFpmConf(phpFpmConfPath, phpEtcDir string) error {
	// Read the php-fpm.conf file
	content, err := os.ReadFile(phpFpmConfPath)
	if err != nil {
		return fmt.Errorf("failed to read php-fpm.conf: %w", err)
	}

	phpFpmConfContent := string(content)

	// Check if user has fpm.d configs
	fpmDDir := filepath.Join(phpEtcDir, "fpm.d")
	hasFpmDConfigs := false
	if exists, err := libbuildpack.FileExists(fpmDDir); err != nil {
		return fmt.Errorf("failed to check for fpm.d directory: %w", err)
	} else if exists {
		// Check if there are any .conf files in fpm.d
		entries, err := os.ReadDir(fpmDDir)
		if err != nil {
			return fmt.Errorf("failed to read fpm.d directory: %w", err)
		}
		for _, entry := range entries {
			if !entry.IsDir() && filepath.Ext(entry.Name()) == ".conf" {
				hasFpmDConfigs = true
				s.Log.Debug("Found user fpm.d config: %s", entry.Name())
				break
			}
		}
	}

	// Set the include directive based on whether user has fpm.d configs
	var includeDirective string
	if hasFpmDConfigs {
		// Use DEPS_DIR with dynamic index which will be replaced during finalize phase
		depsIdx := s.Stager.DepsIdx()
		includeDirective = fmt.Sprintf("include=@{DEPS_DIR}/%s/php/etc/fpm.d/*.conf", depsIdx)
		s.Log.Info("Enabling fpm.d config includes")
	} else {
		includeDirective = ""
		s.Log.Debug("No user fpm.d configs found, include directive disabled")
	}

	// Replace the placeholder
	phpFpmConfContent = strings.ReplaceAll(phpFpmConfContent, "@{PHP_FPM_CONF_INCLUDE}", includeDirective)

	// Write back to php-fpm.conf
	if err := os.WriteFile(phpFpmConfPath, []byte(phpFpmConfContent), 0644); err != nil {
		return fmt.Errorf("failed to write php-fpm.conf: %w", err)
	}

	return nil
}

// createIncludePathIni creates a separate include-path.ini file in php.ini.d
// This file uses @{HOME} placeholder which gets replaced during finalize phase AFTER HOME is restored
// to /home/vcap/app, avoiding the issue where php.ini gets rewritten while HOME
// points to the deps directory
func (s *Supplier) createIncludePathIni(phpIniDDir string) error {
	includePathIniPath := filepath.Join(phpIniDDir, "include-path.ini")

	// Use @{HOME} placeholder which will be replaced during finalize phase
	// after HOME is restored to /home/vcap/app
	content := `; Include path configuration
; This file is rewritten during finalize phase after HOME is restored to /home/vcap/app
include_path = ".:/usr/share/php:@{HOME}/lib"
`

	if err := os.WriteFile(includePathIniPath, []byte(content), 0644); err != nil {
		return fmt.Errorf("failed to write include-path.ini: %w", err)
	}

	s.Log.Debug("Created include-path.ini with @{HOME}/lib placeholder")
	return nil
}

// InstallWebServer installs the web server (httpd, nginx, or none) based on configuration
func (s *Supplier) InstallWebServer() error {
	// Get WEB_SERVER from options (user config or default)
	webServer := s.Options.WebServer

	s.Log.Info("Web server: %s", webServer)

	switch webServer {
	case "httpd":
		return s.installHTTPD()
	case "nginx":
		return s.installNginx()
	case "none":
		s.Log.Info("No web server requested")
		return nil
	default:
		return fmt.Errorf("unsupported web server: %s", webServer)
	}
}

// installHTTPD installs and configures Apache HTTPD
func (s *Supplier) installHTTPD() error {
	var dep libbuildpack.Dependency
	var err error

	// Get default version from manifest
	dep, err = s.Manifest.DefaultVersion("httpd")
	if err != nil {
		return fmt.Errorf("could not get httpd version: %w", err)
	}

	s.Log.Info("Installing HTTPD %s", dep.Version)

	// Install to deps directory
	httpdInstallDir := filepath.Join(s.Stager.DepDir(), "httpd")
	if err := s.Installer.InstallDependency(dep, httpdInstallDir); err != nil {
		return fmt.Errorf("could not install httpd: %w", err)
	}

	// Set PHP-FPM to listen on TCP for httpd
	os.Setenv("PHP_FPM_LISTEN", "127.0.0.1:9000")

	// Extract httpd config files from embedded defaults
	httpdConfDir := filepath.Join(s.Stager.BuildDir(), "httpd", "conf")
	s.Log.Debug("Extracting HTTPD config to: %s", httpdConfDir)
	if err := config.ExtractConfig("httpd", httpdConfDir); err != nil {
		return fmt.Errorf("failed to extract httpd config: %w", err)
	}

	// Allow user overrides from .bp-config/httpd
	userConfDir := filepath.Join(s.Stager.BuildDir(), ".bp-config", "httpd")
	if exists, err := libbuildpack.FileExists(userConfDir); err != nil {
		return fmt.Errorf("failed to check for user httpd config: %w", err)
	} else if exists {
		s.Log.Info("Applying user httpd configuration overrides")
		if err := s.copyUserConfigs(userConfDir, httpdConfDir); err != nil {
			return fmt.Errorf("failed to apply user httpd config: %w", err)
		}
	}

	s.Log.Info("HTTPD installed successfully")
	return nil
}

// installNginx installs and configures Nginx
func (s *Supplier) installNginx() error {
	var dep libbuildpack.Dependency
	var err error

	// Get default version from manifest
	dep, err = s.Manifest.DefaultVersion("nginx")
	if err != nil {
		return fmt.Errorf("could not get nginx version: %w", err)
	}

	s.Log.Info("Installing Nginx %s", dep.Version)

	// Install to deps directory
	nginxInstallDir := filepath.Join(s.Stager.DepDir(), "nginx")
	if err := s.Installer.InstallDependency(dep, nginxInstallDir); err != nil {
		return fmt.Errorf("could not install nginx: %w", err)
	}

	// Set PHP-FPM to listen on TCP for nginx (consistent with httpd)
	os.Setenv("PHP_FPM_LISTEN", "127.0.0.1:9000")

	// Extract nginx config files from embedded defaults
	nginxConfDir := filepath.Join(s.Stager.BuildDir(), "nginx", "conf")
	s.Log.Debug("Extracting Nginx config to: %s", nginxConfDir)
	if err := config.ExtractConfig("nginx", nginxConfDir); err != nil {
		return fmt.Errorf("failed to extract nginx config: %w", err)
	}

	// Allow user overrides from .bp-config/nginx
	userConfDir := filepath.Join(s.Stager.BuildDir(), ".bp-config", "nginx")
	if exists, err := libbuildpack.FileExists(userConfDir); err != nil {
		return fmt.Errorf("failed to check for user nginx config: %w", err)
	} else if exists {
		s.Log.Info("Applying user nginx configuration overrides")
		if err := s.copyUserConfigs(userConfDir, nginxConfDir); err != nil {
			return fmt.Errorf("failed to apply user nginx config: %w", err)
		}
	}

	s.Log.Info("Nginx installed successfully")
	return nil
}

// CreateDefaultEnv sets up default environment variables
func (s *Supplier) CreateDefaultEnv() error {
	environmentVars := map[string]string{
		"PHPRC":            filepath.Join(s.Stager.DepDir(), "php", "etc"),
		"PHP_INI_SCAN_DIR": filepath.Join(s.Stager.DepDir(), "php", "etc", "php.ini.d"),
	}

	scriptContents := fmt.Sprintf(`export PHPRC=$DEPS_DIR/%s/php/etc
export PHP_INI_SCAN_DIR=$DEPS_DIR/%s/php/etc/php.ini.d
`, s.Stager.DepsIdx(), s.Stager.DepsIdx())

	for envVar, envValue := range environmentVars {
		if err := s.Stager.WriteEnvFile(envVar, envValue); err != nil {
			return err
		}
	}

	return s.Stager.WriteProfileD("php.sh", scriptContents)
}

// getConfigPathForPHPVersion returns the config path for a PHP version
// Maps versions like "8.1.29" to config paths like "php/8.1.x"
func (s *Supplier) getConfigPathForPHPVersion(version string) string {
	// Extract major.minor from version (e.g., "8.1.29" -> "8.1")
	parts := strings.Split(version, ".")
	if len(parts) < 2 {
		s.Log.Warning("Invalid PHP version format: %s, using php/8.1.x as fallback", version)
		return "php/8.1.x"
	}

	majorMinor := fmt.Sprintf("%s.%s", parts[0], parts[1])
	configPath := fmt.Sprintf("php/%s.x", majorMinor)

	s.Log.Debug("PHP %s -> config path %s", version, configPath)
	return configPath
}

// copyUserConfigs recursively copies user config files from source to destination
// This allows users to override default configs by placing files in .bp-config/httpd or .bp-config/nginx
func (s *Supplier) copyUserConfigs(srcDir, destDir string) error {
	return filepath.Walk(srcDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		// Get relative path from source directory
		relPath, err := filepath.Rel(srcDir, path)
		if err != nil {
			return err
		}

		// Construct destination path
		destPath := filepath.Join(destDir, relPath)

		// If it's a directory, create it
		if info.IsDir() {
			return os.MkdirAll(destPath, 0755)
		}

		// If it's a file, copy it
		s.Log.Debug("Copying user config: %s -> %s", path, destPath)
		return util.CopyFile(path, destPath)
	})
}

// ProcessPhpFpmConfForTesting exposes processPhpFpmConf for testing purposes
func (s *Supplier) ProcessPhpFpmConfForTesting(phpFpmConfPath, phpEtcDir string) error {
	return s.processPhpFpmConf(phpFpmConfPath, phpEtcDir)
}

func (s *Supplier) loadUserExtensions(ctx *extensions.Context) error {
	return extensions.LoadUserExtensions(ctx, s.Stager.BuildDir())
}
