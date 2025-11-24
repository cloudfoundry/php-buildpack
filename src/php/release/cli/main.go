package main

import (
	"fmt"
)

func main() {
	// Output the release YAML
	// This defines the default process type for Cloud Foundry
	fmt.Println("default_process_types:")
	fmt.Println("  web: $HOME/.bp/bin/start")
}
