package integration_test

import (
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
						Execute(name, filepath.Join(fixtures, "with_appdynamics"))
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
			context("app with network zone set", func() {
				it("sets the right network zone config", func() {
					_, logs, err := platform.Deploy.
						WithServices(map[string]switchblade.Service{
							"some-dynatrace": {
								"apitoken": "secretpaastoken",
								"apiurl":   dynatraceURI, "environmentid": "envid",
								"networkzone": "testzone",
							},
						}).
						WithEnv(map[string]string{
							"BP_DEBUG": "true",
						}).
						Execute(name, filepath.Join(fixtures, "with_dynatrace"))
					Expect(err).NotTo(HaveOccurred())

					Eventually(logs.String()).Should(SatisfyAll(
						ContainSubstring("Extracting Dynatrace OneAgent"),
						ContainSubstring("Setting DT_NETWORK_ZONE..."),
					))

					// Eventually(logs.String()).Should(SatisfyAll(
					// 	ContainSubstring("Initializing"),
					// 	ContainSubstring("Found one matching Dynatrace service"),
					// 	ContainSubstring("Downloading Dynatrace OneAgent Installer"),
					// 	ContainSubstring("Extracting Dynatrace OneAgent"),
					// 	ContainSubstring("Removing Dynatrace OneAgent Installer"),
					// 	ContainSubstring("Adding Dynatrace specific Environment Vars"),
					// 	ContainSubstring("Adding Dynatrace LD_PRELOAD settings"),
					// 	ContainSubstring("Agent path not found in manifest.json, using fallback"),
					// ))

					// Eventually(func() string {
					// 	cmd := exec.Command("docker", "container", "logs", deployment.Name)
					// 	output, err := cmd.CombinedOutput()
					// 	Expect(err).NotTo(HaveOccurred())
					// 	return string(output)
					// }).Should(
					// 	ContainSubstring("Installing AppDynamics package..."),
					// )
				})
			})
		})
	}
}
