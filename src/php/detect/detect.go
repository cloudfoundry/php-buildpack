package detect

import (
	"fmt"
	"os"
	"path/filepath"
)

type Detector struct {
	BuildDir string
	Version  string
}

// Run performs PHP app detection
func Run(d *Detector) error {
	// Check for composer.json
	if _, err := os.Stat(filepath.Join(d.BuildDir, "composer.json")); err == nil {
		fmt.Printf("php %s\n", d.Version)
		return nil
	}

	// Check for .php files recursively
	found := false
	err := filepath.Walk(d.BuildDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		if !info.IsDir() && filepath.Ext(path) == ".php" {
			found = true
			return filepath.SkipAll
		}
		return nil
	})
	if err != nil {
		return err
	}
	if found {
		fmt.Printf("php %s\n", d.Version)
		return nil
	}

	// Check for webdir - looking for common web directories
	webdirs := []string{"htdocs", "public", "web", "www"}
	for _, dir := range webdirs {
		if _, err := os.Stat(filepath.Join(d.BuildDir, dir)); err == nil {
			fmt.Printf("php %s\n", d.Version)
			return nil
		}
	}

	// No PHP app detected
	return fmt.Errorf("no PHP app detected")
}
