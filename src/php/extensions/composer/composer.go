package composer

import (
	"encoding/json"
	"fmt"
	"io"
	"io/ioutil"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strings"

	"github.com/cloudfoundry/libbuildpack"
	"github.com/cloudfoundry/php-buildpack/src/php/config"
	"github.com/cloudfoundry/php-buildpack/src/php/extensions"
)

// ComposerExtension downloads, installs and runs Composer
type ComposerExtension struct {
	jsonPath          string
	lockPath          string
	authPath          string
	buildDir          string
	bpDir             string
	cacheDir          string
	webDir            string
	libDir            string
	tmpDir            string
	detected          bool
	composerHome      string
	composerVendorDir string
}

// Name returns the extension name
func (e *ComposerExtension) Name() string {
	return "composer"
}

// ShouldCompile determines if Composer should be installed
func (e *ComposerExtension) ShouldCompile(ctx *extensions.Context) bool {
	e.buildDir = ctx.GetString("BUILD_DIR")
	e.bpDir = ctx.GetString("BP_DIR")
	e.webDir = ctx.GetString("WEBDIR")

	// Find composer.json and composer.lock
	e.jsonPath = findComposerPath(e.buildDir, e.webDir, "composer.json")
	e.lockPath = findComposerPath(e.buildDir, e.webDir, "composer.lock")
	e.authPath = findComposerPath(e.buildDir, e.webDir, "auth.json")

	e.detected = (e.jsonPath != "" || e.lockPath != "")
	return e.detected
}

// findComposerPath searches for a Composer file in various locations
func findComposerPath(buildDir, webDir, fileName string) string {
	paths := []string{
		filepath.Join(buildDir, fileName),
		filepath.Join(buildDir, webDir, fileName),
	}

	// Check for COMPOSER_PATH environment variable
	if composerPath := os.Getenv("COMPOSER_PATH"); composerPath != "" {
		paths = append(paths,
			filepath.Join(buildDir, composerPath, fileName),
			filepath.Join(buildDir, webDir, composerPath, fileName),
		)
	}

	for _, path := range paths {
		if _, err := os.Stat(path); err == nil {
			return path
		}
	}

	return ""
}

// Configure runs early configuration to set PHP version and extensions
func (e *ComposerExtension) Configure(ctx *extensions.Context) error {
	if !e.detected {
		return nil
	}

	// Read PHP version and extensions from composer files
	var exts []string

	// Include any existing extensions
	if existing := ctx.GetStringSlice("PHP_EXTENSIONS"); existing != nil {
		exts = append(exts, existing...)
	}

	// Add 'openssl' extension (required for Composer)
	exts = append(exts, "openssl")

	// Add platform extensions from composer.json
	if e.jsonPath != "" {
		jsonExts, err := e.readExtensionsFromFile(e.jsonPath)
		if err != nil {
			return fmt.Errorf("failed to read extensions from composer.json: %w", err)
		}
		exts = append(exts, jsonExts...)
	}

	// Add platform extensions from composer.lock
	if e.lockPath != "" {
		lockExts, err := e.readExtensionsFromFile(e.lockPath)
		if err != nil {
			return fmt.Errorf("failed to read extensions from composer.lock: %w", err)
		}
		exts = append(exts, lockExts...)
	}

	// Read PHP version requirement
	phpVersion, err := e.readPHPVersionFromComposer()
	if err == nil && phpVersion != "" {
		selectedVersion := e.pickPHPVersion(ctx, phpVersion)
		ctx.Set("PHP_VERSION", selectedVersion)
	}

	// Update context with unique extensions
	ctx.Set("PHP_EXTENSIONS", uniqueStrings(exts))
	ctx.Set("PHP_VM", "php")

	return nil
}

// readExtensionsFromFile extracts ext-* requirements from composer files
func (e *ComposerExtension) readExtensionsFromFile(path string) ([]string, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}

	var exts []string

	// Match "require" sections and extract ext-* entries
	reqPattern := regexp.MustCompile(`"require"\s*:\s*\{([^}]*)\}`)
	extPattern := regexp.MustCompile(`"ext-([^"]+)"`)

	reqMatches := reqPattern.FindAllStringSubmatch(string(data), -1)
	for _, reqMatch := range reqMatches {
		if len(reqMatch) > 1 {
			extMatches := extPattern.FindAllStringSubmatch(reqMatch[1], -1)
			for _, extMatch := range extMatches {
				if len(extMatch) > 1 {
					exts = append(exts, extMatch[1])
				}
			}
		}
	}

	return exts, nil
}

