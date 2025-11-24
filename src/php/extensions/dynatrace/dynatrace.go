package dynatrace

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strings"
	"time"

	"github.com/cloudfoundry/php-buildpack/src/php/extensions"
)

// DynatraceExtension downloads and configures Dynatrace OneAgent
type DynatraceExtension struct {
	detected         bool
	runInstaller     bool
	apiURL           string
	environmentID    string
	token            string
	skipErrors       string
	networkZone      string
	addTechnologies  string
	buildpackVersion string
	buildDir         string
	bpDir            string
	home             string
}

// Name returns the extension name
func (e *DynatraceExtension) Name() string {
	return "dynatrace"
}

// ShouldCompile determines if Dynatrace should be installed
func (e *DynatraceExtension) ShouldCompile(ctx *extensions.Context) bool {
	// Only run if PHP VM is 'php'
	if ctx.GetString("PHP_VM") != "php" {
		return false
	}

	// Load service info to detect Dynatrace
	e.loadServiceInfo(ctx)
	return e.detected
}

// loadServiceInfo searches for Dynatrace service and loads credentials
func (e *DynatraceExtension) loadServiceInfo(ctx *extensions.Context) {
	vcapServices := ctx.VcapServices
	var detectedServices []map[string]interface{}

	// Search through all service providers
	for _, services := range vcapServices {
		for _, service := range services {
			// Check if service name contains 'dynatrace'
			if strings.Contains(service.Name, "dynatrace") {
				// Get credentials
				envID, hasEnvID := service.Credentials["environmentid"]
				apiToken, hasToken := service.Credentials["apitoken"]

				if hasEnvID && hasToken && envID != nil && apiToken != nil {
					detectedServices = append(detectedServices, service.Credentials)
				}
			}
		}
	}

	if len(detectedServices) == 1 {
		// Found exactly one matching service
		creds := detectedServices[0]

		if apiURL, ok := creds["apiurl"].(string); ok {
			e.apiURL = apiURL
		}
		if envID, ok := creds["environmentid"].(string); ok {
			e.environmentID = envID
		}
		if token, ok := creds["apitoken"].(string); ok {
			e.token = token
		}
		if skipErrs, ok := creds["skiperrors"].(string); ok {
			e.skipErrors = skipErrs
		}
		if netZone, ok := creds["networkzone"].(string); ok {
			e.networkZone = netZone
		}
		if addTech, ok := creds["addtechnologies"].(string); ok {
			e.addTechnologies = addTech
		}

		// Convert API URL if not provided
		e.convertAPIURL()
		e.detected = true
		e.runInstaller = true
	} else if len(detectedServices) > 1 {
		fmt.Println("-----> WARNING: More than one Dynatrace service found!")
		e.detected = false
	}
}

// convertAPIURL sets the API URL from environment ID if not provided
func (e *DynatraceExtension) convertAPIURL() {
	if e.apiURL == "" && e.environmentID != "" {
		e.apiURL = fmt.Sprintf("https://%s.live.dynatrace.com/api", e.environmentID)
	}
}

// Configure runs early configuration
func (e *DynatraceExtension) Configure(ctx *extensions.Context) error {
	// Store context values for later use
	e.buildDir = ctx.GetString("BUILD_DIR")
	e.bpDir = ctx.GetString("BP_DIR")
	e.home = ctx.GetString("HOME")

	// Read buildpack version
	versionFile := filepath.Join(e.bpDir, "VERSION")
	if data, err := os.ReadFile(versionFile); err == nil {
		e.buildpackVersion = strings.TrimSpace(string(data))
	} else {
		e.buildpackVersion = "unknown"
	}

	return nil
}

