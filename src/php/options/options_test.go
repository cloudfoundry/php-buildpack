package options_test

import (
	"os"
	"path/filepath"
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

	// Create defaults directory
	defaultsDir := filepath.Join(bpDir, "defaults")
	if err := os.MkdirAll(defaultsDir, 0755); err != nil {
		t.Fatalf("Failed to create defaults dir: %v", err)
	}

	// Write default options.json with invalid web server
	defaultOpts := `{
		"STACK": "cflinuxfs4",
		"LIBDIR": "lib",
		"WEBDIR": "htdocs",
		"WEB_SERVER": "apache",
		"PHP_VM": "php",
		"ADMIN_EMAIL": "admin@localhost",
		"HTTPD_STRIP": false,
		"HTTPD_MODULES_STRIP": true,
		"NGINX_STRIP": false,
		"PHP_STRIP": false,
		"PHP_MODULES_STRIP": true,
		"PHP_MODULES": [],
		"PHP_EXTENSIONS": [],
		"ZEND_EXTENSIONS": []
	}`
	if err := os.WriteFile(filepath.Join(defaultsDir, "options.json"), []byte(defaultOpts), 0644); err != nil {
		t.Fatalf("Failed to write default options: %v", err)
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
		t.Fatal("Expected error for invalid WEB_SERVER, got nil")
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
