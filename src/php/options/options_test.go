package options_test

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/cloudfoundry/libbuildpack"
	"github.com/cloudfoundry/php-buildpack/src/php/options"
)

// MockManifest implements the Manifest interface for testing
type MockManifest struct {
	versions       map[string][]string
	defaultVersion map[string]libbuildpack.Dependency
}

func (m *MockManifest) AllDependencyVersions(depName string) []string {
	return m.versions[depName]
}

func (m *MockManifest) DefaultVersion(depName string) (libbuildpack.Dependency, error) {
	return m.defaultVersion[depName], nil
}

func TestLoadOptions_DefaultOnly(t *testing.T) {
	// Setup temp directories
	tmpDir := t.TempDir()
	bpDir := filepath.Join(tmpDir, "bp")
	buildDir := filepath.Join(tmpDir, "build")

	// Create defaults directory
	defaultsDir := filepath.Join(bpDir, "defaults")
	if err := os.MkdirAll(defaultsDir, 0755); err != nil {
		t.Fatalf("Failed to create defaults dir: %v", err)
	}

	// Write default options.json
	defaultOpts := `{
		"STACK": "cflinuxfs4",
		"LIBDIR": "lib",
		"WEBDIR": "htdocs",
		"WEB_SERVER": "httpd",
		"PHP_VM": "php",
		"ADMIN_EMAIL": "admin@localhost",
		"HTTPD_STRIP": false,
		"HTTPD_MODULES_STRIP": true,
		"NGINX_STRIP": false,
		"PHP_STRIP": false,
		"PHP_MODULES_STRIP": true,
		"PHP_MODULES": [],
		"PHP_EXTENSIONS": ["bz2", "zlib", "curl"],
		"ZEND_EXTENSIONS": []
	}`
	if err := os.WriteFile(filepath.Join(defaultsDir, "options.json"), []byte(defaultOpts), 0644); err != nil {
		t.Fatalf("Failed to write default options: %v", err)
	}

	// Create mock manifest
	manifest := &MockManifest{
		versions: map[string][]string{
			"php": {"8.1.10", "8.1.29", "8.2.5", "8.2.15", "8.3.1"},
		},
		defaultVersion: map[string]libbuildpack.Dependency{
			"php": {Name: "php", Version: "8.1.29"},
		},
	}

	// Create mock logger
	logger := libbuildpack.NewLogger(os.Stdout)

	// Load options
	opts, err := options.LoadOptions(bpDir, buildDir, manifest, logger)
	if err != nil {
		t.Fatalf("LoadOptions failed: %v", err)
	}

	// Verify defaults are loaded
	if opts.WebServer != "httpd" {
		t.Errorf("Expected WEB_SERVER=httpd, got %s", opts.WebServer)
	}
	if opts.WebDir != "htdocs" {
		t.Errorf("Expected WEBDIR=htdocs, got %s", opts.WebDir)
	}
	if opts.LibDir != "lib" {
		t.Errorf("Expected LIBDIR=lib, got %s", opts.LibDir)
	}

	// Verify PHP default version from manifest
	if opts.PHPDefault != "8.1.29" {
		t.Errorf("Expected PHPDefault=8.1.29, got %s", opts.PHPDefault)
	}

	// Verify PHP_XX_LATEST versions are set
	if opts.PHPVersions["PHP_81_LATEST"] != "8.1.29" {
		t.Errorf("Expected PHP_81_LATEST=8.1.29, got %s", opts.PHPVersions["PHP_81_LATEST"])
	}
	if opts.PHPVersions["PHP_82_LATEST"] != "8.2.15" {
		t.Errorf("Expected PHP_82_LATEST=8.2.15, got %s", opts.PHPVersions["PHP_82_LATEST"])
	}
	if opts.PHPVersions["PHP_83_LATEST"] != "8.3.1" {
		t.Errorf("Expected PHP_83_LATEST=8.3.1, got %s", opts.PHPVersions["PHP_83_LATEST"])
	}
}

