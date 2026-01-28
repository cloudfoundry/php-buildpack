package finalize

import (
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"

	"github.com/cloudfoundry/libbuildpack"
	"github.com/cloudfoundry/php-buildpack/src/php/extensions"
	"github.com/cloudfoundry/php-buildpack/src/php/options"
)

// Stager interface abstracts buildpack staging operations
type Stager interface {
	BuildDir() string
	DepDir() string
	DepsIdx() string
	WriteProfileD(scriptName, scriptContents string) error
	SetLaunchEnvironment() error
}

// Manifest interface abstracts buildpack manifest operations
type Manifest interface {
	IsCached() bool
	AllDependencyVersions(depName string) []string
	DefaultVersion(depName string) (libbuildpack.Dependency, error)
}

// Command interface abstracts command execution
type Command interface {
	Execute(dir string, stdout io.Writer, stderr io.Writer, program string, args ...string) error
}

// Finalizer contains the buildpack finalize phase logic
type Finalizer struct {
	Manifest Manifest
	Stager   Stager
	Command  Command
	Log      *libbuildpack.Logger
	Logfile  *os.File
	Registry *extensions.Registry
}

// Run executes the PHP buildpack finalize phase
func Run(f *Finalizer) error {
	f.Log.BeginStep("Finalizing PHP")

	// Run extension finalize phases if registry is provided
	if f.Registry != nil {
		ctx, err := f.createExtensionContext()
		if err != nil {
			f.Log.Error("Failed to create extension context: %v", err)
			return err
		}

		// Collect preprocess commands from extensions
		preprocessCmds, err := f.Registry.GetPreprocessCommands(ctx)
		if err != nil {
			f.Log.Error("Failed to get preprocess commands: %v", err)
			return err
		}

		// Execute preprocess commands
		for _, cmd := range preprocessCmds {
			f.Log.Info("Running preprocess command: %s", cmd)
			if err := f.Command.Execute(f.Stager.BuildDir(), f.Log.Output(), f.Log.Output(), "bash", "-c", cmd); err != nil {
				f.Log.Error("Preprocess command failed: %v", err)
				return err
			}
		}

		// Collect service commands from extensions
		serviceCmds, err := f.Registry.GetServiceCommands(ctx)
		if err != nil {
			f.Log.Error("Failed to get service commands: %v", err)
			return err
		}

		// Write service commands to profile.d
		if len(serviceCmds) > 0 {
			if err := f.writeServiceCommands(serviceCmds); err != nil {
				f.Log.Error("Failed to write service commands: %v", err)
				return err
			}
		}

		// Collect service environment variables from extensions
		serviceEnv, err := f.Registry.GetServiceEnvironment(ctx)
		if err != nil {
			f.Log.Error("Failed to get service environment: %v", err)
			return err
		}

		// Write service environment variables
		if len(serviceEnv) > 0 {
			if err := f.writeServiceEnvironment(serviceEnv); err != nil {
				f.Log.Error("Failed to write service environment: %v", err)
				return err
			}
		}
	}

	// Load options for config processing
	bpDir := os.Getenv("BP_DIR")
	if bpDir == "" {
		return fmt.Errorf("BP_DIR environment variable not set")
	}
	opts, err := options.LoadOptions(bpDir, f.Stager.BuildDir(), f.Manifest, f.Log)
	if err != nil {
		return fmt.Errorf("could not load options: %v", err)
	}

	// Process all config files (replace build-time placeholders)
	if err := f.ProcessConfigs(opts); err != nil {
		f.Log.Error("Error processing configs: %v", err)
		return err
	}

	// Create start script
	if err := f.CreateStartScript(); err != nil {
		f.Log.Error("Error creating start script: %v", err)
		return err
	}

	// Create pre-start wrapper script
	if err := f.writePreStartScript(); err != nil {
		f.Log.Error("Error creating pre-start script: %v", err)
		return err
	}

	// Create PHP-FPM runtime directories
	if err := f.CreatePHPRuntimeDirectories(); err != nil {
		f.Log.Error("Error creating PHP runtime directories: %v", err)
		return err
	}

	// Create .profile.d script to set up PHP environment (PATH, etc)
	if err := f.CreatePHPEnvironmentScript(); err != nil {
		f.Log.Error("Error creating PHP environment script: %v", err)
		return err
	}

	// Copy profile.d scripts from deps to BUILD_DIR/.profile.d
	// This ensures CF launcher sources them at runtime
	if err := f.Stager.SetLaunchEnvironment(); err != nil {
		f.Log.Error("Error setting launch environment: %v", err)
		return err
	}

	// Set up process types (web, worker, etc)
	if err := f.SetupProcessTypes(); err != nil {
		f.Log.Error("Error setting up process types: %v", err)
		return err
	}

	// Write release YAML file for bin/release to consume
	tmpDir := filepath.Join(f.Stager.BuildDir(), "tmp")
	if err := os.MkdirAll(tmpDir, 0755); err != nil {
		return fmt.Errorf("failed to create tmp directory: %w", err)
	}

	releaseYamlPath := filepath.Join(tmpDir, "php-buildpack-release-step.yml")
	yamlContent := `---
default_process_types:
  web: $HOME/.bp/bin/start
`
	if err := os.WriteFile(releaseYamlPath, []byte(yamlContent), 0644); err != nil {
		return fmt.Errorf("failed to write release YAML: %w", err)
	}

	f.Log.Info("PHP buildpack finalize phase complete")
	return nil
}

