package main

import (
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"path/filepath"
	"strings"
)

// rewriteFile replaces template patterns in a file with environment variable values
// Supports: @{VAR}, #{VAR}, @VAR@, and #VAR patterns
func rewriteFile(filePath string) error {
	// Read the file
	content, err := ioutil.ReadFile(filePath)
	if err != nil {
		return fmt.Errorf("failed to read file %s: %w", filePath, err)
	}

	result := string(content)

	// Replace patterns with braces: @{VAR} and #{VAR}
	result = replacePatterns(result, "@{", "}")
	result = replacePatterns(result, "#{", "}")

	// Replace patterns without braces: @VAR@ and #VAR (word boundary after)
	result = replaceSimplePatterns(result, "@", "@")
	result = replaceSimplePatterns(result, "#", "")

	// Write back to file
	err = ioutil.WriteFile(filePath, []byte(result), 0644)
	if err != nil {
		return fmt.Errorf("failed to write file %s: %w", filePath, err)
	}

	return nil
}

// replacePatterns replaces all occurrences of startDelim + VAR + endDelim with env var values
func replacePatterns(content, startDelim, endDelim string) string {
	result := content
	pos := 0

	for pos < len(result) {
		start := strings.Index(result[pos:], startDelim)
		if start == -1 {
			break
		}
		start += pos

		end := strings.Index(result[start+len(startDelim):], endDelim)
		if end == -1 {
			// No matching end delimiter, skip this start delimiter
			pos = start + len(startDelim)
			continue
		}
		end += start + len(startDelim)

		// Extract variable name
		varName := result[start+len(startDelim) : end]

		// Get environment variable value
		varValue := os.Getenv(varName)

		// Replace the pattern (keep pattern if variable not found - safe_substitute behavior)
		if varValue != "" {
			result = result[:start] + varValue + result[end+len(endDelim):]
			pos = start + len(varValue)
		} else {
			// Keep the pattern and continue searching after it
			pos = end + len(endDelim)
		}
	}

	return result
}

// replaceSimplePatterns replaces patterns like @VAR@ or #VAR (without braces)
// For #VAR patterns, endDelim is empty and we match until a non-alphanumeric/underscore character
func replaceSimplePatterns(content, startDelim, endDelim string) string {
	result := content
	pos := 0

	for pos < len(result) {
		start := strings.Index(result[pos:], startDelim)
		if start == -1 {
			break
		}
		start += pos

		// Find the end of the variable name
		varStart := start + len(startDelim)
		varEnd := varStart

		if endDelim != "" {
			// Pattern like @VAR@ - find matching end delimiter
			end := strings.Index(result[varStart:], endDelim)
			if end == -1 {
				pos = varStart
				continue
			}
			varEnd = varStart + end
		} else {
			// Pattern like #VAR - match until non-alphanumeric/underscore
			for varEnd < len(result) {
				c := result[varEnd]
				if !((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '_') {
					break
				}
				varEnd++
			}

			// If we didn't match any characters, skip this delimiter
			if varEnd == varStart {
				pos = varStart
				continue
			}
		}

		// Extract variable name
		varName := result[varStart:varEnd]

		// Skip if variable name is empty
		if varName == "" {
			pos = varStart
			continue
		}

		// Get environment variable value
		varValue := os.Getenv(varName)

		// Replace the pattern (keep pattern if variable not found - safe_substitute behavior)
		if varValue != "" {
			endPos := varEnd
			if endDelim != "" {
				endPos = varEnd + len(endDelim)
			}
			result = result[:start] + varValue + result[endPos:]
			pos = start + len(varValue)
		} else {
			// Keep the pattern and continue searching after it
			pos = varEnd
			if endDelim != "" {
				pos += len(endDelim)
			}
		}
	}

	return result
}

// rewriteConfigsRecursive walks a directory and rewrites all files
func rewriteConfigsRecursive(dirPath string) error {
	return filepath.Walk(dirPath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		// Skip directories
		if info.IsDir() {
			return nil
		}

		log.Printf("Rewriting config file: %s", path)
		return rewriteFile(path)
	})
}

func main() {
	if len(os.Args) != 2 {
		fmt.Fprintln(os.Stderr, "Argument required! Specify path to configuration directory.")
		os.Exit(1)
	}

	toPath := os.Args[1]

	// Check if path exists
	info, err := os.Stat(toPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Path [%s] not found.\n", toPath)
		os.Exit(1)
	}

	// Process directory or single file
	if info.IsDir() {
		log.Printf("Rewriting configuration under [%s]", toPath)
		err = rewriteConfigsRecursive(toPath)
	} else {
		log.Printf("Rewriting configuration file [%s]", toPath)
		err = rewriteFile(toPath)
	}

	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}
