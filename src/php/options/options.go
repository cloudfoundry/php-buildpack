package options

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/cloudfoundry/libbuildpack"
	"github.com/cloudfoundry/php-buildpack/src/php/config"
	"github.com/cloudfoundry/php-buildpack/src/php/util"
)

// Manifest interface abstracts the buildpack manifest operations needed for options
type Manifest interface {
	AllDependencyVersions(depName string) []string
	DefaultVersion(depName string) (libbuildpack.Dependency, error)
}

// Options represents the merged buildpack configuration from defaults/options.json and .bp-config/options.json
type Options struct {
	Stack      string `json:"STACK"`
	LibDir     string `json:"LIBDIR"`                // Library directory (default: "lib")
	WebDir     string `json:"WEBDIR"`                // Web root directory (default: "htdocs")
	WebServer  string `json:"WEB_SERVER"`            // Web server: "httpd", "nginx", or "none"
	PHPVM      string `json:"PHP_VM"`                // PHP VM type (default: "php")
	PHPVersion string `json:"PHP_VERSION,omitempty"` // Specific PHP version to install
	PHPDefault string `json:"PHP_DEFAULT,omitempty"` // Default PHP version from manifest
	AdminEmail string `json:"ADMIN_EMAIL"`           // Admin email for server config (used by httpd)

	// STRIP flags control whether to strip the top-level directory when extracting archives.
	// These are internal flags used during dependency installation and rarely need to be changed.
	// The defaults (false for main packages, true for modules) work for standard buildpack usage.
	HTTPDStrip        bool `json:"HTTPD_STRIP"`         // Strip top dir when extracting httpd (default: false)
	HTTPDModulesStrip bool `json:"HTTPD_MODULES_STRIP"` // Strip top dir for httpd modules (default: true)
	NginxStrip        bool `json:"NGINX_STRIP"`         // Strip top dir when extracting nginx (default: false)
	PHPStrip          bool `json:"PHP_STRIP"`           // Strip top dir when extracting php (default: false)
	PHPModulesStrip   bool `json:"PHP_MODULES_STRIP"`   // Strip top dir for php modules (default: true)

	PHPModules             []string `json:"PHP_MODULES"`                        // PHP modules to load
	PHPExtensions          []string `json:"PHP_EXTENSIONS"`                     // PHP extensions to enable
	ZendExtensions         []string `json:"ZEND_EXTENSIONS"`                    // Zend extensions to enable
	ComposerVendorDir      string   `json:"COMPOSER_VENDOR_DIR,omitempty"`      // Custom composer vendor directory
	ComposerInstallOptions []string `json:"COMPOSER_INSTALL_OPTIONS,omitempty"` // Additional composer install options

	// Internal flags
	OptionsJSONHasPHPExtensions bool `json:"OPTIONS_JSON_HAS_PHP_EXTENSIONS,omitempty"`

	// Dynamic PHP version tracking (e.g., PHP_81_LATEST, PHP_82_LATEST)
	PHPVersions map[string]string `json:"-"`
}

// LoadOptions loads and merges options from defaults/options.json and .bp-config/options.json
func LoadOptions(bpDir, buildDir string, manifest Manifest, logger *libbuildpack.Logger) (*Options, error) {
	opts := &Options{
		PHPVersions: make(map[string]string),
	}

	// Load default options from embedded defaults/options.json
	logger.Debug("Loading default options from embedded config")
	data, err := config.GetOptionsJSON()
	if err != nil {
		return nil, fmt.Errorf("failed to load default options: %w", err)
	}
	if err := json.Unmarshal(data, opts); err != nil {
		return nil, fmt.Errorf("invalid default options.json: %w", err)
	}

	// Get PHP default version from manifest
	defaultVersions := manifest.AllDependencyVersions("php")
	if len(defaultVersions) > 0 {
		// Find the default version from manifest
		if dep, err := manifest.DefaultVersion("php"); err == nil {
			opts.PHPDefault = dep.Version
			logger.Debug("Set PHP_DEFAULT = %s from manifest", dep.Version)
		}
	}

	// Build PHP version map (e.g., PHP_81_LATEST, PHP_82_LATEST)
	phpVersions := manifest.AllDependencyVersions("php")
	versionsByLine := make(map[string][]string)

	for _, version := range phpVersions {
		parts := strings.Split(version, ".")
		if len(parts) >= 2 {
			// Create key like "PHP_81_LATEST" for PHP 8.1.x
			key := fmt.Sprintf("PHP_%s%s_LATEST", parts[0], parts[1])
			versionsByLine[key] = append(versionsByLine[key], version)
		}
	}

	// Sort and find highest patch version for each line
	for key, versions := range versionsByLine {
		if len(versions) > 0 {
			// Sort versions and take the last (highest)
			sortVersions(versions)
			highest := versions[len(versions)-1]
			opts.PHPVersions[key] = highest
			logger.Debug("Set %s = %s", key, highest)
		}
	}

	// Load user options from .bp-config/options.json (if exists)
	userOptsPath := filepath.Join(buildDir, ".bp-config", "options.json")
	if exists, err := libbuildpack.FileExists(userOptsPath); err != nil {
		return nil, fmt.Errorf("failed to check for user options: %w", err)
	} else if exists {
		logger.Info("Loading user configuration from .bp-config/options.json")
		userOpts := &Options{}
		if err := loadJSONFile(userOptsPath, userOpts, logger); err != nil {
			// Print the file contents on error for debugging
			if content, readErr := os.ReadFile(userOptsPath); readErr == nil {
				logger.Error("Invalid JSON in %s:\n%s", userOptsPath, string(content))
			}
			return nil, fmt.Errorf("failed to load user options: %w", err)
		}

		// Merge user options into default options
		opts.mergeUserOptions(userOpts)

		// Set flag if user specified PHP extensions
		if len(userOpts.PHPExtensions) > 0 {
			opts.OptionsJSONHasPHPExtensions = true
			fmt.Println("Warning: PHP_EXTENSIONS in options.json is deprecated. See: http://docs.cloudfoundry.org/buildpacks/php/gsg-php-config.html")
		}
	}

	// Validate required fields
	if err := opts.validate(); err != nil {
		return nil, err
	}

	return opts, nil
}

