package appdynamics

import (
	"fmt"
	"path/filepath"
	"regexp"

	"github.com/cloudfoundry/php-buildpack/src/php/extensions"
)

// AppDynamicsExtension downloads, installs and configures the AppDynamics agent for PHP
type AppDynamicsExtension struct{}

// Name returns the extension name
func (e *AppDynamicsExtension) Name() string {
	return "appdynamics"
}

const (
	filterPattern = "app[-]?dynamics"
)

// credentials holds AppDynamics controller and application configuration
type credentials struct {
	hostName         string
	port             string
	accountName      string
	accountAccessKey string
	sslEnabled       string
	appName          string
	tierName         string
	nodeName         string
}

// detectAppDynamicsService searches for AppDynamics service in VCAP_SERVICES
func (e *AppDynamicsExtension) detectAppDynamicsService(ctx *extensions.Context) bool {
	pattern := regexp.MustCompile(filterPattern)

	// Search in all services for AppDynamics pattern
	for _, services := range ctx.VcapServices {
		for _, service := range services {
			if pattern.MatchString(service.Name) {
				return true
			}
		}
	}

	return false
}

// loadServiceCredentials loads AppDynamics configuration from VCAP_SERVICES
func (e *AppDynamicsExtension) loadServiceCredentials(ctx *extensions.Context) *credentials {
	creds := &credentials{}

	// Try marketplace AppDynamics services first
	if appdServices := ctx.FindServicesByLabel("appdynamics"); len(appdServices) > 0 {
		if len(appdServices) > 1 {
			fmt.Println("Multiple AppDynamics services found in VCAP_SERVICES, using credentials from first one.")
		} else {
			fmt.Println("AppDynamics service found in VCAP_SERVICES")
		}

		service := appdServices[0]
		creds.loadFromCredentials(service.Credentials)
		creds.loadAppDetails(ctx)
		return creds
	}

	// Try user-provided services
	fmt.Println("No Marketplace AppDynamics services found")
	fmt.Println("Searching for AppDynamics service in user-provided services")

	if userServices := ctx.FindServicesByLabel("user-provided"); len(userServices) > 0 {
		pattern := regexp.MustCompile(filterPattern)
		for _, service := range userServices {
			if pattern.MatchString(service.Name) {
				fmt.Println("Using the first AppDynamics service present in user-provided services")
				creds.loadFromCredentials(service.Credentials)

				// Try to load app details from user-provided service
				fmt.Println("Setting AppDynamics App, Tier and Node names from user-provided service")
				if appName, ok := service.Credentials["application-name"].(string); ok {
					creds.appName = appName
					fmt.Printf("User-provided service application-name = %s\n", creds.appName)
				}
				if tierName, ok := service.Credentials["tier-name"].(string); ok {
					creds.tierName = tierName
					fmt.Printf("User-provided service tier-name = %s\n", creds.tierName)
				}
				if nodeName, ok := service.Credentials["node-name"].(string); ok {
					creds.nodeName = nodeName
					fmt.Printf("User-provided service node-name = %s\n", creds.nodeName)
				}

				// If app details weren't in user-provided service, use defaults
				if creds.appName == "" || creds.tierName == "" || creds.nodeName == "" {
					fmt.Println("Exception occurred while setting AppDynamics App, Tier and Node names from user-provided service, using default naming")
					creds.loadAppDetails(ctx)
				}

				return creds
			}
		}
	}

	return nil
}

// loadFromCredentials populates controller binding credentials
func (c *credentials) loadFromCredentials(credMap map[string]interface{}) {
	fmt.Println("Setting AppDynamics Controller Binding Credentials")

	if hostName, ok := credMap["host-name"].(string); ok {
		c.hostName = hostName
	}
	if port, ok := credMap["port"]; ok {
		c.port = fmt.Sprintf("%v", port)
	}
	if accountName, ok := credMap["account-name"].(string); ok {
		c.accountName = accountName
	}
	if accessKey, ok := credMap["account-access-key"].(string); ok {
		c.accountAccessKey = accessKey
	}
	if sslEnabled, ok := credMap["ssl-enabled"]; ok {
		c.sslEnabled = fmt.Sprintf("%v", sslEnabled)
	}
}

// loadAppDetails sets default application naming from VCAP_APPLICATION
func (c *credentials) loadAppDetails(ctx *extensions.Context) {
	fmt.Println("Setting default AppDynamics App, Tier and Node names")

	spaceName := ctx.VcapApplication.SpaceName
	appName := ctx.VcapApplication.ApplicationName

	c.appName = fmt.Sprintf("%s:%s", spaceName, appName)
	fmt.Printf("AppDynamics default application-name = %s\n", c.appName)

	c.tierName = appName
	fmt.Printf("AppDynamics default tier-name = %s\n", c.tierName)

	c.nodeName = c.tierName
	fmt.Printf("AppDynamics default node-name = %s\n", c.nodeName)
}