// createExtensionContext creates an extension context from the buildpack state
func (f *Finalizer) createExtensionContext() (*extensions.Context, error) {
	ctx, err := extensions.NewContext()
	if err != nil {
		return nil, fmt.Errorf("failed to create context: %w", err)
	}

	// Set buildpack directories
	ctx.Set("BUILD_DIR", f.Stager.BuildDir())
	ctx.Set("BP_DIR", os.Getenv("BP_DIR"))
	ctx.Set("DEPS_DIR", f.Stager.DepDir())
	ctx.Set("DEPS_IDX", f.Stager.DepsIdx())

	return ctx, nil
}

// writeServiceCommands writes service commands to a shell script
func (f *Finalizer) writeServiceCommands(commands map[string]string) error {
	scriptContent := "#!/usr/bin/env bash\n"
	scriptContent += "# Extension service commands\n\n"

	for name, cmd := range commands {
		scriptContent += fmt.Sprintf("# %s\n", name)
		scriptContent += fmt.Sprintf("%s &\n\n", cmd)
	}

	return f.Stager.WriteProfileD("extension-services.sh", scriptContent)
}

// writeServiceEnvironment writes service environment variables
func (f *Finalizer) writeServiceEnvironment(env map[string]string) error {
	scriptContent := "#!/usr/bin/env bash\n"
	scriptContent += "# Extension environment variables\n\n"

	for key, val := range env {
		scriptContent += fmt.Sprintf("export %s='%s'\n", key, val)
	}

	return f.Stager.WriteProfileD("extension-env.sh", scriptContent)
}

// CreatePHPEnvironmentScript creates a .profile.d script to set up PHP environment
func (f *Finalizer) CreatePHPEnvironmentScript() error {
	depsIdx := f.Stager.DepsIdx()

	// Create script that adds PHP bin directory to PATH
	// DEPS_DIR defaults to /home/vcap/deps in Cloud Foundry runtime
	scriptContent := fmt.Sprintf(`#!/usr/bin/env bash
# Add PHP binaries to PATH for CLI usage (e.g., CakePHP migrations, Laravel artisan)
: ${DEPS_DIR:=/home/vcap/deps}
export DEPS_DIR
export PATH="$DEPS_DIR/%s/php/bin:$DEPS_DIR/%s/php/sbin:$PATH"
`, depsIdx, depsIdx)

	return f.Stager.WriteProfileD("php-env.sh", scriptContent)
}