// readPHPVersionFromComposer reads PHP version requirement
func (e *ComposerExtension) readPHPVersionFromComposer() (string, error) {
	// Try composer.json first
	if e.jsonPath != "" {
		version, err := e.readVersionFromFile(e.jsonPath, "require", "php")
		if err == nil && version != "" {
			return version, nil
		}
	}

	// Try composer.lock
	if e.lockPath != "" {
		version, err := e.readVersionFromFile(e.lockPath, "platform", "php")
		if err == nil && version != "" {
			return version, nil
		}
	}

	return "", nil
}

// readVersionFromFile reads a version constraint from a JSON file
func (e *ComposerExtension) readVersionFromFile(path, section, key string) (string, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return "", err
	}

	var parsed map[string]interface{}
	if err := json.Unmarshal(data, &parsed); err != nil {
		return "", fmt.Errorf("invalid JSON in %s: %w", filepath.Base(path), err)
	}

	if sectionData, ok := parsed[section].(map[string]interface{}); ok {
		if value, ok := sectionData[key].(string); ok {
			return value, nil
		}
	}

	return "", nil
}

// pickPHPVersion selects the appropriate PHP version based on requirements
func (e *ComposerExtension) pickPHPVersion(ctx *extensions.Context, requested string) string {
	if requested == "" {
		return ctx.GetString("PHP_VERSION")
	}

	// TODO: Implement proper semantic version matching
	// For now, return the default version or requested if valid
	// The Python version uses node-semver library for this

	fmt.Printf("-----> Composer requires PHP %s\n", requested)

	// Simplified version selection - in production this would use semver matching
	// against ALL_PHP_VERSIONS from context
	return ctx.GetString("PHP_DEFAULT")
}

// Compile downloads and runs Composer
func (e *ComposerExtension) Compile(ctx *extensions.Context, installer *extensions.Installer) error {
	if !e.detected {
		return nil
	}

	e.cacheDir = ctx.GetString("CACHE_DIR")
	e.libDir = ctx.GetString("LIBDIR")
	e.tmpDir = ctx.GetString("TMPDIR")
	e.composerHome = filepath.Join(e.cacheDir, "composer")

	// Get COMPOSER_VENDOR_DIR from context
	e.composerVendorDir = ctx.GetString("COMPOSER_VENDOR_DIR")
	if e.composerVendorDir == "" {
		// Default to LIBDIR/vendor if not specified
		e.composerVendorDir = filepath.Join(e.libDir, "vendor")
	}

	// Clean old cache directory
	e.cleanCacheDir()

	// Move local vendor folder if it exists
	if err := e.moveLocalVendorFolder(); err != nil {
		return fmt.Errorf("failed to move vendor folder: %w", err)
	}

	// Install PHP (required for Composer to run)
	fmt.Println("-----> Installing PHP for Composer")
	if err := installer.Package("php"); err != nil {
		return fmt.Errorf("failed to install PHP: %w", err)
	}

	// Setup PHP configuration (config files + process extensions in php.ini)
	if err := e.setupPHPConfig(ctx); err != nil {
		return fmt.Errorf("failed to setup PHP config: %w", err)
	}

	// Install Composer itself
	if err := e.installComposer(ctx, installer); err != nil {
		return fmt.Errorf("failed to install Composer: %w", err)
	}

	// Move composer files to build directory root
	e.moveComposerFilesToRoot()

	// Sanity check for composer.lock
	if _, err := os.Stat(filepath.Join(e.buildDir, "composer.lock")); os.IsNotExist(err) {
		msg := "PROTIP: Include a `composer.lock` file with your application! " +
			"This will make sure the exact same version of dependencies are used " +
			"when you deploy to CloudFoundry."
		fmt.Printf("-----> %s\n", msg)
	}

	// Run composer install
	if err := e.runComposer(ctx); err != nil {
		return fmt.Errorf("failed to run composer: %w", err)
	}

	return nil
}