// Compile downloads and installs the Dynatrace OneAgent
func (e *DynatraceExtension) Compile(ctx *extensions.Context, installer *extensions.Installer) error {
	if !e.detected {
		return nil
	}

	fmt.Println("-----> Installing Dynatrace OneAgent")

	// Create dynatrace directory
	dynatraceDir := filepath.Join(e.buildDir, "dynatrace")
	if err := os.MkdirAll(dynatraceDir, 0755); err != nil {
		return fmt.Errorf("failed to create dynatrace directory: %w", err)
	}

	// Download installer
	installerPath := e.getOneAgentInstallerPath()
	if err := e.downloadOneAgentInstaller(installerPath); err != nil {
		if e.skipErrors == "true" {
			fmt.Printf("-----> WARNING: Dynatrace installer download failed, skipping: %v\n", err)
			e.runInstaller = false
			return nil
		}
		return fmt.Errorf("dynatrace agent download failed: %w", err)
	}

	if !e.runInstaller {
		return nil
	}

	// Make installer executable
	if err := os.Chmod(installerPath, 0777); err != nil {
		return fmt.Errorf("failed to make installer executable: %w", err)
	}

	// Extract OneAgent
	fmt.Println("-----> Extracting Dynatrace OneAgent")
	if err := e.extractOneAgent(installerPath); err != nil {
		return fmt.Errorf("failed to extract OneAgent: %w", err)
	}

	// Remove installer
	fmt.Println("-----> Removing Dynatrace OneAgent Installer")
	os.Remove(installerPath)

	// Add environment variables
	fmt.Println("-----> Adding Dynatrace specific Environment Vars")
	if err := e.addingEnvironmentVariables(); err != nil {
		return fmt.Errorf("failed to add environment variables: %w", err)
	}

	// Add LD_PRELOAD settings
	fmt.Println("-----> Adding Dynatrace LD_PRELOAD settings")
	if err := e.addingLDPreloadSettings(); err != nil {
		return fmt.Errorf("failed to add LD_PRELOAD settings: %w", err)
	}

	// Update agent config from API
	fmt.Println("-----> Fetching updated OneAgent configuration from tenant...")
	if err := e.updateAgentConfig(); err != nil {
		if e.skipErrors == "true" {
			fmt.Printf("-----> WARNING: Failed to update agent config, continuing: %v\n", err)
		} else {
			return fmt.Errorf("failed to update agent config: %w", err)
		}
	}

	return nil
}

// getOneAgentInstallerPath returns the path to the installer
func (e *DynatraceExtension) getOneAgentInstallerPath() string {
	return filepath.Join(e.buildDir, "dynatrace", "paasInstaller.sh")
}

// downloadOneAgentInstaller downloads the OneAgent installer with retries
func (e *DynatraceExtension) downloadOneAgentInstaller(dest string) error {
	// Build download URL
	url := fmt.Sprintf("%s/v1/deployment/installer/agent/unix/paas-sh/latest?bitness=64&include=php&include=nginx&include=apache", e.apiURL)

	// Add additional technologies if specified
	if e.addTechnologies != "" {
		techs := strings.Split(e.addTechnologies, ",")
		for _, tech := range techs {
			url = fmt.Sprintf("%s&include=%s", url, strings.TrimSpace(tech))
		}
	}

	// Add network zone if specified
	if e.networkZone != "" {
		url = fmt.Sprintf("%s&networkZone=%s", url, e.networkZone)
	}

	return e.retryDownload(url, dest)
}

// retryDownload downloads a file with retry logic
func (e *DynatraceExtension) retryDownload(url, dest string) error {
	tries := 3
	baseWaitTime := 3

	var lastErr error
	for attempt := 0; attempt < tries; attempt++ {
		// Create HTTP request
		req, err := http.NewRequest("GET", url, nil)
		if err != nil {
			lastErr = err
			continue
		}

		// Add headers
		req.Header.Set("User-Agent", fmt.Sprintf("cf-php-buildpack/%s", e.buildpackVersion))
		req.Header.Set("Authorization", fmt.Sprintf("Api-Token %s", e.token))

		// Execute request
		client := &http.Client{Timeout: 5 * time.Minute}
		resp, err := client.Do(req)
		if err != nil {
			lastErr = err
			waitTime := baseWaitTime + (1 << attempt)
			fmt.Printf("-----> WARNING: Error during installer download, retrying in %d seconds\n", waitTime)
			time.Sleep(time.Duration(waitTime) * time.Second)
			continue
		}
		defer resp.Body.Close()

		if resp.StatusCode != http.StatusOK {
			lastErr = fmt.Errorf("download failed with status: %s", resp.Status)
			waitTime := baseWaitTime + (1 << attempt)
			fmt.Printf("-----> WARNING: Download failed with status %s, retrying in %d seconds\n", resp.Status, waitTime)
			time.Sleep(time.Duration(waitTime) * time.Second)
			continue
		}

		// Write to file
		file, err := os.Create(dest)
		if err != nil {
			return fmt.Errorf("failed to create file: %w", err)
		}
		defer file.Close()

		if _, err := io.Copy(file, resp.Body); err != nil {
			return fmt.Errorf("failed to write file: %w", err)
		}

		return nil
	}

	return lastErr
}