// ProcessConfigs replaces build-time placeholders in all config files
func (f *Finalizer) ProcessConfigs(opts *options.Options) error {
	buildDir := f.Stager.BuildDir()
	depsIdx := f.Stager.DepsIdx()
	depDir := f.Stager.DepDir()

	// Determine web server
	webServer := opts.WebServer
	webDir := opts.WebDir
	if webDir == "" {
		webDir = "htdocs"
	}
	libDir := opts.LibDir
	if libDir == "" {
		libDir = "lib"
	}

	// Determine PHP-FPM listen address first (needed for both PHP and web server configs)
	phpFpmListen := "127.0.0.1:9000" // Default TCP
	if webServer == "nginx" {
		// Nginx uses Unix socket for better performance
		phpFpmListen = filepath.Join("/home/vcap/deps", depsIdx, "php", "var", "run", "php-fpm.sock")
	}

	// Process PHP configs - use deps directory for @{HOME}
	phpEtcDir := filepath.Join(depDir, "php", "etc")
	if exists, _ := libbuildpack.FileExists(phpEtcDir); exists {
		depsPath := filepath.Join("/home/vcap/deps", depsIdx)
		phpReplacements := map[string]string{
			"@{HOME}":           depsPath,
			"@{DEPS_DIR}":       "/home/vcap/deps", // For fpm.d include directive
			"@{LIBDIR}":         libDir,
			"@{PHP_FPM_LISTEN}": phpFpmListen,
			// @{TMPDIR} is converted to ${TMPDIR} for shell expansion at runtime
			// This allows users to customize TMPDIR via environment variable
			"@{TMPDIR}": "${TMPDIR}",
		}

		// Process fpm.d directory separately with app HOME (not deps HOME)
		// This is because fpm.d configs contain environment variables for PHP scripts
		// which run in the app context, not the deps context
		fpmDDir := filepath.Join(phpEtcDir, "fpm.d")

		// Process PHP configs, excluding fpm.d which we'll process separately
		f.Log.Debug("Processing PHP configs in %s with replacements: %v (excluding fpm.d)", phpEtcDir, phpReplacements)
		if err := f.replacePlaceholdersInDirExclude(phpEtcDir, phpReplacements, []string{fpmDDir}); err != nil {
			return fmt.Errorf("failed to process PHP configs: %w", err)
		}

		if exists, _ := libbuildpack.FileExists(fpmDDir); exists {
			fpmDReplacements := map[string]string{
				"@{HOME}":   "/home/vcap/app", // Use app HOME for fpm.d env vars
				"@{WEBDIR}": webDir,
				"@{LIBDIR}": libDir,
				"@{TMPDIR}": "${TMPDIR}",
			}

			f.Log.Debug("Processing fpm.d configs in %s with replacements: %v", fpmDDir, fpmDReplacements)
			if err := f.replacePlaceholdersInDir(fpmDDir, fpmDReplacements); err != nil {
				return fmt.Errorf("failed to process fpm.d configs: %w", err)
			}
		}
	}

	// Process web server configs - use app directory for ${HOME}
	appReplacements := map[string]string{
		"@{WEBDIR}":         webDir,
		"@{LIBDIR}":         libDir,
		"@{PHP_FPM_LISTEN}": phpFpmListen,
	}

	// Process HTTPD configs
	if webServer == "httpd" {
		httpdConfDir := filepath.Join(buildDir, "httpd", "conf")
		if exists, _ := libbuildpack.FileExists(httpdConfDir); exists {
			f.Log.Debug("Processing HTTPD configs in %s", httpdConfDir)
			if err := f.replacePlaceholdersInDir(httpdConfDir, appReplacements); err != nil {
				return fmt.Errorf("failed to process HTTPD configs: %w", err)
			}
		}
	}

	// Process Nginx configs
	if webServer == "nginx" {
		nginxConfDir := filepath.Join(buildDir, "nginx", "conf")
		if exists, _ := libbuildpack.FileExists(nginxConfDir); exists {
			// For nginx, also need to handle @{HOME} in some configs (like pid file)
			nginxReplacements := make(map[string]string)
			for k, v := range appReplacements {
				nginxReplacements[k] = v
			}
			nginxReplacements["@{HOME}"] = "/home/vcap/app"

			f.Log.Debug("Processing Nginx configs in %s", nginxConfDir)
			if err := f.replacePlaceholdersInDir(nginxConfDir, nginxReplacements); err != nil {
				return fmt.Errorf("failed to process Nginx configs: %w", err)
			}
		}
	}

	f.Log.Info("Config processing complete")
	return nil
}

