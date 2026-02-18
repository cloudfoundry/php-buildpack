package newrelic

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/cloudfoundry/php-buildpack/src/php/extensions"
)

const newrelicEnvScript = `if [[ -z "${NEWRELIC_LICENSE:-}" ]]; then
  export NEWRELIC_LICENSE=$(echo $VCAP_SERVICES  | jq -r '.newrelic[0].credentials.licenseKey')
fi
`

// NewRelicExtension downloads, installs and configures the NewRelic agent for PHP
type NewRelicExtension struct {
	detected      bool
	appName       string
	licenseKey    string
	newrelicSo    string
	logPath       string
	daemonLogPath string
	daemonPath    string
	socketPath    string
	pidPath       string
	phpIniPath    string
	phpExtnDir    string
	phpAPI        string
	phpZTS        bool
	phpArch       string
	buildDir      string
	bpDir         string
}

// Name returns the extension name
func (e *NewRelicExtension) Name() string {
	return "newrelic"
}

// ShouldCompile determines if NewRelic should be installed
func (e *NewRelicExtension) ShouldCompile(ctx *extensions.Context) bool {
	// Only run if PHP VM is 'php'
	if ctx.GetString("PHP_VM") != "php" {
		return false
	}

	e.loadServiceInfo(ctx)
	e.loadNewRelicInfo(ctx)

	return e.detected
}

// loadServiceInfo searches for NewRelic service
func (e *NewRelicExtension) loadServiceInfo(ctx *extensions.Context) {
	services := ctx.FindServicesByLabel("newrelic")

	if len(services) == 0 {
		fmt.Println("-----> NewRelic services not detected.")
		return
	}

	if len(services) > 1 {
		fmt.Println("-----> WARNING: Multiple NewRelic services found, using credentials from first one.")
	}

	if len(services) > 0 {
		service := services[0]
		if licenseKey, ok := service.Credentials["licenseKey"].(string); ok && licenseKey != "" {
			e.licenseKey = licenseKey
			e.detected = true
		}
	}
}

// loadNewRelicInfo loads application info and checks for manual configuration
func (e *NewRelicExtension) loadNewRelicInfo(ctx *extensions.Context) {
	// Get app name from VCAP_APPLICATION
	e.appName = ctx.VcapApplication.Name

	// Check for manual license key configuration
	if manualKey := ctx.GetString("NEWRELIC_LICENSE"); manualKey != "" {
		if e.detected {
			fmt.Println("-----> WARNING: Detected a NewRelic Service & Manual Key, using the manual key.")
		}
		e.licenseKey = manualKey
		e.detected = true
	} else if e.licenseKey != "" {
		// Store license key in context for later use
		ctx.Set("NEWRELIC_LICENSE", e.licenseKey)
	}
}

// Configure runs early configuration
func (e *NewRelicExtension) Configure(ctx *extensions.Context) error {
	e.buildDir = ctx.GetString("BUILD_DIR")
	e.bpDir = ctx.GetString("BP_DIR")

	// Load PHP info
	e.phpIniPath = filepath.Join(e.buildDir, "php", "etc", "php.ini")

	if err := e.loadPHPInfo(); err != nil {
		return fmt.Errorf("failed to load PHP info: %w", err)
	}

	if e.detected {
		// Set up paths
		newrelicSoName := fmt.Sprintf("newrelic-%s%s.so", e.phpAPI, map[bool]string{true: "zts", false: ""}[e.phpZTS])
		e.newrelicSo = filepath.Join("@{HOME}", "newrelic", "agent", e.phpArch, newrelicSoName)
		e.logPath = filepath.Join("@{HOME}", "logs", "newrelic.log")
		e.daemonLogPath = filepath.Join("@{HOME}", "logs", "newrelic-daemon.log")
		e.daemonPath = filepath.Join("@{HOME}", "newrelic", "daemon", fmt.Sprintf("newrelic-daemon.%s", e.phpArch))
		e.socketPath = filepath.Join("@{HOME}", "newrelic", "daemon.sock")
		e.pidPath = filepath.Join("@{HOME}", "newrelic", "daemon.pid")
	}

	return nil
}

// loadPHPInfo extracts PHP configuration information
func (e *NewRelicExtension) loadPHPInfo() error {
	// Find extension_dir from php.ini
	data, err := os.ReadFile(e.phpIniPath)
	if err != nil {
		return fmt.Errorf("failed to read php.ini: %w", err)
	}

	lines := strings.Split(string(data), "\n")
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if strings.HasPrefix(line, "extension_dir") {
			parts := strings.Split(line, " = ")
			if len(parts) == 2 {
				e.phpExtnDir = strings.Trim(parts[1], "\"")
				break
			}
		}
	}

	if e.phpExtnDir == "" {
		return fmt.Errorf("extension_dir not found in php.ini")
	}

	// Parse PHP API version and ZTS status from extension directory
	basename := filepath.Base(e.phpExtnDir)
	parts := strings.Split(basename, "-")
	if len(parts) > 0 {
		e.phpAPI = parts[len(parts)-1]
	}
	e.phpZTS = !strings.Contains(basename, "non-zts")

	// Set architecture (default to x64)
	e.phpArch = "x64"
	if arch := os.Getenv("NEWRELIC_ARCH"); arch != "" {
		e.phpArch = arch
	}

	return nil
}

