package main

import (
	"fmt"
	"os"

	"github.com/cloudfoundry/php-buildpack/src/php/detect"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "Usage: detect <build-dir>")
		os.Exit(1)
	}

	buildDir := os.Args[1]
	version := ""
	if len(os.Args) >= 3 {
		version = os.Args[2]
	}

	detector := &detect.Detector{
		BuildDir: buildDir,
		Version:  version,
	}

	if err := detect.Run(detector); err != nil {
		os.Exit(1)
	}

	os.Exit(0)
}