// CreateStartScript creates the start script for the application
func (f *Finalizer) CreateStartScript() error {
	bpBinDir := filepath.Join(f.Stager.BuildDir(), ".bp", "bin")
	startScriptPath := filepath.Join(bpBinDir, "start")

	// Ensure .bp/bin directory exists
	if err := os.MkdirAll(bpBinDir, 0755); err != nil {
		return fmt.Errorf("could not create .bp/bin directory: %v", err)
	}

	bpDir := os.Getenv("BP_DIR")
	if bpDir == "" {
		return fmt.Errorf("BP_DIR environment variable not set")
	}

	opts, err := options.LoadOptions(bpDir, f.Stager.BuildDir(), f.Manifest, f.Log)
	if err != nil {
		return fmt.Errorf("could not load options: %v", err)
	}

	// Determine which web server to use from options
	webServer := opts.WebServer
	f.Log.Debug("Using web server: %s (from options.json)", webServer)

	var startScript string
	depsIdx := f.Stager.DepsIdx()

	switch webServer {
	case "httpd":
		startScript = f.generateHTTPDStartScript(depsIdx, opts)
	case "nginx":
		startScript = f.generateNginxStartScript(depsIdx, opts)
	case "none":
		startScript = f.generatePHPFPMStartScript(depsIdx, opts)
	default:
		return fmt.Errorf("unsupported web server: %s", webServer)
	}

	if err := os.WriteFile(startScriptPath, []byte(startScript), 0755); err != nil {
		return fmt.Errorf("could not write start script: %v", err)
	}

	f.Log.Info("Created start script for %s", webServer)
	return nil
}

// writePreStartScript creates a pre-start wrapper that runs optional user commands
// (e.g., migrations) before starting the server.
func (f *Finalizer) writePreStartScript() error {
	// Create script in .bp/bin/ directory (same location as start)
	bpBinDir := filepath.Join(f.Stager.BuildDir(), ".bp", "bin")
	if err := os.MkdirAll(bpBinDir, 0755); err != nil {
		return fmt.Errorf("could not create .bp/bin directory: %v", err)
	}
	preStartPath := filepath.Join(bpBinDir, "pre-start")

	script := `#!/usr/bin/env bash
# PHP Pre-Start Wrapper
# Runs optional user command before starting servers
set -e

# Set DEPS_DIR with fallback
: ${DEPS_DIR:=$HOME/.cloudfoundry}
export DEPS_DIR

# Run user command if provided
if [ $# -gt 0 ]; then
    echo "-----> Pre-start: Running command: $@"
    "$@" || {
        echo "ERROR: Pre-start command failed: $@"
        exit 1
    }
fi

# Start the application servers
echo "-----> Pre-start: Starting application..."
exec $HOME/.bp/bin/start
`

	if err := os.WriteFile(preStartPath, []byte(script), 0755); err != nil {
		return fmt.Errorf("could not write pre-start script: %v", err)
	}

	f.Log.Debug("Created pre-start wrapper script")
	return nil
}

// CreatePHPRuntimeDirectories creates directories needed by PHP-FPM at runtime
func (f *Finalizer) CreatePHPRuntimeDirectories() error {
	// Create the PHP-FPM PID file directory
	phpVarRunDir := filepath.Join(f.Stager.DepDir(), "php", "var", "run")
	if err := os.MkdirAll(phpVarRunDir, 0755); err != nil {
		return fmt.Errorf("could not create PHP var/run directory: %v", err)
	}
	f.Log.Debug("Created PHP runtime directory: %s", phpVarRunDir)
	return nil
}