// cleanCacheDir removes old cache directory if needed
func (e *ComposerExtension) cleanCacheDir() {
	cacheDir := filepath.Join(e.composerHome, "cache")
	if _, err := os.Stat(cacheDir); os.IsNotExist(err) {
		// Old style cache exists, remove it
		os.RemoveAll(e.composerHome)
	}
}

// moveLocalVendorFolder moves existing vendor directory to configured location
func (e *ComposerExtension) moveLocalVendorFolder() error {
	vendorPath := filepath.Join(e.buildDir, e.webDir, "vendor")
	if _, err := os.Stat(vendorPath); os.IsNotExist(err) {
		return nil
	}

	fmt.Printf("-----> Moving existing vendor directory to %s\n", e.composerVendorDir)

	destPath := filepath.Join(e.buildDir, e.composerVendorDir)

	// Create parent directory if it doesn't exist
	destDir := filepath.Dir(destPath)
	if err := os.MkdirAll(destDir, 0755); err != nil {
		return fmt.Errorf("failed to create vendor parent directory: %w", err)
	}

	if err := os.Rename(vendorPath, destPath); err != nil {
		return fmt.Errorf("failed to move vendor directory: %w", err)
	}

	return nil
}

// installComposer downloads and installs Composer
func (e *ComposerExtension) installComposer(ctx *extensions.Context, installer *extensions.Installer) error {
	composerVersion := ctx.GetString("COMPOSER_VERSION")
	dest := filepath.Join(e.buildDir, "php", "bin", "composer.phar")

	if composerVersion == "latest" {
		// Check if we're in a cached buildpack
		depsPath := filepath.Join(e.bpDir, "dependencies")
		if _, err := os.Stat(depsPath); err == nil {
			return fmt.Errorf("\"COMPOSER_VERSION\": \"latest\" is not supported in the cached buildpack. " +
				"Please vendor your preferred version of composer with your app, or use the provided default composer version")
		}

		// Download latest composer from getcomposer.org
		url := "https://getcomposer.org/composer.phar"

		fmt.Println("-----> Downloading latest Composer")
		if err := e.downloadFile(url, dest); err != nil {
			return fmt.Errorf("failed to download latest composer: %w", err)
		}
	} else {
		// Install from manifest using InstallDependency (supports cached buildpack)
		fmt.Printf("-----> Installing composer %s\n", composerVersion)

		// Create a temporary directory for the composer download
		tmpDir, err := ioutil.TempDir("", "composer-install")
		if err != nil {
			return fmt.Errorf("failed to create temp dir: %w", err)
		}
		defer os.RemoveAll(tmpDir)

		// Use InstallDependency to download composer (works with cached buildpack)
		dep := libbuildpack.Dependency{
			Name:    "composer",
			Version: composerVersion,
		}
		if err := installer.InstallDependency(dep, tmpDir); err != nil {
			return fmt.Errorf("failed to install composer from manifest: %w", err)
		}

		// Find the downloaded .phar file (e.g., composer_2.8.8_linux_noarch_cflinuxfs4_abc123.phar)
		files, err := ioutil.ReadDir(tmpDir)
		if err != nil {
			return fmt.Errorf("failed to read temp dir: %w", err)
		}

		var pharFile string
		for _, f := range files {
			if strings.HasSuffix(f.Name(), ".phar") {
				pharFile = filepath.Join(tmpDir, f.Name())
				break
			}
		}

		if pharFile == "" {
			return fmt.Errorf("no .phar file found after composer installation")
		}

		// Create destination directory
		if err := os.MkdirAll(filepath.Dir(dest), 0755); err != nil {
			return fmt.Errorf("failed to create composer bin dir: %w", err)
		}

		// Move the .phar file to the correct location
		if err := os.Rename(pharFile, dest); err != nil {
			return fmt.Errorf("failed to move composer.phar: %w", err)
		}

		// Make executable
		if err := os.Chmod(dest, 0755); err != nil {
			return fmt.Errorf("failed to make composer.phar executable: %w", err)
		}
	}

	return nil
}

