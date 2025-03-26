package integration_test

import (
	"fmt"
	"os/exec"
	"path/filepath"
	"testing"

	"github.com/cloudfoundry/switchblade"
	"github.com/sclevine/spec"

	. "github.com/cloudfoundry/switchblade/matchers"
	. "github.com/onsi/gomega"
)

func testAPMs(platform switchblade.Platform, fixtures, dynatraceURI string) func(*testing.T, spec.G, spec.S) {
	return func(t *testing.T, context spec.G, it spec.S) {
		var (
			Expect     = NewWithT(t).Expect
			Eventually = NewWithT(t).Eventually

			name string
		)

		it.Before(func() {
			var err error
			name, err = switchblade.RandomName()
			Expect(err).NotTo(HaveOccurred())
		})

		it.After(func() {
			Expect(platform.Delete.Execute(name)).To(Succeed())
		})

		context("appdynamics", func() {
			context("app with appdynamics configured", func() {
				it("sets the right config on build", func() {
					deployment, logs, err := platform.Deploy.
						WithServices(map[string]switchblade.Service{
							"appdynamics": {
								"account-access-key": "fe244dc3-372f-4d36-83b0-379973103c5c",
								"account-name":       "customer1", "host-name": "testhostname.com",
								"port":        "8090",
								"ssl-enabled": "False",
							},
						}).
						WithEnv(map[string]string{
							"BP_DEBUG": "true",
						}).
						Execute(name, filepath.Join(fixtures, "default"))
					Expect(err).NotTo(HaveOccurred())

					Eventually(logs.String()).Should(SatisfyAll(
						ContainSubstring("AppDynamics service detected, beginning compilation"),
						ContainSubstring("Running AppDynamics extension method _configure"),
						ContainSubstring("Setting AppDynamics credentials info..."),
						ContainSubstring("Downloading AppDynamics package..."),
					))

					Eventually(deployment).Should(Serve(
						MatchRegexp("(?i)module_(Zend[+ ])?%s", "appdynamics_agent"),
					))

					Eventually(func() string {
						cmd := exec.Command("docker", "container", "logs", deployment.Name)
						output, err := cmd.CombinedOutput()
						Expect(err).NotTo(HaveOccurred())
						return string(output)
					}).Should(
						ContainSubstring("Installing AppDynamics package..."),
					)
				})
			})
		})

		context("dynatrace", func() {
			context("app with single service and network zone set", func() {
				it("sets the right network zone config", func() {
					_, logs, err := platform.Deploy.
						WithServices(map[string]switchblade.Service{
							"some-dynatrace": {
								"apitoken":      "secretpaastoken",
								"apiurl":        dynatraceURI,
								"environmentid": "envid",
								"networkzone":   "testzone",
							},
						}).
						WithEnv(map[string]string{
							"BP_DEBUG": "true",
						}).
						Execute(name, filepath.Join(fixtures, "default"))
					Expect(err).NotTo(HaveOccurred())

					Eventually(logs.String()).Should(SatisfyAll(
						ContainSubstring("Extracting Dynatrace OneAgent"),
						ContainSubstring("Setting DT_NETWORK_ZONE..."),
					))
				})
			})

			context("app with single service and check for additional code modules", func() {
				it("adds additional code modules", func() {
					_, logs, err := platform.Deploy.
						WithServices(map[string]switchblade.Service{
							"some-dynatrace": {
								"apitoken":        "secretpaastoken",
								"apiurl":          dynatraceURI,
								"environmentid":   "envid",
								"networkzone":     "testzone",
								"addtechnologies": "go,nodejs",
							},
						}).
						WithEnv(map[string]string{
							"BP_DEBUG": "true",
						}).
						Execute(name, filepath.Join(fixtures, "default"))
					Expect(err).NotTo(HaveOccurred())

					Eventually(logs.String()).Should(SatisfyAll(
						ContainSubstring("Fetching updated OneAgent configuration from tenant..."),
						ContainSubstring("Finished writing updated OneAgent config back to"),
						ContainSubstring("Adding additional code module to download: go"),
						ContainSubstring("Adding additional code module to download: nodejs"),
					))
				})
			})

			context("multiple dynatrace services", func() {
				it("sets the right config", func() {
					_, logs, err := platform.Deploy.
						WithServices(map[string]switchblade.Service{
							"dynatrace1": {
								"apitoken":      "secretpaastoken",
								"apiurl":        dynatraceURI,
								"environmentid": "envid",
							},
							"dynatrace2": {
								"apitoken":      "secretpaastoken",
								"apiurl":        dynatraceURI,
								"environmentid": "envid2",
							},
						}).
						WithEnv(map[string]string{
							"BP_DEBUG": "true",
						}).
						Execute(name, filepath.Join(fixtures, "default"))
					Expect(err).To(HaveOccurred())
					Expect(err).To(MatchError(ContainSubstring("App staging failed")))

					Eventually(logs.String()).Should(SatisfyAll(
						ContainSubstring("More than one matching service found!"),
					))
				})
			})

			context("app with wrong url and skiperrors set to true", func() {
				it("sets the right network zone config", func() {
					_, logs, err := platform.Deploy.
						WithServices(map[string]switchblade.Service{
							"some-dynatrace": {
								"apitoken":      "secretpaastoken",
								"apiurl":        fmt.Sprintf("%s/no-such-endpoint", dynatraceURI),
								"environmentid": "envid",
								"skiperrors":    "true",
							},
						}).
						WithEnv(map[string]string{
							"BP_DEBUG": "true",
						}).
						Execute(name, filepath.Join(fixtures, "default"))
					Expect(err).NotTo(HaveOccurred())

					Eventually(logs.String()).Should(SatisfyAll(
						ContainSubstring("Found one matching Dynatrace service"),
						ContainSubstring("Downloading Dynatrace OneAgent Installer"),
						ContainSubstring("Error during installer download, retrying in"),
						ContainSubstring("Error during installer download, skipping installation"),
					))
				})
			})
		})

		context("newrelic", func() {
			context("app with appdynamics configured", func() {
				it("sets the right config on build", func() {
					_, logs, err := platform.Deploy.
						WithEnv(map[string]string{
							"NEWRELIC_LICENSE": "mock_license",
							"BP_DEBUG":         "true",
						}).
						Execute(name, filepath.Join(fixtures, "default"))
					Expect(err).NotTo(HaveOccurred())

					Eventually(logs.String()).Should(SatisfyAll(
						ContainSubstring("Installing NewRelic"),
						ContainSubstring("NewRelic Installed"),
						ContainSubstring("Using NewRelic default version:"),
					))
				})
			})
		})
	}
}