// generateHTTPDStartScript generates a start script for Apache HTTPD with PHP-FPM
func (f *Finalizer) generateHTTPDStartScript(depsIdx string, opts *options.Options) string {
	// Load options to get WEBDIR and other config values
	webDir := os.Getenv("WEBDIR")
	if webDir == "" {
		webDir = opts.WebDir
		if webDir == "" {
			webDir = "htdocs" // default
		}
	}

	libDir := opts.LibDir
	if libDir == "" {
		libDir = "lib" // default
	}

	return fmt.Sprintf(`#!/usr/bin/env bash
# PHP Application Start Script (HTTPD)
set -e

# Set DEPS_DIR with fallback for different environments
: ${DEPS_DIR:=/home/vcap/deps}
export DEPS_DIR

# Set TMPDIR with fallback (users can override via environment variable)
: ${TMPDIR:=/home/vcap/tmp}
export TMPDIR

export PHPRC="$DEPS_DIR/%s/php/etc"
export PHP_INI_SCAN_DIR="$DEPS_DIR/%s/php/etc/php.ini.d"

# Add PHP binaries to PATH for CLI commands (e.g., bin/cake migrations)
export PATH="$DEPS_DIR/%s/php/bin:$PATH"

# Set HTTPD_SERVER_ADMIN if not already set
export HTTPD_SERVER_ADMIN="${HTTPD_SERVER_ADMIN:-noreply@vcap.me}"

echo "Starting PHP application with HTTPD..."
echo "DEPS_DIR: $DEPS_DIR"
echo "TMPDIR: $TMPDIR"
echo "PHP-FPM: $DEPS_DIR/%s/php/sbin/php-fpm"
echo "HTTPD: $DEPS_DIR/%s/httpd/bin/httpd"

# Create symlinks for httpd files (httpd config expects them relative to ServerRoot)
ln -sf "$DEPS_DIR/%s/httpd/modules" "$HOME/httpd/modules"
ln -sf "$DEPS_DIR/%s/httpd/conf/mime.types" "$HOME/httpd/conf/mime.types" 2>/dev/null || \
    touch "$HOME/httpd/conf/mime.types"

# Create required directories
mkdir -p "$HOME/httpd/logs"
mkdir -p "$DEPS_DIR/%s/php/var/run"
mkdir -p "$TMPDIR"

# Expand ${TMPDIR} in PHP configs (php.ini uses ${TMPDIR} placeholder)
# This allows users to customize TMPDIR via environment variable
for config_file in "$PHPRC/php.ini" "$PHPRC/php-fpm.conf"; do
    if [ -f "$config_file" ]; then
        sed "s|\${TMPDIR}|$TMPDIR|g" "$config_file" > "$config_file.tmp"
        mv "$config_file.tmp" "$config_file"
    fi
done

# Also process php.ini.d directory if it exists
if [ -d "$PHP_INI_SCAN_DIR" ]; then
    for config_file in "$PHP_INI_SCAN_DIR"/*.ini; do
        if [ -f "$config_file" ]; then
            sed "s|\${TMPDIR}|$TMPDIR|g" "$config_file" > "$config_file.tmp"
            mv "$config_file.tmp" "$config_file"
        fi
    done
fi

# Start PHP-FPM in background
$DEPS_DIR/%s/php/sbin/php-fpm -F -y $PHPRC/php-fpm.conf &
PHP_FPM_PID=$!

# Start HTTPD in foreground directly (bypass apachectl which has hardcoded paths)
$DEPS_DIR/%s/httpd/bin/httpd -f "$HOME/httpd/conf/httpd.conf" -k start -DFOREGROUND &
HTTPD_PID=$!

# Wait for both processes
wait $PHP_FPM_PID $HTTPD_PID
`, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx)
}