// ShouldCompile checks if the extension should be compiled
func (e *AppDynamicsExtension) ShouldCompile(ctx *extensions.Context) bool {
	if e.detectAppDynamicsService(ctx) {
		fmt.Println("AppDynamics service detected, beginning compilation")
		return true
	}
	return false
}

// Configure configures the extension
func (e *AppDynamicsExtension) Configure(ctx *extensions.Context) error {
	fmt.Println("Running AppDynamics extension method _configure")

	// Load and store service credentials in context
	creds := e.loadServiceCredentials(ctx)
	if creds != nil {
		ctx.Set("APPDYNAMICS_CREDENTIALS", creds)
	}

	return nil
}

// Compile installs/compiles the extension payload
func (e *AppDynamicsExtension) Compile(ctx *extensions.Context, installer *extensions.Installer) error {
	fmt.Println("Downloading AppDynamics package...")

	buildDir := ctx.GetString("BUILD_DIR")
	appdynamicsInstallDir := filepath.Join(buildDir, "appdynamics")

	if err := installer.InstallOnlyVersion("appdynamics", appdynamicsInstallDir); err != nil {
		return fmt.Errorf("failed to download AppDynamics package: %w", err)
	}

	fmt.Println("Downloaded AppDynamics package")
	return nil
}

// PreprocessCommands returns commands to run before app starts
func (e *AppDynamicsExtension) PreprocessCommands(ctx *extensions.Context) ([]string, error) {
	fmt.Println("Running AppDynamics preprocess commands")

	commands := []string{
		`echo "Installing AppDynamics package..."`,
		`PHP_EXT_DIR=$(find /home/vcap/app -name "no-debug-non-zts*" -type d)`,
		`chmod -R 755 /home/vcap`,
		`chmod -R 777 /home/vcap/app/appdynamics/appdynamics-php-agent-linux_x64/logs`,
		`if [ $APPD_CONF_SSL_ENABLED == "true" ] ; then export sslflag=-s ; echo sslflag set to $sslflag ; fi`,
		`/home/vcap/app/appdynamics/appdynamics-php-agent-linux_x64/install.sh ` +
			`$sslflag ` +
			`-a "$APPD_CONF_ACCOUNT_NAME@$APPD_CONF_ACCESS_KEY" ` +
			`-e "$PHP_EXT_DIR" ` +
			`-p "/home/vcap/app/php/bin" ` +
			`-i "/home/vcap/app/appdynamics/phpini" ` +
			`-v "$PHP_VERSION" ` +
			`--ignore-permissions ` +
			`"$APPD_CONF_CONTROLLER_HOST" ` +
			`"$APPD_CONF_CONTROLLER_PORT" ` +
			`"$APPD_CONF_APP" ` +
			`"$APPD_CONF_TIER" ` +
			`"$APPD_CONF_NODE:$CF_INSTANCE_INDEX" `,
		`cat /home/vcap/app/appdynamics/phpini/appdynamics_agent.ini >> /home/vcap/app/php/etc/php.ini`,
		`echo "AppDynamics installation complete"`,
	}

	return commands, nil
}

// ServiceCommands returns long-running service commands
func (e *AppDynamicsExtension) ServiceCommands(ctx *extensions.Context) (map[string]string, error) {
	// AppDynamics doesn't provide service commands
	return map[string]string{}, nil
}

// ServiceEnvironment returns environment variables for services
func (e *AppDynamicsExtension) ServiceEnvironment(ctx *extensions.Context) (map[string]string, error) {
	fmt.Println("Setting AppDynamics service environment variables")

	credsVal, ok := ctx.Get("APPDYNAMICS_CREDENTIALS")
	if !ok {
		return map[string]string{}, nil
	}

	creds, ok := credsVal.(*credentials)
	if !ok {
		return map[string]string{}, fmt.Errorf("invalid credentials type")
	}

	env := map[string]string{
		"PHP_VERSION":               "$(/home/vcap/app/php/bin/php-config --version | cut -d '.' -f 1,2)",
		"PHP_EXT_DIR":               "$(/home/vcap/app/php/bin/php-config --extension-dir | sed 's|/tmp/staged|/home/vcap|')",
		"APPD_CONF_CONTROLLER_HOST": creds.hostName,
		"APPD_CONF_CONTROLLER_PORT": creds.port,
		"APPD_CONF_ACCOUNT_NAME":    creds.accountName,
		"APPD_CONF_ACCESS_KEY":      creds.accountAccessKey,
		"APPD_CONF_SSL_ENABLED":     creds.sslEnabled,
		"APPD_CONF_APP":             creds.appName,
		"APPD_CONF_TIER":            creds.tierName,
		"APPD_CONF_NODE":            creds.nodeName,
	}

	return env, nil
}
