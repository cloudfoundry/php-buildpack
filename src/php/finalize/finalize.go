package finalize

import (
	"fmt"
	"io"
	"os"
	"path/filepath"

	"github.com/cloudfoundry/libbuildpack"
	"github.com/cloudfoundry/php-buildpack/src/php/extensions"
	"github.com/cloudfoundry/php-buildpack/src/php/options"
	"github.com/cloudfoundry/php-buildpack/src/php/util"
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

// CreateStartScript creates the start script for the application
func (f *Finalizer) CreateStartScript() error {
	bpBinDir := filepath.Join(f.Stager.BuildDir(), ".bp", "bin")
	startScriptPath := filepath.Join(bpBinDir, "start")

	// Ensure .bp/bin directory exists
	if err := os.MkdirAll(bpBinDir, 0755); err != nil {
		return fmt.Errorf("could not create .bp/bin directory: %v", err)
	}

	// Copy rewrite binary to .bp/bin
	bpDir := os.Getenv("BP_DIR")
	if bpDir == "" {
		return fmt.Errorf("BP_DIR environment variable not set")
	}
	rewriteSrc := filepath.Join(bpDir, "bin", "rewrite")
	rewriteDst := filepath.Join(bpBinDir, "rewrite")
	if err := util.CopyFile(rewriteSrc, rewriteDst); err != nil {
		return fmt.Errorf("could not copy rewrite binary: %v", err)
	}
	f.Log.Debug("Copied rewrite binary to .bp/bin")

	// Load options from options.json to determine which web server to use
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

// writePreStartScript creates a pre-start wrapper that handles config rewriting
// before running optional user commands (e.g., migrations) and starting the server.
// This allows PHP commands to run with properly rewritten configs.
func (f *Finalizer) writePreStartScript() error {
	depsIdx := f.Stager.DepsIdx()

	// Create script in .bp/bin/ directory (same location as start and rewrite)
	bpBinDir := filepath.Join(f.Stager.BuildDir(), ".bp", "bin")
	if err := os.MkdirAll(bpBinDir, 0755); err != nil {
		return fmt.Errorf("could not create .bp/bin directory: %v", err)
	}
	preStartPath := filepath.Join(bpBinDir, "pre-start")

	script := fmt.Sprintf(`#!/usr/bin/env bash
# PHP Pre-Start Wrapper
# Runs config rewriting and optional user command before starting servers
set -e

# Set DEPS_DIR with fallback
: ${DEPS_DIR:=$HOME/.cloudfoundry}
export DEPS_DIR

# Source all profile.d scripts to set up environment
for f in /home/vcap/deps/%s/profile.d/*.sh; do
    [ -f "$f" ] && source "$f"
done

# Export required variables for rewrite tool
export HOME="${HOME:-/home/vcap/app}"
export PHPRC="$DEPS_DIR/%s/php/etc"
export PHP_INI_SCAN_DIR="$DEPS_DIR/%s/php/etc/php.ini.d"

echo "-----> Pre-start: Rewriting PHP configs..."

# Rewrite PHP base configs with HOME=$DEPS_DIR/0
OLD_HOME="$HOME"
export HOME="$DEPS_DIR/%s"
$OLD_HOME/.bp/bin/rewrite "$DEPS_DIR/%s/php/etc/php.ini"
$OLD_HOME/.bp/bin/rewrite "$DEPS_DIR/%s/php/etc/php-fpm.conf"
export HOME="$OLD_HOME"

# Rewrite user configs with app HOME
if [ -d "$DEPS_DIR/%s/php/etc/fpm.d" ]; then
    $HOME/.bp/bin/rewrite "$DEPS_DIR/%s/php/etc/fpm.d"
fi

if [ -d "$DEPS_DIR/%s/php/etc/php.ini.d" ]; then
    $HOME/.bp/bin/rewrite "$DEPS_DIR/%s/php/etc/php.ini.d"
fi

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
`, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx)

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

	phpFpmConfInclude := "; No additional includes"

	return fmt.Sprintf(`#!/usr/bin/env bash
# PHP Application Start Script (HTTPD)
set -e

# Set DEPS_DIR with fallback for different environments
: ${DEPS_DIR:=$HOME/.cloudfoundry}
export DEPS_DIR
export PHPRC="$DEPS_DIR/%s/php/etc"
export PHP_INI_SCAN_DIR="$DEPS_DIR/%s/php/etc/php.ini.d"

# Add PHP binaries to PATH for CLI commands (e.g., bin/cake migrations)
export PATH="$DEPS_DIR/%s/php/bin:$PATH"

# Set HTTPD_SERVER_ADMIN if not already set
export HTTPD_SERVER_ADMIN="${HTTPD_SERVER_ADMIN:-noreply@vcap.me}"

# Set template variables for rewrite tool - use absolute paths!
export HOME="${HOME:-/home/vcap/app}"
export WEBDIR="%s"
export LIBDIR="%s"
export PHP_FPM_LISTEN="127.0.0.1:9000"
export PHP_FPM_CONF_INCLUDE="%s"

echo "Starting PHP application with HTTPD..."
echo "DEPS_DIR: $DEPS_DIR"
echo "WEBDIR: $WEBDIR"
echo "PHP-FPM: $DEPS_DIR/%s/php/sbin/php-fpm"
echo "HTTPD: $DEPS_DIR/%s/httpd/bin/httpd"
echo "Checking if binaries exist..."
ls -la "$DEPS_DIR/%s/php/sbin/php-fpm" || echo "PHP-FPM not found!"
ls -la "$DEPS_DIR/%s/httpd/bin/httpd" || echo "HTTPD not found!"

# Create symlinks for httpd files (httpd config expects them relative to ServerRoot)
ln -sf "$DEPS_DIR/%s/httpd/modules" "$HOME/httpd/modules"
ln -sf "$DEPS_DIR/%s/httpd/conf/mime.types" "$HOME/httpd/conf/mime.types" 2>/dev/null || \
    touch "$HOME/httpd/conf/mime.types"

# Create httpd logs directory if it doesn't exist
mkdir -p "$HOME/httpd/logs"

# Run rewrite to update config with runtime values
$HOME/.bp/bin/rewrite "$HOME/httpd/conf"

# Rewrite PHP base configs (php.ini, php-fpm.conf) with HOME=$DEPS_DIR/0
# This ensures @{HOME} placeholders in extension_dir are replaced with correct deps path
OLD_HOME="$HOME"
export HOME="$DEPS_DIR/%s"
export DEPS_DIR
$OLD_HOME/.bp/bin/rewrite "$DEPS_DIR/%s/php/etc/php.ini"
$OLD_HOME/.bp/bin/rewrite "$DEPS_DIR/%s/php/etc/php-fpm.conf"
export HOME="$OLD_HOME"

# Rewrite user fpm.d configs with HOME=/home/vcap/app
# User configs expect HOME to be the app directory, not deps directory
if [ -d "$DEPS_DIR/%s/php/etc/fpm.d" ]; then
    $HOME/.bp/bin/rewrite "$DEPS_DIR/%s/php/etc/fpm.d"
fi

# Rewrite php.ini.d configs with app HOME as well (may contain user overrides)
if [ -d "$DEPS_DIR/%s/php/etc/php.ini.d" ]; then
    $HOME/.bp/bin/rewrite "$DEPS_DIR/%s/php/etc/php.ini.d"
fi

# Create PHP-FPM socket directory if it doesn't exist
mkdir -p "$DEPS_DIR/%s/php/var/run"

# Start PHP-FPM in background
$DEPS_DIR/%s/php/sbin/php-fpm -F -y $PHPRC/php-fpm.conf &
PHP_FPM_PID=$!

# Start HTTPD in foreground directly (bypass apachectl which has hardcoded paths)
$DEPS_DIR/%s/httpd/bin/httpd -f "$HOME/httpd/conf/httpd.conf" -k start -DFOREGROUND &
HTTPD_PID=$!

# Wait for both processes
wait $PHP_FPM_PID $HTTPD_PID
`, depsIdx, depsIdx, depsIdx, webDir, libDir, phpFpmConfInclude, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx)
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
: ${DEPS_DIR:=$HOME/.cloudfoundry}
export DEPS_DIR
export PHPRC="$DEPS_DIR/%s/php/etc"
export PHP_INI_SCAN_DIR="$DEPS_DIR/%s/php/etc/php.ini.d"

# Add PHP binaries to PATH for CLI commands (e.g., bin/cake migrations)
export PATH="$DEPS_DIR/%s/php/bin:$PATH"

# Set template variables for rewrite tool - use absolute paths!
export HOME="${HOME:-/home/vcap/app}"
export WEBDIR="%s"
export LIBDIR="%s"
export PHP_FPM_LISTEN="127.0.0.1:9000"
export PHP_FPM_CONF_INCLUDE=""

echo "Starting PHP application with Nginx..."
echo "DEPS_DIR: $DEPS_DIR"
echo "WEBDIR: $WEBDIR"
echo "PHP-FPM: $DEPS_DIR/%s/php/sbin/php-fpm"
echo "Nginx: $DEPS_DIR/%s/nginx/sbin/nginx"
echo "Checking if binaries exist..."
ls -la "$DEPS_DIR/%s/php/sbin/php-fpm" || echo "PHP-FPM not found!"
ls -la "$DEPS_DIR/%s/nginx/sbin/nginx" || echo "Nginx not found!"

# Run rewrite to update config with runtime values
$HOME/.bp/bin/rewrite "$HOME/nginx/conf"

# Rewrite PHP base configs (php.ini, php-fpm.conf) with HOME=$DEPS_DIR/0
# This ensures @{HOME} placeholders in extension_dir are replaced with correct deps path
OLD_HOME="$HOME"
export HOME="$DEPS_DIR/%s"
export DEPS_DIR
$OLD_HOME/.bp/bin/rewrite "$DEPS_DIR/%s/php/etc/php.ini"
$OLD_HOME/.bp/bin/rewrite "$DEPS_DIR/%s/php/etc/php-fpm.conf"
export HOME="$OLD_HOME"

# Rewrite user fpm.d configs with HOME=/home/vcap/app
# User configs expect HOME to be the app directory, not deps directory
if [ -d "$DEPS_DIR/%s/php/etc/fpm.d" ]; then
    $HOME/.bp/bin/rewrite "$DEPS_DIR/%s/php/etc/fpm.d"
fi

# Rewrite php.ini.d configs with app HOME as well (may contain user overrides)
if [ -d "$DEPS_DIR/%s/php/etc/php.ini.d" ]; then
    $HOME/.bp/bin/rewrite "$DEPS_DIR/%s/php/etc/php.ini.d"
fi

# Create required directories
mkdir -p "$DEPS_DIR/%s/php/var/run"
mkdir -p "$HOME/nginx/logs"

# Start PHP-FPM in background
$DEPS_DIR/%s/php/sbin/php-fpm -F -y $PHPRC/php-fpm.conf &
PHP_FPM_PID=$!

# Start Nginx in foreground (nginx binary is in DEPS_DIR, not HOME)
$DEPS_DIR/%s/nginx/sbin/nginx -c "$HOME/nginx/conf/nginx.conf" &
NGINX_PID=$!

# Wait for both processes
wait $PHP_FPM_PID $NGINX_PID
`, depsIdx, depsIdx, depsIdx, webDir, libDir, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx)
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
: ${DEPS_DIR:=$HOME/.cloudfoundry}
export DEPS_DIR
export PHPRC="$DEPS_DIR/%s/php/etc"
export PHP_INI_SCAN_DIR="$DEPS_DIR/%s/php/etc/php.ini.d"

# Set template variables for rewrite tool - use absolute paths!
export HOME="${HOME:-/home/vcap/app}"
export WEBDIR="%s"
export LIBDIR="%s"
export PHP_FPM_LISTEN="$DEPS_DIR/%s/php/var/run/php-fpm.sock"
export PHP_FPM_CONF_INCLUDE=""

echo "Starting PHP-FPM only..."
echo "DEPS_DIR: $DEPS_DIR"
echo "WEBDIR: $WEBDIR"
echo "PHP-FPM path: $DEPS_DIR/%s/php/sbin/php-fpm"
ls -la "$DEPS_DIR/%s/php/sbin/php-fpm" || echo "PHP-FPM not found!"

# Temporarily set HOME to DEPS_DIR/0 for PHP config rewriting
# This ensures @{HOME} placeholders in extension_dir are replaced with the correct path
OLD_HOME="$HOME"
export HOME="$DEPS_DIR/%s"
export DEPS_DIR
$OLD_HOME/.bp/bin/rewrite "$DEPS_DIR/%s/php/etc"
export HOME="$OLD_HOME"

# Create PHP-FPM socket directory if it doesn't exist
mkdir -p "$DEPS_DIR/%s/php/var/run"

# Start PHP-FPM in foreground
exec $DEPS_DIR/%s/php/sbin/php-fpm -F -y $PHPRC/php-fpm.conf
`, depsIdx, depsIdx, webDir, libDir, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx, depsIdx)
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