// generateNginxStartScript generates a start script for Nginx with PHP-FPM
func (f *Finalizer) generateNginxStartScript(depsIdx string, opts *options.Options) string {
	// Load options to get WEBDIR and other config values
	webDir := os.Getenv("WEBDIR")
	if webDir == "" {
		webDir = opts.WebDir
		if webDir == "" {
			webDir = "htdocs" // default
		}
	}

	libDir := opts.LibDir
	if libDir == "" {
		libDir = "lib" // default
	}

	return fmt.Sprintf(`#!/usr/bin/env bash
# PHP Application Start Script (Nginx)
set -e

# Set DEPS_DIR with fallback for different environments
: ${DEPS_DIR:=/home/vcap/deps}
export DEPS_DIR

# Set TMPDIR with fallback (users can override via environment variable)
: ${TMPDIR:=/home/vcap/tmp}
export TMPDIR

export PHPRC="$DEPS_DIR/%s/php/etc"
export PHP_INI_SCAN_DIR="$DEPS_DIR/%s/php/etc/php.ini.d"

# Add PHP binaries to PATH for CLI commands (e.g., bin/cake migrations)
export PATH="$DEPS_DIR/%s/php/bin:$PATH"

echo "Starting PHP application with Nginx..."
echo "DEPS_DIR: $DEPS_DIR"
echo "TMPDIR: $TMPDIR"
echo "PHP-FPM: $DEPS_DIR/%s/php/sbin/php-fpm"
echo "Nginx: $DEPS_DIR/%s/nginx/sbin/nginx"

# Substitute runtime variables in nginx config
# PORT is assigned by Cloud Foundry, TMPDIR can be customized by user
sed -e "s|\${PORT}|$PORT|g" -e "s|\${TMPDIR}|$TMPDIR|g" "$HOME/nginx/conf/server-defaults.conf" > "$HOME/nginx/conf/server-defaults.conf.tmp"
mv "$HOME/nginx/conf/server-defaults.conf.tmp" "$HOME/nginx/conf/server-defaults.conf"

# Expand ${TMPDIR} in PHP configs (php.ini uses ${TMPDIR} placeholder)
# This allows users to customize TMPDIR via environment variable
for config_file in "$PHPRC/php.ini" "$PHPRC/php-fpm.conf"; do
    if [ -f "$config_file" ]; then
        sed "s|\${TMPDIR}|$TMPDIR|g" "$config_file" > "$config_file.tmp"
        mv "$config_file.tmp" "$config_file"
    fi
done

# Also process php.ini.d directory if it exists
if [ -d "$PHP_INI_SCAN_DIR" ]; then
    for config_file in "$PHP_INI_SCAN_DIR"/*.ini; do
        if [ -f "$config_file" ]; then
            sed "s|\${TMPDIR}|$TMPDIR|g" "$config_file" > "$config_file.tmp"
            mv "$config_file.tmp" "$config_file"
        fi
    done
fi

# Create required directories
mkdir -p "$DEPS_DIR/%s/php/var/run"
mkdir -p "$HOME/nginx/logs"
mkdir -p "$TMPDIR"
mkdir -p "$TMPDIR/nginx_fastcgi"
mkdir -p "$TMPDIR/nginx_client_body"
mkdir -p "$TMPDIR/nginx_proxy"

# Start PHP-FPM in background
$DEPS_DIR/%s/php/sbin/php-fpm -F -y $PHPRC/php-fpm.conf &
PHP_FPM_PID=$!

# Start Nginx in foreground (nginx binary is in DEPS_DIR, not HOME)
$DEPS_DIR/%s/nginx/sbin/nginx -c "$HOME/nginx/conf/nginx.conf" &
NGINX_PID=$!

# Wait for both processes
wait $PHP_FPM_PID $NGINX_PID
`, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx)
}

// generatePHPFPMStartScript generates a start script for PHP-FPM only (no web server)
func (f *Finalizer) generatePHPFPMStartScript(depsIdx string, opts *options.Options) string {
	// Load options to get WEBDIR and other config values
	webDir := os.Getenv("WEBDIR")
	if webDir == "" {
		webDir = opts.WebDir
		if webDir == "" {
			webDir = "htdocs" // default
		}
	}

	libDir := opts.LibDir
	if libDir == "" {
		libDir = "lib" // default
	}

	return fmt.Sprintf(`#!/usr/bin/env bash
# PHP Application Start Script (PHP-FPM only)
set -e

# Set DEPS_DIR with fallback for different environments
: ${DEPS_DIR:=/home/vcap/deps}
export DEPS_DIR

# Set TMPDIR with fallback (users can override via environment variable)
: ${TMPDIR:=/home/vcap/tmp}
export TMPDIR

export PHPRC="$DEPS_DIR/%s/php/etc"
export PHP_INI_SCAN_DIR="$DEPS_DIR/%s/php/etc/php.ini.d"

echo "Starting PHP-FPM only..."
echo "DEPS_DIR: $DEPS_DIR"
echo "TMPDIR: $TMPDIR"
echo "PHP-FPM path: $DEPS_DIR/%s/php/sbin/php-fpm"

# Expand ${TMPDIR} in PHP configs
for config_file in "$PHPRC/php.ini" "$PHPRC/php-fpm.conf"; do
    if [ -f "$config_file" ]; then
        sed "s|\${TMPDIR}|$TMPDIR|g" "$config_file" > "$config_file.tmp"
        mv "$config_file.tmp" "$config_file"
    fi
done

# Also process php.ini.d directory if it exists
if [ -d "$PHP_INI_SCAN_DIR" ]; then
    for config_file in "$PHP_INI_SCAN_DIR"/*.ini; do
        if [ -f "$config_file" ]; then
            sed "s|\${TMPDIR}|$TMPDIR|g" "$config_file" > "$config_file.tmp"
            mv "$config_file.tmp" "$config_file"
        fi
    done
fi

# Create PHP-FPM socket directory if it doesn't exist
mkdir -p "$DEPS_DIR/%s/php/var/run"
mkdir -p "$TMPDIR"

# Start PHP-FPM in foreground
exec $DEPS_DIR/%s/php/sbin/php-fpm -F -y $PHPRC/php-fpm.conf
`, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx)
}