func TestLoadOptions_UserOverride(t *testing.T) {
	// Setup temp directories
	tmpDir := t.TempDir()
	bpDir := filepath.Join(tmpDir, "bp")
	buildDir := filepath.Join(tmpDir, "build")

	// Create defaults directory
	defaultsDir := filepath.Join(bpDir, "defaults")
	if err := os.MkdirAll(defaultsDir, 0755); err != nil {
		t.Fatalf("Failed to create defaults dir: %v", err)
	}

	// Write default options.json
	defaultOpts := `{
		"STACK": "cflinuxfs4",
		"LIBDIR": "lib",
		"WEBDIR": "htdocs",
		"WEB_SERVER": "httpd",
		"PHP_VM": "php",
		"ADMIN_EMAIL": "admin@localhost",
		"HTTPD_STRIP": false,
		"HTTPD_MODULES_STRIP": true,
		"NGINX_STRIP": false,
		"PHP_STRIP": false,
		"PHP_MODULES_STRIP": true,
		"PHP_MODULES": [],
		"PHP_EXTENSIONS": ["bz2", "zlib"],
		"ZEND_EXTENSIONS": []
	}`
	if err := os.WriteFile(filepath.Join(defaultsDir, "options.json"), []byte(defaultOpts), 0644); err != nil {
		t.Fatalf("Failed to write default options: %v", err)
	}

	// Create user config directory
	userConfigDir := filepath.Join(buildDir, ".bp-config")
	if err := os.MkdirAll(userConfigDir, 0755); err != nil {
		t.Fatalf("Failed to create user config dir: %v", err)
	}

	// Write user options.json with overrides
	userOpts := `{
		"WEB_SERVER": "nginx",
		"WEBDIR": "public",
		"PHP_VERSION": "8.2.15",
		"PHP_EXTENSIONS": ["pdo", "pdo_mysql", "redis"]
	}`
	if err := os.WriteFile(filepath.Join(userConfigDir, "options.json"), []byte(userOpts), 0644); err != nil {
		t.Fatalf("Failed to write user options: %v", err)
	}

	// Create mock manifest
	manifest := &MockManifest{
		versions: map[string][]string{
			"php": {"8.1.29", "8.2.15"},
		},
		defaultVersion: map[string]libbuildpack.Dependency{
			"php": {Name: "php", Version: "8.1.29"},
		},
	}

	// Create mock logger
	logger := libbuildpack.NewLogger(os.Stdout)

	// Load options
	opts, err := options.LoadOptions(bpDir, buildDir, manifest, logger)
	if err != nil {
		t.Fatalf("LoadOptions failed: %v", err)
	}

	// Verify user overrides
	if opts.WebServer != "nginx" {
		t.Errorf("Expected WEB_SERVER=nginx, got %s", opts.WebServer)
	}
	if opts.WebDir != "public" {
		t.Errorf("Expected WEBDIR=public, got %s", opts.WebDir)
	}
	if opts.LibDir != "lib" {
		t.Errorf("Expected LIBDIR=lib (default), got %s", opts.LibDir)
	}
	if opts.PHPVersion != "8.2.15" {
		t.Errorf("Expected PHP_VERSION=8.2.15, got %s", opts.PHPVersion)
	}

	// Verify PHP extensions were overridden
	if len(opts.PHPExtensions) != 3 {
		t.Errorf("Expected 3 PHP extensions, got %d", len(opts.PHPExtensions))
	}
	if opts.OptionsJSONHasPHPExtensions != true {
		t.Errorf("Expected OptionsJSONHasPHPExtensions=true")
	}
}

func TestLoadOptions_InvalidWebServer(t *testing.T) {
	// Setup temp directories
	tmpDir := t.TempDir()
	bpDir := filepath.Join(tmpDir, "bp")
	buildDir := filepath.Join(tmpDir, "build")

	// Create user config directory with invalid web server
	userConfigDir := filepath.Join(buildDir, ".bp-config")
	if err := os.MkdirAll(userConfigDir, 0755); err != nil {
		t.Fatalf("Failed to create user config dir: %v", err)
	}

	// Write user options.json with INVALID web server
	userOpts := `{
		"WEB_SERVER": "apache"
	}`
	if err := os.WriteFile(filepath.Join(userConfigDir, "options.json"), []byte(userOpts), 0644); err != nil {
		t.Fatalf("Failed to write user options: %v", err)
	}

	// Create mock manifest
	manifest := &MockManifest{
		versions: map[string][]string{
			"php": {"8.1.29"},
		},
		defaultVersion: map[string]libbuildpack.Dependency{
			"php": {Name: "php", Version: "8.1.29"},
		},
	}

	// Create mock logger
	logger := libbuildpack.NewLogger(os.Stdout)

	// Load options - should fail validation
	_, err := options.LoadOptions(bpDir, buildDir, manifest, logger)
	if err == nil {
		t.Fatal("Expected error for invalid WEB_SERVER 'apache', got nil")
	}

	// Verify error message
	expectedMsg := "invalid WEB_SERVER: apache"
	if !strings.Contains(err.Error(), expectedMsg) {
		t.Errorf("Expected error containing '%s', got: %v", expectedMsg, err)
	}
}

