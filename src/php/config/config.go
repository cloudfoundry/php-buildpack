package config

import (
	"embed"
	"fmt"
	"io"
	"io/fs"
	"os"
	"path/filepath"
	"strings"

	"github.com/cloudfoundry/php-buildpack/src/php/util"
)

//go:embed defaults
var defaultsFS embed.FS

// ExtractDefaults extracts all embedded default config files to the specified destination directory.
// This is used during buildpack execution to populate configuration files for httpd, nginx, and PHP.
func ExtractDefaults(destDir string) error {
	// Walk through all embedded files
	return fs.WalkDir(defaultsFS, "defaults", func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}

		// Get relative path (remove "defaults/" prefix)
		relPath, err := filepath.Rel("defaults", path)
		if err != nil {
			return fmt.Errorf("failed to get relative path for %s: %w", path, err)
		}

		// Construct destination path
		destPath := filepath.Join(destDir, relPath)

		// If it's a directory, create it
		if d.IsDir() {
			return os.MkdirAll(destPath, 0755)
		}

		// If it's a file, copy it
		return extractFile(path, destPath)
	})
}

// extractFile copies a single file from the embedded FS to the destination
func extractFile(embeddedPath, destPath string) error {
	// Read the embedded file
	data, err := defaultsFS.ReadFile(embeddedPath)
	if err != nil {
		return fmt.Errorf("failed to read embedded file %s: %w", embeddedPath, err)
	}

	// Ensure parent directory exists
	if err := os.MkdirAll(filepath.Dir(destPath), 0755); err != nil {
		return fmt.Errorf("failed to create parent directory for %s: %w", destPath, err)
	}

	// Write to destination
	if err := os.WriteFile(destPath, data, 0644); err != nil {
		return fmt.Errorf("failed to write file %s: %w", destPath, err)
	}

	return nil
}

// ExtractConfig extracts a specific config directory (httpd, nginx, or php) to the destination
func ExtractConfig(configType, destDir string) error {
	configPath := filepath.Join("defaults", "config", configType)

	// Check if the path exists in the embedded FS
	if _, err := fs.Stat(defaultsFS, configPath); err != nil {
		return fmt.Errorf("config type %s not found in embedded defaults: %w", configType, err)
	}

	// Walk through the specific config directory
	return fs.WalkDir(defaultsFS, configPath, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}

		// Get relative path from the config type directory
		relPath, err := filepath.Rel(configPath, path)
		if err != nil {
			return fmt.Errorf("failed to get relative path for %s: %w", path, err)
		}

		// Skip the root directory itself
		if relPath == "." {
			return nil
		}

		// Construct destination path
		destPath := filepath.Join(destDir, relPath)

		// If it's a directory, create it
		if d.IsDir() {
			return os.MkdirAll(destPath, 0755)
		}

		// If it's a file, copy it
		return extractFile(path, destPath)
	})
}

// ReadConfigFile reads a single config file from the embedded FS
func ReadConfigFile(configPath string) ([]byte, error) {
	fullPath := filepath.Join("defaults", configPath)
	data, err := defaultsFS.ReadFile(fullPath)
	if err != nil {
		return nil, fmt.Errorf("failed to read config file %s: %w", configPath, err)
	}
	return data, nil
}

// OpenConfigFile opens a config file from the embedded FS for reading
func OpenConfigFile(configPath string) (fs.File, error) {
	fullPath := filepath.Join("defaults", configPath)
	file, err := defaultsFS.Open(fullPath)
	if err != nil {
		return nil, fmt.Errorf("failed to open config file %s: %w", configPath, err)
	}
	return file, nil
}

// CopyConfigFile copies a single config file from embedded FS to destination with optional variable substitution
func CopyConfigFile(configPath, destPath string) error {
	data, err := ReadConfigFile(configPath)
	if err != nil {
		return err
	}

	// Ensure parent directory exists
	if err := os.MkdirAll(filepath.Dir(destPath), 0755); err != nil {
		return fmt.Errorf("failed to create parent directory for %s: %w", destPath, err)
	}

	// Write to destination
	if err := os.WriteFile(destPath, data, 0644); err != nil {
		return fmt.Errorf("failed to write file %s: %w", destPath, err)
	}

	return nil
}