// Compile downloads and installs NewRelic
func (e *NewRelicExtension) Compile(ctx *extensions.Context, installer *extensions.Installer) error {
	if !e.detected {
		return nil
	}

	fmt.Println("-----> Installing NewRelic")

	newrelicInstallDir := filepath.Join(e.buildDir, "newrelic")
	if err := installer.InstallOnlyVersion("newrelic", newrelicInstallDir); err != nil {
		return fmt.Errorf("failed to install NewRelic package: %w", err)
	}

	// Add environment variables script
	if err := e.addingEnvironmentVariables(); err != nil {
		return fmt.Errorf("failed to add environment variables: %w", err)
	}

	// Modify php.ini
	fmt.Println("-----> Configuring NewRelic in php.ini")
	if err := e.modifyPHPIni(); err != nil {
		return fmt.Errorf("failed to modify php.ini: %w", err)
	}

	fmt.Println("-----> NewRelic Installed.")
	return nil
}

// addingEnvironmentVariables creates the NewRelic environment script
func (e *NewRelicExtension) addingEnvironmentVariables() error {
	destFolder := filepath.Join(e.buildDir, ".profile.d")
	dest := filepath.Join(destFolder, "0_newrelic_env.sh")

	// Create .profile.d folder if it doesn't exist
	if err := os.MkdirAll(destFolder, 0755); err != nil {
		return fmt.Errorf("failed to create .profile.d directory: %w", err)
	}

	// Write the environment script
	if err := os.WriteFile(dest, []byte(newrelicEnvScript), 0644); err != nil {
		return fmt.Errorf("failed to write newrelic_env.sh: %w", err)
	}

	return nil
}

// modifyPHPIni adds NewRelic configuration to php.ini
func (e *NewRelicExtension) modifyPHPIni() error {
	data, err := os.ReadFile(e.phpIniPath)
	if err != nil {
		return fmt.Errorf("failed to read php.ini: %w", err)
	}

	lines := strings.Split(string(data), "\n")

	// Find where to insert the extension line
	// Look for the last extension= line
	insertPos := -1
	for i, line := range lines {
		if strings.HasPrefix(strings.TrimSpace(line), "extension=") {
			insertPos = i + 1
		}
	}

	// If no extensions found, insert after #{PHP_EXTENSIONS} marker
	if insertPos == -1 {
		for i, line := range lines {
			if strings.Contains(line, "#{PHP_EXTENSIONS}") {
				insertPos = i + 1
				break
			}
		}
	}

	if insertPos == -1 {
		return fmt.Errorf("could not find suitable position to insert extension in php.ini")
	}

	// Insert the NewRelic extension line
	newLines := append(lines[:insertPos], append([]string{fmt.Sprintf("extension=%s", e.newrelicSo)}, lines[insertPos:]...)...)

	// Append NewRelic configuration section at the end
	newRelicConfig := []string{
		"",
		"[newrelic]",
		fmt.Sprintf("newrelic.license=%s", "@{NEWRELIC_LICENSE}"),
		fmt.Sprintf("newrelic.appname=%s", e.appName),
		fmt.Sprintf("newrelic.logfile=%s", e.logPath),
		fmt.Sprintf("newrelic.daemon.logfile=%s", e.daemonLogPath),
		fmt.Sprintf("newrelic.daemon.location=%s", e.daemonPath),
		fmt.Sprintf("newrelic.daemon.port=%s", e.socketPath),
		fmt.Sprintf("newrelic.daemon.pidfile=%s", e.pidPath),
	}

	newLines = append(newLines, newRelicConfig...)

	// Write back to php.ini
	output := strings.Join(newLines, "\n")
	if err := os.WriteFile(e.phpIniPath, []byte(output), 0644); err != nil {
		return fmt.Errorf("failed to write php.ini: %w", err)
	}

	return nil
}

// PreprocessCommands returns commands to run before app starts (none for NewRelic)
func (e *NewRelicExtension) PreprocessCommands(ctx *extensions.Context) ([]string, error) {
	return nil, nil
}

// ServiceCommands returns long-running service commands (none for NewRelic)
func (e *NewRelicExtension) ServiceCommands(ctx *extensions.Context) (map[string]string, error) {
	return nil, nil
}

// ServiceEnvironment returns environment variables for runtime
func (e *NewRelicExtension) ServiceEnvironment(ctx *extensions.Context) (map[string]string, error) {
	if !e.detected {
		return nil, nil
	}

	return map[string]string{
		"NEWRELIC_LICENSE": "$NEWRELIC_LICENSE",
	}, nil
}