// downloadFile downloads a file from a URL
func (e *ComposerExtension) downloadFile(url, dest string) error {
	resp, err := http.Get(url)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("download failed with status: %s", resp.Status)
	}

	// Create destination directory
	if err := os.MkdirAll(filepath.Dir(dest), 0755); err != nil {
		return err
	}

	// Create file
	file, err := os.Create(dest)
	if err != nil {
		return err
	}
	defer file.Close()

	// Copy data
	if _, err := io.Copy(file, resp.Body); err != nil {
		return err
	}

	// Make executable
	return os.Chmod(dest, 0755)
}

// moveComposerFilesToRoot moves composer files to build directory root
func (e *ComposerExtension) moveComposerFilesToRoot() {
	e.moveFileToRoot(e.jsonPath, "composer.json")
	e.moveFileToRoot(e.lockPath, "composer.lock")
	e.moveFileToRoot(e.authPath, "auth.json")
}

// moveFileToRoot moves a file to the build directory root if needed
func (e *ComposerExtension) moveFileToRoot(filePath, fileName string) {
	if filePath == "" {
		return
	}

	destPath := filepath.Join(e.buildDir, fileName)
	if filePath == destPath {
		return // Already in root
	}

	if err := os.Rename(filePath, destPath); err != nil {
		fmt.Printf("-----> WARNING: Failed to move %s: %v\n", fileName, err)
	}
}

// runComposer executes composer install
func (e *ComposerExtension) runComposer(ctx *extensions.Context) error {
	phpPath := filepath.Join(e.buildDir, "php", "bin", "php")
	composerPath := filepath.Join(e.buildDir, "php", "bin", "composer.phar")

	// Check if buildpack is cached (has dependencies directory)
	depsPath := filepath.Join(e.bpDir, "dependencies")
	_, hasDeps := os.Stat(depsPath)

	// Set up GitHub OAuth token if provided and not cached
	tokenValid := false
	if os.IsNotExist(hasDeps) {
		if token := os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"); token != "" {
			tokenValid = e.setupGitHubToken(phpPath, composerPath, token)
		}

		// Check GitHub rate limit
		e.checkGitHubRateLimit(tokenValid)
	}

	// Get Composer install options
	installOpts := ctx.GetStringSlice("COMPOSER_INSTALL_OPTIONS")
	if installOpts == nil {
		installOpts = []string{"--no-interaction", "--no-dev"}
	}

	// Install global Composer dependencies if specified
	globalDeps := ctx.GetStringSlice("COMPOSER_INSTALL_GLOBAL")
	if len(globalDeps) > 0 {
		fmt.Println("-----> Installing global Composer dependencies")
		args := []string{"global", "require", "--no-progress"}
		args = append(args, globalDeps...)
		if err := e.runComposerCommand(ctx, phpPath, composerPath, args...); err != nil {
			return fmt.Errorf("failed to install global dependencies: %w", err)
		}
	}

	// Run composer install
	fmt.Println("-----> Installing Composer dependencies")
	args := []string{"install", "--no-progress"}
	args = append(args, installOpts...)

	if err := e.runComposerCommand(ctx, phpPath, composerPath, args...); err != nil {
		fmt.Println("-----> Composer command failed")
		return fmt.Errorf("composer install failed: %w", err)
	}

	return nil
}

