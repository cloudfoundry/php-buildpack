package integration_test

import (
	"fmt"
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
			if t.Failed() && name != "" {
				t.Logf("❌ FAILED TEST - App/Container: %s", name)
				t.Logf("   Platform: %s", settings.Platform)
			}
			if name != "" && (!settings.KeepFailedContainers || !t.Failed()) {
				Expect(platform.Delete.Execute(name)).To(Succeed())
			}
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
						ContainSubstring("Setting AppDynamics Controller Binding Credentials"),
					))

					Eventually(deployment).Should(Serve(
						MatchRegexp("(?i)module_(Zend[+ ])?%s", "appdynamics_agent"),
					))
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
						ContainSubstring("Installing Dynatrace OneAgent"),
						ContainSubstring("Extracting Dynatrace OneAgent"),
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
						ContainSubstring("Installing Dynatrace OneAgent"),
						ContainSubstring("Fetching updated OneAgent configuration from tenant..."),
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
						ContainSubstring("More than one Dynatrace service found!"),
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
						ContainSubstring("Installing Dynatrace OneAgent"),
						ContainSubstring("Error during installer download, retrying in"),
						ContainSubstring("Dynatrace installer download failed, skipping"),
					))
				})
			})
		})

		context("newrelic", func() {
			context("app with newrelic configured", func() {
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
					))
				})
			})
		})
	}
}