// SetupProcessTypes creates the process types for the application
func (f *Finalizer) SetupProcessTypes() error {
	// TODO: Read from Procfile if it exists
	// TODO: Generate default web process based on WEB_SERVER config

	procfile := filepath.Join(f.Stager.BuildDir(), "Procfile")
	if exists, err := libbuildpack.FileExists(procfile); err != nil {
		return err
	} else if exists {
		f.Log.Debug("Using existing Procfile")
		return nil
	}

	// Create default Procfile
	defaultProcfile := "web: .bp/bin/start\n"
	if err := os.WriteFile(procfile, []byte(defaultProcfile), 0644); err != nil {
		return fmt.Errorf("could not write Procfile: %v", err)
	}

	return nil
}

// replacePlaceholders replaces build-time placeholders in a file
func (f *Finalizer) replacePlaceholders(filePath string, replacements map[string]string) error {
	content, err := os.ReadFile(filePath)
	if err != nil {
		return fmt.Errorf("failed to read file %s: %w", filePath, err)
	}

	result := string(content)

	// Replace all placeholders
	for placeholder, value := range replacements {
		result = strings.ReplaceAll(result, placeholder, value)
	}

	if err := os.WriteFile(filePath, []byte(result), 0644); err != nil {
		return fmt.Errorf("failed to write file %s: %w", filePath, err)
	}

	return nil
}

// replacePlaceholdersInDir replaces placeholders in all files in a directory recursively
func (f *Finalizer) replacePlaceholdersInDir(dirPath string, replacements map[string]string) error {
	return f.replacePlaceholdersInDirExclude(dirPath, replacements, nil)
}

func (f *Finalizer) replacePlaceholdersInDirExclude(dirPath string, replacements map[string]string, excludeDirs []string) error {
	return filepath.Walk(dirPath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		// Skip directories, but check if we should skip their contents
		if info.IsDir() {
			// Check if this directory should be excluded
			for _, exclude := range excludeDirs {
				if path == exclude {
					return filepath.SkipDir
				}
			}
			return nil
		}

		// Replace placeholders in this file
		return f.replacePlaceholders(path, replacements)
	})
}

func (f *Finalizer) copyFile(src, dst string) error {
	sourceFile, err := os.Open(src)
	if err != nil {
		return fmt.Errorf("could not open source file: %v", err)
	}
	defer sourceFile.Close()

	destFile, err := os.Create(dst)
	if err != nil {
		return fmt.Errorf("could not create destination file: %v", err)
	}
	defer destFile.Close()

	if _, err := io.Copy(destFile, sourceFile); err != nil {
		return fmt.Errorf("could not copy file: %v", err)
	}

	sourceInfo, err := os.Stat(src)
	if err != nil {
		return fmt.Errorf("could not stat source file: %v", err)
	}

	if err := os.Chmod(dst, sourceInfo.Mode()); err != nil {
		return fmt.Errorf("could not set file permissions: %v", err)
	}

	return nil
}
