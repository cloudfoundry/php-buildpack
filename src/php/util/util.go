package util

import (
	"fmt"
	"os"
	"os/exec"
	"strconv"
	"strings"
)

// UniqueStrings returns a slice with duplicate strings removed while preserving order
func UniqueStrings(input []string) []string {
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

// GetCompiledModules returns a list of built-in PHP modules by running `php -m`
func GetCompiledModules(phpBinPath, phpLibPath string) (map[string]bool, error) {
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

// CompareVersions compares two version strings in semantic version format.
// Returns -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2
func CompareVersions(v1, v2 string) int {
	parts1 := strings.Split(v1, ".")
	parts2 := strings.Split(v2, ".")

	maxLen := len(parts1)
	if len(parts2) > maxLen {
		maxLen = len(parts2)
	}

	for i := 0; i < maxLen; i++ {
		var p1, p2 int

		if i < len(parts1) {
			p1, _ = strconv.Atoi(parts1[i])
		}
		if i < len(parts2) {
			p2, _ = strconv.Atoi(parts2[i])
		}

		if p1 < p2 {
			return -1
		}
		if p1 > p2 {
			return 1
		}
	}

	return 0
}