// extractOneAgent runs the installer to extract the agent
func (e *DynatraceExtension) extractOneAgent(installerPath string) error {
	cmd := exec.Command(installerPath, e.buildDir)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	return cmd.Run()
}

// addingEnvironmentVariables copies the dynatrace-env.sh file to .profile.d
func (e *DynatraceExtension) addingEnvironmentVariables() error {
	source := filepath.Join(e.buildDir, "dynatrace", "oneagent", "dynatrace-env.sh")
	destFolder := filepath.Join(e.buildDir, ".profile.d")
	dest := filepath.Join(destFolder, "dynatrace-env.sh")

	// Create .profile.d folder
	if err := os.MkdirAll(destFolder, 0755); err != nil {
		return fmt.Errorf("failed to create .profile.d directory: %w", err)
	}

	// Move the file
	if err := os.Rename(source, dest); err != nil {
		return fmt.Errorf("failed to move dynatrace-env.sh: %w", err)
	}

	return nil
}

// addingLDPreloadSettings adds LD_PRELOAD configuration to dynatrace-env.sh
func (e *DynatraceExtension) addingLDPreloadSettings() error {
	envFile := filepath.Join(e.buildDir, ".profile.d", "dynatrace-env.sh")

	// Determine agent path from manifest.json
	agentPath := e.getAgentPathFromManifest()
	if agentPath == "" {
		fmt.Println("-----> WARNING: Agent path not found in manifest.json, using fallback")
		agentPath = filepath.Join("agent", "lib64", "liboneagentproc.so")
	}

	// Prepend agent path with installer directory
	fullAgentPath := filepath.Join(e.home, "app", "dynatrace", "oneagent", agentPath)

	// Build extra environment variables
	extraEnv := fmt.Sprintf("\nexport LD_PRELOAD=\"%s\"", fullAgentPath)
	extraEnv += "\nexport DT_LOGSTREAM=${DT_LOGSTREAM:-stdout}"

	if e.networkZone != "" {
		extraEnv += fmt.Sprintf("\nexport DT_NETWORK_ZONE=\"${DT_NETWORK_ZONE:-%s}\"", e.networkZone)
	}

	// Append to file
	file, err := os.OpenFile(envFile, os.O_APPEND|os.O_WRONLY, 0644)
	if err != nil {
		return fmt.Errorf("failed to open dynatrace-env.sh: %w", err)
	}
	defer file.Close()

	if _, err := file.WriteString(extraEnv); err != nil {
		return fmt.Errorf("failed to write LD_PRELOAD settings: %w", err)
	}

	return nil
}

// getAgentPathFromManifest reads the agent path from manifest.json
func (e *DynatraceExtension) getAgentPathFromManifest() string {
	manifestFile := filepath.Join(e.buildDir, "dynatrace", "oneagent", "manifest.json")

	data, err := os.ReadFile(manifestFile)
	if err != nil {
		return ""
	}

	var manifest struct {
		Technologies struct {
			Process struct {
				LinuxX8664 []struct {
					BinaryType string `json:"binarytype"`
					Path       string `json:"path"`
				} `json:"linux-x86-64"`
			} `json:"process"`
		} `json:"technologies"`
	}

	if err := json.Unmarshal(data, &manifest); err != nil {
		return ""
	}

	// Find primary binary
	for _, entry := range manifest.Technologies.Process.LinuxX8664 {
		if entry.BinaryType == "primary" {
			return entry.Path
		}
	}

	return ""
}