// loadJSONFile loads a JSON file into the target structure
func loadJSONFile(path string, target interface{}, logger *libbuildpack.Logger) error {
	logger.Debug("Loading config from %s", path)

	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return fmt.Errorf("config file not found: %s", path)
		}
		return err
	}

	if err := json.Unmarshal(data, target); err != nil {
		return fmt.Errorf("invalid JSON in %s: %w", path, err)
	}

	return nil
}

// mergeUserOptions merges user-provided options into the default options
// User options override defaults, but only for fields that are explicitly set
func (o *Options) mergeUserOptions(user *Options) {
	if user.Stack != "" {
		o.Stack = user.Stack
	}
	if user.LibDir != "" {
		o.LibDir = user.LibDir
	}
	if user.WebDir != "" {
		o.WebDir = user.WebDir
	}
	if user.WebServer != "" {
		o.WebServer = user.WebServer
	}
	if user.PHPVM != "" {
		o.PHPVM = user.PHPVM
	}
	if user.PHPVersion != "" {
		o.PHPVersion = user.PHPVersion
	}
	if user.AdminEmail != "" {
		o.AdminEmail = user.AdminEmail
	}
	if user.ComposerVendorDir != "" {
		o.ComposerVendorDir = user.ComposerVendorDir
	}

	// Merge arrays - user values replace defaults
	if len(user.PHPModules) > 0 {
		o.PHPModules = user.PHPModules
	}
	if len(user.PHPExtensions) > 0 {
		o.PHPExtensions = user.PHPExtensions
	}
	if len(user.ZendExtensions) > 0 {
		o.ZendExtensions = user.ZendExtensions
	}
	if len(user.ComposerInstallOptions) > 0 {
		o.ComposerInstallOptions = user.ComposerInstallOptions
	}

	// Note: Boolean fields are not merged because we can't distinguish between
	// false (user set) and false (default zero value). If needed, use pointers.
}

// validate checks that required options are set and valid
func (o *Options) validate() error {
	// Check web server is valid
	if o.WebServer != "httpd" && o.WebServer != "nginx" && o.WebServer != "none" {
		return fmt.Errorf("invalid WEB_SERVER: %s (must be 'httpd', 'nginx', or 'none')", o.WebServer)
	}

	// Other validations can be added here
	return nil
}

// GetPHPVersion returns the PHP version to use, either from user config or default
// Resolves placeholders like {PHP_83_LATEST} to actual versions
func (o *Options) GetPHPVersion() string {
	if o.PHPVersion != "" {
		// Check if it's a placeholder like {PHP_83_LATEST}
		if strings.HasPrefix(o.PHPVersion, "{") && strings.HasSuffix(o.PHPVersion, "}") {
			// Extract the placeholder name (remove { and })
			placeholderName := strings.TrimPrefix(strings.TrimSuffix(o.PHPVersion, "}"), "{")

			// Look up the actual version from PHPVersions map
			if actualVersion, exists := o.PHPVersions[placeholderName]; exists {
				return actualVersion
			}

			// If placeholder not found, return as-is (will fail with clear error message)
			// This allows the buildpack to show which placeholder was invalid
		}
		return o.PHPVersion
	}
	return o.PHPDefault
}

// sortVersions sorts semantic versions in ascending order
func sortVersions(versions []string) {
	// Simple bubble sort for semantic versions
	for i := 0; i < len(versions); i++ {
		for j := i + 1; j < len(versions); j++ {
			if util.CompareVersions(versions[i], versions[j]) > 0 {
				versions[i], versions[j] = versions[j], versions[i]
			}
		}
	}
}