// setupPHPConfig sets up PHP configuration files and processes extensions
func (e *ComposerExtension) setupPHPConfig(ctx *extensions.Context) error {
	phpInstallDir := filepath.Join(e.buildDir, "php")
	phpEtcDir := filepath.Join(phpInstallDir, "etc")

	// Get PHP version from context to determine config path
	phpVersion := ctx.GetString("PHP_VERSION")
	if phpVersion == "" {
		return fmt.Errorf("PHP_VERSION not set in context")
	}

	// Extract major.minor version (e.g., "8.1.32" -> "8.1")
	versionParts := strings.Split(phpVersion, ".")
	if len(versionParts) < 2 {
		return fmt.Errorf("invalid PHP version format: %s", phpVersion)
	}
	majorMinor := fmt.Sprintf("%s.%s", versionParts[0], versionParts[1])
	phpConfigPath := fmt.Sprintf("php/%s.x", majorMinor)

	// Extract PHP config files from embedded defaults
	if err := config.ExtractConfig(phpConfigPath, phpEtcDir); err != nil {
		return fmt.Errorf("failed to extract PHP config: %w", err)
	}

	// Create php.ini.d directory for extension configs
	phpIniDir := filepath.Join(phpEtcDir, "php.ini.d")
	if err := os.MkdirAll(phpIniDir, 0755); err != nil {
		return fmt.Errorf("failed to create php.ini.d directory: %w", err)
	}

	// Process php.ini to replace extension placeholders
	phpIniPath := filepath.Join(phpEtcDir, "php.ini")
	if err := e.processPhpIni(ctx, phpIniPath); err != nil {
		return fmt.Errorf("failed to process php.ini: %w", err)
	}

	// Copy processed php.ini to TMPDIR for Composer to use
	// This matches the Python buildpack behavior where PHPRC points to TMPDIR
	tmpPhpIniPath := filepath.Join(e.tmpDir, "php.ini")
	if err := e.copyFile(phpIniPath, tmpPhpIniPath); err != nil {
		return fmt.Errorf("failed to copy php.ini to TMPDIR: %w", err)
	}

	return nil
}

// getCompiledModules returns a list of built-in PHP modules by running `php -m`
func getCompiledModules(phpBinPath, phpLibPath string) (map[string]bool, error) {
	cmd := exec.Command(phpBinPath, "-m")
	// Set LD_LIBRARY_PATH so php binary can find its shared libraries
	env := os.Environ()
	env = append(env, fmt.Sprintf("LD_LIBRARY_PATH=%s", phpLibPath))
	cmd.Env = env

	output, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("failed to run php -m: %w", err)
	}

	// Parse output - skip header lines and empty lines
	compiledModules := make(map[string]bool)
	skipLines := map[string]bool{
		"[PHP Modules]":  true,
		"[Zend Modules]": true,
	}

	for _, line := range strings.Split(string(output), "\n") {
		line = strings.TrimSpace(line)
		if line != "" && !skipLines[line] {
			// Store lowercase version for case-insensitive comparison
			compiledModules[strings.ToLower(line)] = true
		}
	}

	return compiledModules, nil
}

