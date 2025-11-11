package main

import (
	"io"
	"os"
	"time"

	"github.com/cloudfoundry/libbuildpack"
	"github.com/cloudfoundry/php-buildpack/src/php/extensions"
	"github.com/cloudfoundry/php-buildpack/src/php/extensions/appdynamics"
	"github.com/cloudfoundry/php-buildpack/src/php/extensions/composer"
	"github.com/cloudfoundry/php-buildpack/src/php/extensions/dynatrace"
	"github.com/cloudfoundry/php-buildpack/src/php/extensions/newrelic"
	"github.com/cloudfoundry/php-buildpack/src/php/extensions/sessions"
	"github.com/cloudfoundry/php-buildpack/src/php/finalize"
	_ "github.com/cloudfoundry/php-buildpack/src/php/hooks"
)

func main() {
	logfile, err := os.CreateTemp("", "cloudfoundry.php-buildpack.finalize")
	defer logfile.Close()
	if err != nil {
		logger := libbuildpack.NewLogger(os.Stdout)
		logger.Error("Unable to create log file: %s", err.Error())
		os.Exit(8)
	}

	stdout := io.MultiWriter(os.Stdout, logfile)
	logger := libbuildpack.NewLogger(stdout)

	buildpackDir, err := libbuildpack.GetBuildpackDir()
	if err != nil {
		logger.Error("Unable to determine buildpack directory: %s", err.Error())
		os.Exit(9)
	}

	manifest, err := libbuildpack.NewManifest(buildpackDir, logger, time.Now())
	if err != nil {
		logger.Error("Unable to load buildpack manifest: %s", err.Error())
		os.Exit(10)
	}

	stager := libbuildpack.NewStager(os.Args[1:], logger, manifest)

	if err = manifest.ApplyOverride(stager.DepsDir()); err != nil {
		logger.Error("Unable to apply override.yml files: %s", err)
		os.Exit(17)
	}

	if err := stager.SetStagingEnvironment(); err != nil {
		logger.Error("Unable to setup environment variables: %s", err.Error())
		os.Exit(11)
	}

	// Set BP_DIR for use by finalize phase (e.g., copying binaries)
	os.Setenv("BP_DIR", buildpackDir)

	// Initialize extension registry and register all extensions
	registry := extensions.NewRegistry()
	registry.Register(&sessions.SessionsExtension{})
	registry.Register(&appdynamics.AppDynamicsExtension{})
	registry.Register(&dynatrace.DynatraceExtension{})
	registry.Register(&newrelic.NewRelicExtension{})
	registry.Register(&composer.ComposerExtension{})

	f := finalize.Finalizer{
		Stager:   stager,
		Manifest: manifest,
		Log:      logger,
		Logfile:  logfile,
		Command:  &libbuildpack.Command{},
		Registry: registry,
	}

	if err := finalize.Run(&f); err != nil {
		os.Exit(12)
	}

	if err := libbuildpack.RunAfterCompile(stager); err != nil {
		logger.Error("After Compile: %s", err.Error())
		os.Exit(13)
	}

	if err := stager.SetLaunchEnvironment(); err != nil {
		logger.Error("Unable to setup launch environment: %s", err.Error())
		os.Exit(14)
	}

	stager.StagingComplete()
}
