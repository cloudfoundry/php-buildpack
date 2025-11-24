package main

import (
	"io"
	"os"
	"path/filepath"
	"time"

	"github.com/cloudfoundry/libbuildpack"
	"github.com/cloudfoundry/php-buildpack/src/php/extensions"
	"github.com/cloudfoundry/php-buildpack/src/php/extensions/appdynamics"
	"github.com/cloudfoundry/php-buildpack/src/php/extensions/composer"
	"github.com/cloudfoundry/php-buildpack/src/php/extensions/dynatrace"
	"github.com/cloudfoundry/php-buildpack/src/php/extensions/newrelic"
	"github.com/cloudfoundry/php-buildpack/src/php/extensions/sessions"
	_ "github.com/cloudfoundry/php-buildpack/src/php/hooks"
	"github.com/cloudfoundry/php-buildpack/src/php/supply"
)

func main() {
	logfile, err := os.CreateTemp("", "cloudfoundry.php-buildpack.supply")
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
	installer := libbuildpack.NewInstaller(manifest)

	stager := libbuildpack.NewStager(os.Args[1:], logger, manifest)
	if err := stager.CheckBuildpackValid(); err != nil {
		os.Exit(11)
	}

	if err = installer.SetAppCacheDir(stager.CacheDir()); err != nil {
		logger.Error("Unable to setup appcache: %s", err)
		os.Exit(18)
	}
	if err = manifest.ApplyOverride(stager.DepsDir()); err != nil {
		logger.Error("Unable to apply override.yml files: %s", err)
		os.Exit(17)
	}

	err = libbuildpack.RunBeforeCompile(stager)
	if err != nil {
		logger.Error("Before Compile: %s", err.Error())
		os.Exit(12)
	}

	for _, dir := range []string{"bin", "lib", "include", "pkgconfig"} {
		if err := os.MkdirAll(filepath.Join(stager.DepDir(), dir), 0755); err != nil {
			logger.Error("Could not create directory: %s", err.Error())
			os.Exit(12)
		}
	}

	err = stager.SetStagingEnvironment()
	if err != nil {
		logger.Error("Unable to setup environment variables: %s", err.Error())
		os.Exit(13)
	}

	// Initialize extension registry and register all extensions
	registry := extensions.NewRegistry()
	registry.Register(&sessions.SessionsExtension{})
	registry.Register(&appdynamics.AppDynamicsExtension{})
	registry.Register(&dynatrace.DynatraceExtension{})
	registry.Register(&newrelic.NewRelicExtension{})
	registry.Register(&composer.ComposerExtension{})

	s := supply.Supplier{
		Logfile:   logfile,
		Stager:    stager,
		Manifest:  manifest,
		Installer: installer,
		Log:       logger,
		Command:   &libbuildpack.Command{},
		Registry:  registry,
	}

	err = supply.Run(&s)
	if err != nil {
		os.Exit(14)
	}

	if err := stager.WriteConfigYml(nil); err != nil {
		logger.Error("Error writing config.yml: %s", err.Error())
		os.Exit(15)
	}
	if err = installer.CleanupAppCache(); err != nil {
		logger.Error("Unable to clean up app cache: %s", err)
		os.Exit(19)
	}
}