// processPhpIni processes php.ini to replace extension placeholders with actual extension directives
func (e *ComposerExtension) processPhpIni(ctx *extensions.Context, phpIniPath string) error {
	// Read the php.ini file
	content, err := os.ReadFile(phpIniPath)
	if err != nil {
		return fmt.Errorf("failed to read php.ini: %w", err)
	}

	phpIniContent := string(content)

	// Get PHP extensions from context
	phpExtensions := ctx.GetStringSlice("PHP_EXTENSIONS")
	zendExtensions := ctx.GetStringSlice("ZEND_EXTENSIONS")

	// Skip certain extensions that should not be in php.ini (they're CLI-only or built-in)
	skipExtensions := map[string]bool{
		"cli":  true,
		"pear": true,
		"cgi":  true,
	}

	// Find PHP extensions directory to validate requested extensions
	phpExtDir := ""
	phpLibDir := filepath.Join(e.buildDir, "php", "lib", "php", "extensions")
	if entries, err := os.ReadDir(phpLibDir); err == nil {
		for _, entry := range entries {
			if entry.IsDir() && strings.HasPrefix(entry.Name(), "no-debug-non-zts-") {
				phpExtDir = filepath.Join(phpLibDir, entry.Name())
				break
			}
		}
	}

	// Get list of built-in PHP modules (extensions compiled into PHP core)
	phpBinary := filepath.Join(e.buildDir, "php", "bin", "php")
	phpLib := filepath.Join(e.buildDir, "php", "lib")
	compiledModules, err := getCompiledModules(phpBinary, phpLib)
	if err != nil {
		fmt.Printf("       WARNING: Failed to get compiled PHP modules: %v\n", err)
		compiledModules = make(map[string]bool) // Continue without built-in module list
	}

	// Build extension directives and validate extensions
	var extensionLines []string
	for _, ext := range phpExtensions {
		if skipExtensions[ext] {
			continue
		}

		// Check if extension .so file exists
		if phpExtDir != "" {
			extFile := filepath.Join(phpExtDir, ext+".so")
			exists := false
			if info, err := os.Stat(extFile); err == nil && !info.IsDir() {
				exists = true
			}

			if exists {
				// Extension has .so file, add to php.ini
				extensionLines = append(extensionLines, fmt.Sprintf("extension=%s.so", ext))
			} else if !compiledModules[strings.ToLower(ext)] {
				// Extension doesn't have .so file AND is not built-in -> warn
				fmt.Printf("The extension '%s' is not provided by this buildpack.\n", ext)
			}
			// If it's built-in (no .so but in compiled modules), silently skip - it's already available
		}
	}
	extensionsString := strings.Join(extensionLines, "\n")

	// Build zend extension directives
	var zendExtensionLines []string
	for _, ext := range zendExtensions {
		zendExtensionLines = append(zendExtensionLines, fmt.Sprintf("zend_extension=\"%s.so\"", ext))
	}
	zendExtensionsString := strings.Join(zendExtensionLines, "\n")

	// Replace placeholders
	phpIniContent = strings.ReplaceAll(phpIniContent, "#{PHP_EXTENSIONS}", extensionsString)
	phpIniContent = strings.ReplaceAll(phpIniContent, "#{ZEND_EXTENSIONS}", zendExtensionsString)

	// Replace path placeholders (@{HOME}, @{TMPDIR}, #{LIBDIR})
	// @{HOME} should be the build directory, not build_dir/php
	// The template already has paths like @{HOME}/php/lib/...
	phpIniContent = strings.ReplaceAll(phpIniContent, "@{HOME}", e.buildDir)
	phpIniContent = strings.ReplaceAll(phpIniContent, "@{TMPDIR}", e.tmpDir)
	phpIniContent = strings.ReplaceAll(phpIniContent, "#{LIBDIR}", e.libDir)

	// Fix extension_dir to use the actual discovered path
	// During Composer phase, PHP is installed in BUILD_DIR/php
	// The phpExtDir variable already contains the correct full path
	if phpExtDir != "" {
		// Find and replace the extension_dir line with the actual path
		lines := strings.Split(phpIniContent, "\n")
		for i, line := range lines {
			trimmed := strings.TrimSpace(line)
			if strings.HasPrefix(trimmed, "extension_dir") && !strings.HasPrefix(trimmed, ";") {
				// This is the active extension_dir line - replace it with actual path
				lines[i] = fmt.Sprintf("extension_dir = \"%s\"", phpExtDir)
				break
			}
		}
		phpIniContent = strings.Join(lines, "\n")
	}

	// Write back to php.ini
	if err := os.WriteFile(phpIniPath, []byte(phpIniContent), 0644); err != nil {
		return fmt.Errorf("failed to write php.ini: %w", err)
	}

	fmt.Printf("       Configured PHP with %d extensions\n", len(extensionLines))
	return nil
}

// setupGitHubToken configures GitHub OAuth token for Composer
func (e *ComposerExtension) setupGitHubToken(phpPath, composerPath, token string) bool {
	if !e.isValidGitHubToken(token) {
		fmt.Println("-----> The GitHub OAuth token supplied from $COMPOSER_GITHUB_OAUTH_TOKEN is invalid")
		return false
	}

	fmt.Println("-----> Using custom GitHub OAuth token in $COMPOSER_GITHUB_OAUTH_TOKEN")

	// Run: composer config -g github-oauth.github.com TOKEN
	cmd := exec.Command(phpPath, composerPath, "config", "-g", "github-oauth.github.com", token)
	cmd.Dir = e.buildDir
	cmd.Env = e.buildComposerEnv()
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	if err := cmd.Run(); err != nil {
		fmt.Printf("-----> WARNING: Failed to configure GitHub token: %v\n", err)
		return false
	}

	return true
}

// isValidGitHubToken checks if a GitHub token is valid
func (e *ComposerExtension) isValidGitHubToken(token string) bool {
	req, err := http.NewRequest("GET", "https://api.github.com/rate_limit", nil)
	if err != nil {
		return false
	}

	req.Header.Set("Authorization", "token "+token)

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return false
	}
	defer resp.Body.Close()

	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return false
	}

	_, hasResources := result["resources"]
	return hasResources
}