func TestGetPHPVersion(t *testing.T) {
	opts := &options.Options{
		PHPDefault: "8.1.29",
		PHPVersion: "",
	}

	// Should return default when PHPVersion is not set
	if opts.GetPHPVersion() != "8.1.29" {
		t.Errorf("Expected 8.1.29, got %s", opts.GetPHPVersion())
	}

	// Should return user version when set
	opts.PHPVersion = "8.2.15"
	if opts.GetPHPVersion() != "8.2.15" {
		t.Errorf("Expected 8.2.15, got %s", opts.GetPHPVersion())
	}
}

func TestGetPHPVersion_PlaceholderResolution(t *testing.T) {
	tests := []struct {
		name        string
		phpVersion  string
		phpVersions map[string]string
		expected    string
	}{
		{
			name:       "Resolves {PHP_83_LATEST} placeholder",
			phpVersion: "{PHP_83_LATEST}",
			phpVersions: map[string]string{
				"PHP_81_LATEST": "8.1.34",
				"PHP_82_LATEST": "8.2.29",
				"PHP_83_LATEST": "8.3.30",
			},
			expected: "8.3.30",
		},
		{
			name:       "Resolves {PHP_82_LATEST} placeholder",
			phpVersion: "{PHP_82_LATEST}",
			phpVersions: map[string]string{
				"PHP_81_LATEST": "8.1.34",
				"PHP_82_LATEST": "8.2.29",
				"PHP_83_LATEST": "8.3.30",
			},
			expected: "8.2.29",
		},
		{
			name:       "Resolves {PHP_81_LATEST} placeholder",
			phpVersion: "{PHP_81_LATEST}",
			phpVersions: map[string]string{
				"PHP_81_LATEST": "8.1.34",
				"PHP_82_LATEST": "8.2.29",
				"PHP_83_LATEST": "8.3.30",
			},
			expected: "8.1.34",
		},
		{
			name:       "Returns invalid placeholder as-is (for clear error message)",
			phpVersion: "{PHP_99_LATEST}",
			phpVersions: map[string]string{
				"PHP_81_LATEST": "8.1.34",
				"PHP_82_LATEST": "8.2.29",
				"PHP_83_LATEST": "8.3.30",
			},
			expected: "{PHP_99_LATEST}",
		},
		{
			name:       "Returns exact version without placeholder syntax",
			phpVersion: "8.3.21",
			phpVersions: map[string]string{
				"PHP_83_LATEST": "8.3.30",
			},
			expected: "8.3.21",
		},
		{
			name:       "Returns version with partial placeholder syntax (not a placeholder)",
			phpVersion: "PHP_83_LATEST",
			phpVersions: map[string]string{
				"PHP_83_LATEST": "8.3.30",
			},
			expected: "PHP_83_LATEST",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			opts := &options.Options{
				PHPDefault:  "8.1.32",
				PHPVersion:  tt.phpVersion,
				PHPVersions: tt.phpVersions,
			}

			result := opts.GetPHPVersion()
			if result != tt.expected {
				t.Errorf("Expected %s, got %s", tt.expected, result)
			}
		})
	}
}