// updateAgentConfig fetches the latest config from the API and merges it
func (e *DynatraceExtension) updateAgentConfig() error {
	configURL := fmt.Sprintf("%s/v1/deployment/installer/agent/processmoduleconfig", e.apiURL)

	// Fetch config from API
	req, err := http.NewRequest("GET", configURL, nil)
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("User-Agent", fmt.Sprintf("cf-php-buildpack/%s", e.buildpackVersion))
	req.Header.Set("Authorization", fmt.Sprintf("Api-Token %s", e.token))

	client := &http.Client{Timeout: 30 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("failed to fetch config from API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("config fetch failed with status: %s", resp.Status)
	}

	// Parse JSON response
	var apiConfig struct {
		Properties []struct {
			Section string `json:"section"`
			Key     string `json:"key"`
			Value   string `json:"value"`
		} `json:"properties"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&apiConfig); err != nil {
		return fmt.Errorf("failed to decode API config: %w", err)
	}

	// Convert API config to nested map
	configFromAPI := make(map[string]map[string]string)
	for _, prop := range apiConfig.Properties {
		section := fmt.Sprintf("[%s]", prop.Section)
		if configFromAPI[section] == nil {
			configFromAPI[section] = make(map[string]string)
		}
		configFromAPI[section][prop.Key] = prop.Value
	}

	// Read existing config file
	configPath := filepath.Join(e.buildDir, "dynatrace", "oneagent", "agent", "conf", "ruxitagentproc.conf")
	data, err := os.ReadFile(configPath)
	if err != nil {
		return fmt.Errorf("failed to read agent config file: %w", err)
	}

	// Parse existing config
	configFromAgent := e.parseAgentConfig(string(data))

	// Merge configs (API overwrites local)
	for section, values := range configFromAPI {
		if configFromAgent[section] == nil {
			configFromAgent[section] = make(map[string]string)
		}
		for key, value := range values {
			configFromAgent[section][key] = value
		}
	}

	// Write merged config back
	return e.writeAgentConfig(configPath, configFromAgent)
}

// parseAgentConfig parses the ruxitagentproc.conf format
func (e *DynatraceExtension) parseAgentConfig(data string) map[string]map[string]string {
	config := make(map[string]map[string]string)
	sectionRegex := regexp.MustCompile(`\[(.*)\]`)
	currentSection := ""

	lines := strings.Split(data, "\n")
	for _, line := range lines {
		line = strings.TrimSpace(line)

		// Check for section header
		if matches := sectionRegex.FindStringSubmatch(line); len(matches) > 0 {
			currentSection = line
			continue
		}

		// Skip comments and empty lines
		if strings.HasPrefix(line, "#") || line == "" {
			continue
		}

		// Parse key-value pair
		parts := strings.Fields(line)
		if len(parts) >= 2 {
			if config[currentSection] == nil {
				config[currentSection] = make(map[string]string)
			}
			key := parts[0]
			value := strings.Join(parts[1:], " ")
			config[currentSection][key] = value
		}
	}

	return config
}

// writeAgentConfig writes the config back to the file
func (e *DynatraceExtension) writeAgentConfig(path string, config map[string]map[string]string) error {
	file, err := os.Create(path)
	if err != nil {
		return fmt.Errorf("failed to create config file: %w", err)
	}
	defer file.Close()

	// Write sections
	for section, values := range config {
		if _, err := fmt.Fprintf(file, "%s\n", section); err != nil {
			return err
		}
		for key, value := range values {
			if _, err := fmt.Fprintf(file, "%s %s\n", key, value); err != nil {
				return err
			}
		}
		// Add blank line after each section
		if _, err := fmt.Fprintln(file); err != nil {
			return err
		}
	}

	return nil
}

// PreprocessCommands returns commands to run before app starts (none for Dynatrace)
func (e *DynatraceExtension) PreprocessCommands(ctx *extensions.Context) ([]string, error) {
	return nil, nil
}

// ServiceCommands returns long-running service commands (none for Dynatrace)
func (e *DynatraceExtension) ServiceCommands(ctx *extensions.Context) (map[string]string, error) {
	return nil, nil
}

// ServiceEnvironment returns environment variables for runtime (none for Dynatrace)
func (e *DynatraceExtension) ServiceEnvironment(ctx *extensions.Context) (map[string]string, error) {
	return nil, nil
}
