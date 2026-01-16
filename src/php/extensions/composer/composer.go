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
	"github.com/cloudfoundry/php-buildpack/src/php/util"
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

	// Read PHP version requirement from composer.json
	phpVersion, err := e.readPHPVersionFromComposer()
	if err != nil {
		return fmt.Errorf("failed to read PHP version from composer files: %w", err)
	}
	if phpVersion != "" {
		// Also check composer.lock for package PHP constraints
		lockConstraints := e.readPHPConstraintsFromLock()
		selectedVersion := e.pickPHPVersion(ctx, phpVersion, lockConstraints)
		ctx.Set("PHP_VERSION", selectedVersion)
	}

	// Update context with unique extensions
	ctx.Set("PHP_EXTENSIONS", util.UniqueStrings(exts))
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
		if err != nil {
			return "", err
		}
		if version != "" {
			return version, nil
		}
	}

	// Try composer.lock
	if e.lockPath != "" {
		version, err := e.readVersionFromFile(e.lockPath, "platform", "php")
		if err != nil {
			return "", err
		}
		if version != "" {
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

// readPHPConstraintsFromLock reads PHP constraints from all packages in composer.lock
func (e *ComposerExtension) readPHPConstraintsFromLock() []string {
	if e.lockPath == "" {
		return nil
	}

	data, err := os.ReadFile(e.lockPath)
	if err != nil {
		return nil
	}

	var lockData struct {
		Packages []struct {
			Name    string                 `json:"name"`
			Require map[string]interface{} `json:"require"`
		} `json:"packages"`
	}

	if err := json.Unmarshal(data, &lockData); err != nil {
		return nil
	}

	var constraints []string
	for _, pkg := range lockData.Packages {
		if phpConstraint, ok := pkg.Require["php"].(string); ok && phpConstraint != "" {
			constraints = append(constraints, phpConstraint)
		}
	}

	return constraints
}

// pickPHPVersion selects the appropriate PHP version based on requirements
func (e *ComposerExtension) pickPHPVersion(ctx *extensions.Context, requested string, lockConstraints []string) string {
	if requested == "" {
		return ctx.GetString("PHP_VERSION")
	}

	fmt.Printf("-----> Composer requires PHP %s\n", requested)

	// If we have composer.lock constraints, show them
	if len(lockConstraints) > 0 {
		fmt.Printf("       Locked dependencies have %d additional PHP constraints\n", len(lockConstraints))
	}

	// Get all available PHP versions from context
	// Context should have ALL_PHP_VERSIONS set by supply phase
	allVersionsStr := ctx.GetString("ALL_PHP_VERSIONS")
	if allVersionsStr == "" {
		fmt.Println("       Warning: ALL_PHP_VERSIONS not set in context, using default")
		return ctx.GetString("PHP_DEFAULT")
	}

	// Parse available versions (comma-separated)
	availableVersions := strings.Split(allVersionsStr, ",")
	for i := range availableVersions {
		availableVersions[i] = strings.TrimSpace(availableVersions[i])
	}

	// Find the best matching version for composer.json constraint
	selectedVersion := e.matchVersion(requested, availableVersions)
	if selectedVersion == "" {
		fmt.Printf("       Warning: No matching PHP version found for %s, using default\n", requested)
		return ctx.GetString("PHP_DEFAULT")
	}

	// If we have lock constraints, ensure the selected version satisfies ALL of them
	if len(lockConstraints) > 0 {
		// Filter available versions to only those matching ALL constraints (composer.json + lock)
		validVersions := []string{}
		for _, version := range availableVersions {
			// Check composer.json constraint
			if !e.versionMatchesConstraint(version, requested) {
				continue
			}

			// Check all lock constraints
			matchesAll := true
			for _, lockConstraint := range lockConstraints {
				if !e.versionMatchesConstraint(version, lockConstraint) {
					matchesAll = false
					break
				}
			}

			if matchesAll {
				validVersions = append(validVersions, version)
			}
		}

		if len(validVersions) == 0 {
			fmt.Printf("       Warning: No PHP version satisfies all constraints, using default\n")
			return ctx.GetString("PHP_DEFAULT")
		}

		// Find the highest valid version
		selectedVersion = e.findHighestVersion(validVersions)
		fmt.Printf("       Selected PHP version: %s (satisfies all %d constraints)\n", selectedVersion, len(lockConstraints)+1)
	} else {
		fmt.Printf("       Selected PHP version: %s\n", selectedVersion)
	}

	return selectedVersion
}

// matchVersion finds the best matching version for a given constraint
func (e *ComposerExtension) matchVersion(constraint string, availableVersions []string) string {
	// Remove leading/trailing spaces
	constraint = strings.TrimSpace(constraint)

	// Handle compound constraints FIRST (before single operator checks)
	// OR constraint: find highest version matching any constraint
	if strings.Contains(constraint, "||") {
		parts := strings.Split(constraint, "||")
		var matches []string
		for _, part := range parts {
			if result := e.matchVersion(strings.TrimSpace(part), availableVersions); result != "" {
				matches = append(matches, result)
			}
		}
		if len(matches) > 0 {
			return e.findHighestVersion(matches)
		}
		return ""
	}

	// AND constraint (multiple constraints): check all
	// Must check BEFORE single operators, as ">=8.1.0 <8.3.0" contains spaces
	if strings.Contains(constraint, " ") {
		parts := strings.Fields(constraint)
		candidates := availableVersions
		for _, part := range parts {
			newCandidates := []string{}
			for _, v := range candidates {
				if e.versionMatchesConstraint(v, part) {
					newCandidates = append(newCandidates, v)
				}
			}
			candidates = newCandidates
		}
		if len(candidates) > 0 {
			return e.findHighestVersion(candidates)
		}
		return ""
	}

	// Handle single operator constraints
	if strings.HasPrefix(constraint, ">=") {
		// >= constraint: find highest version that is >= requested
		minVersion := strings.TrimSpace(constraint[2:])
		return e.findHighestVersionGTE(minVersion, availableVersions)
	} else if strings.HasPrefix(constraint, ">") {
		// > constraint: find highest version that is > requested
		minVersion := strings.TrimSpace(constraint[1:])
		return e.findHighestVersionGT(minVersion, availableVersions)
	} else if strings.HasPrefix(constraint, "<=") {
		// <= constraint: find highest version that is <= requested
		maxVersion := strings.TrimSpace(constraint[2:])
		return e.findHighestVersionLTE(maxVersion, availableVersions)
	} else if strings.HasPrefix(constraint, "<") {
		// < constraint: find highest version that is < requested
		maxVersion := strings.TrimSpace(constraint[1:])
		return e.findHighestVersionLT(maxVersion, availableVersions)
	} else if strings.HasPrefix(constraint, "^") {
		// ^ constraint: compatible version (same major version)
		baseVersion := strings.TrimSpace(constraint[1:])
		return e.findCompatibleVersion(baseVersion, availableVersions)
	} else if strings.HasPrefix(constraint, "~") {
		// ~ constraint: approximately equivalent (same major.minor)
		baseVersion := strings.TrimSpace(constraint[1:])
		return e.findApproximateVersion(baseVersion, availableVersions)
	} else {
		// Exact version or wildcard
		if strings.Contains(constraint, "*") {
			return e.findWildcardMatch(constraint, availableVersions)
		}
		// Check if exact version exists
		for _, v := range availableVersions {
			if v == constraint {
				return v
			}
		}
	}

	return ""
}

// versionMatchesConstraint checks if a version matches a single constraint
func (e *ComposerExtension) versionMatchesConstraint(version, constraint string) bool {
	constraint = strings.TrimSpace(constraint)

	// Handle OR constraints (||)
	if strings.Contains(constraint, "||") {
		parts := strings.Split(constraint, "||")
		for _, part := range parts {
			if e.versionMatchesConstraint(version, strings.TrimSpace(part)) {
				return true
			}
		}
		return false
	}

	// Handle AND constraints (space-separated)
	if strings.Contains(constraint, " ") {
		parts := strings.Fields(constraint)
		for _, part := range parts {
			if !e.versionMatchesConstraint(version, strings.TrimSpace(part)) {
				return false
			}
		}
		return true
	}

	if strings.HasPrefix(constraint, ">=") {
		minVersion := strings.TrimSpace(constraint[2:])
		return util.CompareVersions(version, minVersion) >= 0
	} else if strings.HasPrefix(constraint, ">") {
		minVersion := strings.TrimSpace(constraint[1:])
		return util.CompareVersions(version, minVersion) > 0
	} else if strings.HasPrefix(constraint, "<=") {
		maxVersion := strings.TrimSpace(constraint[2:])
		return util.CompareVersions(version, maxVersion) <= 0
	} else if strings.HasPrefix(constraint, "<") {
		maxVersion := strings.TrimSpace(constraint[1:])
		return util.CompareVersions(version, maxVersion) < 0
	} else if strings.HasPrefix(constraint, "^") {
		baseVersion := strings.TrimSpace(constraint[1:])
		return e.isCompatible(version, baseVersion)
	} else if strings.HasPrefix(constraint, "~") {
		baseVersion := strings.TrimSpace(constraint[1:])
		return e.isApproximatelyEquivalent(version, baseVersion)
	} else if constraint == version {
		return true
	}

	return false
}

// findHighestVersionGTE finds the highest version >= minVersion
func (e *ComposerExtension) findHighestVersionGTE(minVersion string, versions []string) string {
	var best string
	for _, v := range versions {
		if util.CompareVersions(v, minVersion) >= 0 {
			if best == "" || util.CompareVersions(v, best) > 0 {
				best = v
			}
		}
	}
	return best
}

// findHighestVersionGT finds the highest version > minVersion
func (e *ComposerExtension) findHighestVersionGT(minVersion string, versions []string) string {
	var best string
	for _, v := range versions {
		if util.CompareVersions(v, minVersion) > 0 {
			if best == "" || util.CompareVersions(v, best) > 0 {
				best = v
			}
		}
	}
	return best
}

// findHighestVersionLTE finds the highest version <= maxVersion
func (e *ComposerExtension) findHighestVersionLTE(maxVersion string, versions []string) string {
	var best string
	for _, v := range versions {
		if util.CompareVersions(v, maxVersion) <= 0 {
			if best == "" || util.CompareVersions(v, best) > 0 {
				best = v
			}
		}
	}
	return best
}

// findHighestVersionLT finds the highest version < maxVersion
func (e *ComposerExtension) findHighestVersionLT(maxVersion string, versions []string) string {
	var best string
	for _, v := range versions {
		if util.CompareVersions(v, maxVersion) < 0 {
			if best == "" || util.CompareVersions(v, best) > 0 {
				best = v
			}
		}
	}
	return best
}

// findHighestVersion finds the highest version from a list
func (e *ComposerExtension) findHighestVersion(versions []string) string {
	if len(versions) == 0 {
		return ""
	}
	best := versions[0]
	for _, v := range versions[1:] {
		if util.CompareVersions(v, best) > 0 {
			best = v
		}
	}
	return best
}

// findCompatibleVersion finds the highest compatible version (^ constraint)
func (e *ComposerExtension) findCompatibleVersion(baseVersion string, versions []string) string {
	var best string
	for _, v := range versions {
		if e.isCompatible(v, baseVersion) {
			if best == "" || util.CompareVersions(v, best) > 0 {
				best = v
			}
		}
	}
	return best
}

// findApproximateVersion finds the highest approximately equivalent version (~ constraint)
func (e *ComposerExtension) findApproximateVersion(baseVersion string, versions []string) string {
	var best string
	for _, v := range versions {
		if e.isApproximatelyEquivalent(v, baseVersion) {
			if best == "" || util.CompareVersions(v, best) > 0 {
				best = v
			}
		}
	}
	return best
}

// findWildcardMatch finds versions matching a wildcard pattern
func (e *ComposerExtension) findWildcardMatch(pattern string, versions []string) string {
	// Replace * with empty string to get prefix
	prefix := strings.Replace(pattern, "*", "", -1)
	prefix = strings.TrimSuffix(prefix, ".")

	var best string
	for _, v := range versions {
		if strings.HasPrefix(v, prefix) {
			if best == "" || util.CompareVersions(v, best) > 0 {
				best = v
			}
		}
	}
	return best
}

// isCompatible checks if version is compatible with base (^ constraint)
// Compatible means same major version, and >= base version
func (e *ComposerExtension) isCompatible(version, base string) bool {
	vParts := strings.Split(version, ".")
	bParts := strings.Split(base, ".")

	if len(vParts) < 1 || len(bParts) < 1 {
		return false
	}

	// Must have same major version
	if vParts[0] != bParts[0] {
		return false
	}

	// Must be >= base version
	return util.CompareVersions(version, base) >= 0
}

// isApproximatelyEquivalent checks if version is approximately equivalent to base (~ constraint)
// Approximately equivalent means same major.minor, and >= base version
func (e *ComposerExtension) isApproximatelyEquivalent(version, base string) bool {
	vParts := strings.Split(version, ".")
	bParts := strings.Split(base, ".")

	if len(vParts) < 2 || len(bParts) < 2 {
		return false
	}

	// Must have same major.minor version
	if vParts[0] != bParts[0] || vParts[1] != bParts[1] {
		return false
	}

	// Must be >= base version
	return util.CompareVersions(version, base) >= 0
}

// compareVersions compares two semantic versions
// Returns: -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2

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
	if err := util.CopyFile(phpIniPath, tmpPhpIniPath); err != nil {
		return fmt.Errorf("failed to copy php.ini to TMPDIR: %w", err)
	}

	return nil
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
	compiledModules, err := util.GetCompiledModules(phpBinary, phpLib)
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

func (e *ComposerExtension) loadUserExtensions(ctx *extensions.Context) error {
	return extensions.LoadUserExtensions(ctx, e.buildDir)
}