func TestGetPreprocessCommands(t *testing.T) {
	tests := []struct {
		name     string
		cmds     interface{}
		expected []string
	}{
		{
			name:     "nil returns empty slice",
			cmds:     nil,
			expected: nil,
		},
		{
			name:     "empty string returns empty slice",
			cmds:     "",
			expected: nil,
		},
		{
			name:     "single string command",
			cmds:     "source $HOME/scripts/bootstrap.sh",
			expected: []string{"source $HOME/scripts/bootstrap.sh"},
		},
		{
			name:     "array of strings",
			cmds:     []interface{}{"env", "run_something"},
			expected: []string{"env", "run_something"},
		},
		{
			name:     "array with single string",
			cmds:     []interface{}{"source $HOME/scripts/setup.sh"},
			expected: []string{"source $HOME/scripts/setup.sh"},
		},
		{
			name:     "array of arrays (command with args)",
			cmds:     []interface{}{[]interface{}{"echo", "Hello World"}},
			expected: []string{"echo Hello World"},
		},
		{
			name: "mixed array of strings and arrays",
			cmds: []interface{}{
				"env",
				[]interface{}{"echo", "Hello"},
				"run_script",
			},
			expected: []string{"env", "echo Hello", "run_script"},
		},
		{
			name: "complex Drupal-style bootstrap",
			cmds: []interface{}{
				"source $HOME/scripts/bootstrap.sh",
			},
			expected: []string{"source $HOME/scripts/bootstrap.sh"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			opts := &options.Options{
				AdditionalPreprocessCmds: tt.cmds,
			}

			result := opts.GetPreprocessCommands()

			// Check length
			if len(result) != len(tt.expected) {
				t.Errorf("Expected %d commands, got %d: %v", len(tt.expected), len(result), result)
				return
			}

			// Check each command
			for i, cmd := range result {
				if cmd != tt.expected[i] {
					t.Errorf("Command %d: expected %q, got %q", i, tt.expected[i], cmd)
				}
			}
		})
	}
}

func TestFindStandaloneApp(t *testing.T) {
	tests := []struct {
		name          string
		appStartCmd   string
		createFiles   []string
		expectedApp   string
		expectError   bool
		errorContains string
	}{
		{
			name:        "explicit APP_START_CMD exists",
			appStartCmd: "worker.php",
			createFiles: []string{"worker.php"},
			expectedApp: "worker.php",
			expectError: false,
		},
		{
			name:          "explicit APP_START_CMD not found",
			appStartCmd:   "missing.php",
			createFiles:   []string{},
			expectedApp:   "",
			expectError:   true,
			errorContains: "APP_START_CMD file not found",
		},
		{
			name:        "auto-detect app.php (first priority)",
			appStartCmd: "",
			createFiles: []string{"app.php", "main.php", "run.php", "start.php"},
			expectedApp: "app.php",
			expectError: false,
		},
		{
			name:        "auto-detect main.php (second priority)",
			appStartCmd: "",
			createFiles: []string{"main.php", "run.php", "start.php"},
			expectedApp: "main.php",
			expectError: false,
		},
		{
			name:        "auto-detect run.php (third priority)",
			appStartCmd: "",
			createFiles: []string{"run.php", "start.php"},
			expectedApp: "run.php",
			expectError: false,
		},
		{
			name:        "auto-detect start.php (fourth priority)",
			appStartCmd: "",
			createFiles: []string{"start.php"},
			expectedApp: "start.php",
			expectError: false,
		},
		{
			name:          "no standalone app found",
			appStartCmd:   "",
			createFiles:   []string{"index.php"},
			expectedApp:   "",
			expectError:   true,
			errorContains: "no standalone app found",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create temp directory
			buildDir := t.TempDir()

			// Create test files
			for _, file := range tt.createFiles {
				filePath := filepath.Join(buildDir, file)
				if err := os.WriteFile(filePath, []byte("<?php\n"), 0644); err != nil {
					t.Fatalf("Failed to create test file %s: %v", file, err)
				}
			}

			// Create options with APP_START_CMD
			opts := &options.Options{
				AppStartCmd: tt.appStartCmd,
			}

			// Run FindStandaloneApp
			result, err := opts.FindStandaloneApp(buildDir)

			// Check error expectation
			if tt.expectError {
				if err == nil {
					t.Errorf("Expected error containing %q, but got no error", tt.errorContains)
					return
				}
				if !strings.Contains(err.Error(), tt.errorContains) {
					t.Errorf("Expected error containing %q, got: %v", tt.errorContains, err)
				}
				return
			}

			// Check success case
			if err != nil {
				t.Errorf("Unexpected error: %v", err)
				return
			}

			if result != tt.expectedApp {
				t.Errorf("Expected %q, got %q", tt.expectedApp, result)
			}
		})
	}
}