// checkGitHubRateLimit checks if GitHub API rate limit is exceeded
func (e *ComposerExtension) checkGitHubRateLimit(hasValidToken bool) {
	var req *http.Request
	var err error

	if hasValidToken {
		token := os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN")
		req, err = http.NewRequest("GET", "https://api.github.com/rate_limit", nil)
		if err != nil {
			return
		}
		req.Header.Set("Authorization", "token "+token)
	} else {
		req, err = http.NewRequest("GET", "https://api.github.com/rate_limit", nil)
		if err != nil {
			return
		}
	}

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return
	}
	defer resp.Body.Close()

	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return
	}

	if rate, ok := result["rate"].(map[string]interface{}); ok {
		if remaining, ok := rate["remaining"].(float64); ok && remaining <= 0 {
			fmt.Println("-----> WARNING: The GitHub API rate limit has been exceeded. " +
				"Composer will continue by downloading from source, which might result in slower downloads. " +
				"You can increase your rate limit with a GitHub OAuth token. " +
				"Please obtain a GitHub OAuth token by registering your application at " +
				"https://github.com/settings/applications/new. " +
				"Then set COMPOSER_GITHUB_OAUTH_TOKEN in your environment to the value of this token.")
		}
	}
}

// runComposerCommand runs a composer command with proper environment
func (e *ComposerExtension) runComposerCommand(ctx *extensions.Context, phpPath, composerPath string, args ...string) error {
	cmdArgs := []string{composerPath}
	cmdArgs = append(cmdArgs, args...)

	cmd := exec.Command(phpPath, cmdArgs...)
	cmd.Dir = e.buildDir
	cmd.Env = e.buildComposerEnv()
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	return cmd.Run()
}

// buildComposerEnv builds the environment variables for running Composer
func (e *ComposerExtension) buildComposerEnv() []string {
	env := os.Environ()

	// Add Composer-specific variables
	vendorDir := filepath.Join(e.buildDir, e.composerVendorDir)
	binDir := filepath.Join(e.buildDir, "php", "bin")
	cacheDir := filepath.Join(e.composerHome, "cache")

	env = append(env,
		fmt.Sprintf("COMPOSER_HOME=%s", e.composerHome),
		fmt.Sprintf("COMPOSER_VENDOR_DIR=%s", vendorDir),
		fmt.Sprintf("COMPOSER_BIN_DIR=%s", binDir),
		fmt.Sprintf("COMPOSER_CACHE_DIR=%s", cacheDir),
		fmt.Sprintf("LD_LIBRARY_PATH=%s", filepath.Join(e.buildDir, "php", "lib")),
		fmt.Sprintf("PHPRC=%s", e.tmpDir),
	)

	return env
}

// PreprocessCommands returns commands to run before app starts (none for Composer)
func (e *ComposerExtension) PreprocessCommands(ctx *extensions.Context) ([]string, error) {
	return nil, nil
}

// ServiceCommands returns long-running service commands (none for Composer)
func (e *ComposerExtension) ServiceCommands(ctx *extensions.Context) (map[string]string, error) {
	return nil, nil
}

// ServiceEnvironment returns environment variables for runtime (none for Composer)
func (e *ComposerExtension) ServiceEnvironment(ctx *extensions.Context) (map[string]string, error) {
	return nil, nil
}

// copyFile copies a file from src to dst
func (e *ComposerExtension) copyFile(src, dst string) error {
	sourceFile, err := os.Open(src)
	if err != nil {
		return err
	}
	defer sourceFile.Close()

	destFile, err := os.Create(dst)
	if err != nil {
		return err
	}
	defer destFile.Close()

	_, err = io.Copy(destFile, sourceFile)
	return err
}

// uniqueStrings returns a slice with duplicate strings removed
func uniqueStrings(input []string) []string {
	seen := make(map[string]bool)
	result := []string{}

	for _, item := range input {
		if !seen[item] {
			seen[item] = true
			result = append(result, item)
		}
	}

	return result
}