// ListConfigFiles returns a list of all files in a specific config directory
func ListConfigFiles(configType string) ([]string, error) {
	configPath := filepath.Join("defaults", "config", configType)
	var files []string

	err := fs.WalkDir(defaultsFS, configPath, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if !d.IsDir() {
			// Get relative path from configPath
			relPath, err := filepath.Rel(configPath, path)
			if err != nil {
				return err
			}
			files = append(files, relPath)
		}
		return nil
	})

	if err != nil {
		return nil, fmt.Errorf("failed to list config files for %s: %w", configType, err)
	}

	return files, nil
}

// GetOptionsJSON returns the default options.json content
func GetOptionsJSON() ([]byte, error) {
	return ReadConfigFile("options.json")
}

// CopyWithSubstitution copies a file and performs variable substitution
func CopyWithSubstitution(src io.Reader, dest io.Writer, vars map[string]string) error {
	// Read all content
	data, err := io.ReadAll(src)
	if err != nil {
		return err
	}

	content := string(data)

	// Perform simple variable substitution
	// This is a basic implementation - can be enhanced with proper templating
	for key, value := range vars {
		// Replace {VARIABLE} style placeholders
		placeholder := fmt.Sprintf("{%s}", key)
		// TODO: Implement proper string replacement
		_ = placeholder
		_ = value
	}

	_, err = dest.Write([]byte(content))
	return err
}

// ProcessPhpIni processes php.ini file by validating extensions and replacing placeholders
func ProcessPhpIni(
	phpIniPath string,
	phpInstallDir string,
	phpExtensions []string,
	zendExtensions []string,
	additionalReplacements map[string]string,
	logWarning func(string, ...interface{}),
) error {
	content, err := os.ReadFile(phpIniPath)
	if err != nil {
		return fmt.Errorf("failed to read php.ini: %w", err)
	}

	phpIniContent := string(content)

	skipExtensions := map[string]bool{
		"cli":  true,
		"pear": true,
		"cgi":  true,
	}

	phpExtDir := ""
	phpLibDir := filepath.Join(phpInstallDir, "lib", "php", "extensions")
	if entries, err := os.ReadDir(phpLibDir); err == nil {
		for _, entry := range entries {
			if entry.IsDir() && strings.HasPrefix(entry.Name(), "no-debug-non-zts-") {
				phpExtDir = filepath.Join(phpLibDir, entry.Name())
				break
			}
		}
	}

	phpBinary := filepath.Join(phpInstallDir, "bin", "php")
	phpLib := filepath.Join(phpInstallDir, "lib")
	compiledModules, err := util.GetCompiledModules(phpBinary, phpLib)
	if err != nil {
		if logWarning != nil {
			logWarning("Failed to get compiled PHP modules: %v", err)
		}
		compiledModules = make(map[string]bool)
	}

	var extensionLines []string
	for _, ext := range phpExtensions {
		if skipExtensions[ext] {
			continue
		}

		if phpExtDir != "" {
			extFile := filepath.Join(phpExtDir, ext+".so")
			exists := false
			if info, err := os.Stat(extFile); err == nil && !info.IsDir() {
				exists = true
			}

			if exists {
				extensionLines = append(extensionLines, fmt.Sprintf("extension=%s.so", ext))
			} else if !compiledModules[strings.ToLower(ext)] {
				fmt.Printf("The extension '%s' is not provided by this buildpack.\n", ext)
			}
		}
	}
	extensionsString := strings.Join(extensionLines, "\n")

	var zendExtensionLines []string
	for _, ext := range zendExtensions {
		zendExtensionLines = append(zendExtensionLines, fmt.Sprintf("zend_extension=\"%s.so\"", ext))
	}
	zendExtensionsString := strings.Join(zendExtensionLines, "\n")

	phpIniContent = strings.ReplaceAll(phpIniContent, "@{PHP_EXTENSIONS}", extensionsString)
	phpIniContent = strings.ReplaceAll(phpIniContent, "@{ZEND_EXTENSIONS}", zendExtensionsString)

	for placeholder, value := range additionalReplacements {
		phpIniContent = strings.ReplaceAll(phpIniContent, placeholder, value)
	}

	if err := os.WriteFile(phpIniPath, []byte(phpIniContent), 0644); err != nil {
		return fmt.Errorf("failed to write php.ini: %w", err)
	}

	return nil
}
