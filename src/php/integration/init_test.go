package integration_test

import (
	"flag"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/cloudfoundry/switchblade"
	"github.com/onsi/gomega/format"
	"github.com/sclevine/spec"
	"github.com/sclevine/spec/report"

	. "github.com/onsi/gomega"
)

var settings struct {
	Buildpack struct {
		Version string
		Path    string
	}

	Cached               bool
	Serial               bool
	KeepFailedContainers bool
	FixturesPath         string
	GitHubToken          string
	Platform             string
	Stack                string
}

func init() {
	flag.BoolVar(&settings.Cached, "cached", false, "run cached buildpack tests")
	flag.BoolVar(&settings.Serial, "serial", false, "run serial buildpack tests")
	flag.BoolVar(&settings.KeepFailedContainers, "keep-failed-containers", false, "preserve failed test containers for debugging")
	flag.StringVar(&settings.Platform, "platform", "cf", `switchblade platform to test against ("cf" or "docker")`)
	flag.StringVar(&settings.GitHubToken, "github-token", "", "use the token to make GitHub API requests")
	flag.StringVar(&settings.Stack, "stack", "cflinuxfs4", "stack to use as default when pusing apps")
}

func TestIntegration(t *testing.T) {
	var Expect = NewWithT(t).Expect

	format.MaxLength = 0
	SetDefaultEventuallyTimeout(10 * time.Second)

	root, err := filepath.Abs("./../../..")
	Expect(err).NotTo(HaveOccurred())

	fixtures := filepath.Join(root, "fixtures")

	platform, err := switchblade.NewPlatform(settings.Platform, settings.GitHubToken, settings.Stack)
	Expect(err).NotTo(HaveOccurred())

	err = platform.Initialize(
		switchblade.Buildpack{
			Name: "php_buildpack",
			URI:  os.Getenv("BUILDPACK_FILE"),
		},
	)
	Expect(err).NotTo(HaveOccurred())

	// Dynatrace mock server temporarily disabled - not needed for basic extension tests
	// dynatraceName, err := switchblade.RandomName()
	// Expect(err).NotTo(HaveOccurred())
	// dynatraceDeployment, _, err := platform.Deploy.
	// 	WithBuildpacks("go_buildpack").
	// 	Execute(dynatraceName, filepath.Join(fixtures, "util", "dynatrace"))
	// Expect(err).NotTo(HaveOccurred())

	suite := spec.New("integration", spec.Report(report.Terminal{}), spec.Parallel())
	suite("Default", testDefault(platform, fixtures))
	suite("Modules", testModules(platform, fixtures))
	suite("Composer", testComposer(platform, fixtures))
	suite("WebServers", testWebServers(platform, fixtures))
	suite("AppFrameworks", testAppFrameworks(platform, fixtures))
	suite("Placeholders", testPlaceholders(platform, fixtures))
	suite("PreprocessCmds", testPreprocessCmds(platform, fixtures))
	suite("StandaloneApp", testStandaloneApp(platform, fixtures))
	// suite("BuildpackPythonExtension", testPythonExtension(platform, fixtures)) // Skipped for now
	// suite("APMs", testAPMs(platform, fixtures, dynatraceDeployment.InternalURL)) // Needs dynatrace mock
	if settings.Cached {
		suite("Offline", testOffline(platform, fixtures))
	}

	suite.Run(t)

	Expect(os.Remove(os.Getenv("BUILDPACK_FILE"))).To(Succeed())
	Expect(platform.Deinitialize()).To(Succeed())
}
