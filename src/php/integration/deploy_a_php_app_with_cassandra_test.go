package integration_test

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"time"

	"github.com/cloudfoundry/libbuildpack/cutlass"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("CF PHP Buildpack", func() {
	var app *cutlass.App
	var serviceName string
	RunCf := func(args ...string) error {
		command := exec.Command("cf", args...)
		command.Stdout = GinkgoWriter
		command.Stderr = GinkgoWriter
		return command.Run()
	}

	BeforeEach(func() { serviceName = "cassandra-test-service" })
	AfterEach(func() {
		app = DestroyApp(app)
		_ = RunCf("delete-service", "-f", serviceName)
	})

	Context("deploying a basic PHP app using Cassandra module", func() {
		Context("after the Cassandra module has been loaded into PHP", func() {
			It("configures appdynamics", func() {
				app = cutlass.New(filepath.Join(bpDir, "fixtures", "with_cassandra"))
				app.SetEnv("COMPOSER_GITHUB_OAUTH_TOKEN", os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"))
				Expect(app.PushNoStart()).To(Succeed())

				cassandraHost, found := os.LookupEnv("CASSANDRA_HOST")
				if !found {
					cassandraHost = "1.1.1.1"
				}

				Expect(RunCf("cups", serviceName, "-p", fmt.Sprintf(`{"username":"uname","password":"pwd","node_ips":["%s"]}`, cassandraHost))).To(Succeed())
				Expect(RunCf("bind-service", app.Name, serviceName)).To(Succeed())
				Expect(RunCf("start", app.Name)).To(Succeed())

				ConfirmRunning(app)
				Expect(app.ConfirmBuildpack(buildpackVersion)).To(Succeed())

				if found {
					By("connects to and queries Cassandra server")
					Expect(app.GetBody("/")).To(ContainSubstring("<tr><td>system_auth</td><td>roles</td></tr>"))
				} else {
					By("logs that Cassandra could not connect to a server")

					_, headers, err := app.Get("/", nil)
					Expect(err).ToNot(HaveOccurred())
					Expect(headers["StatusCode"]).To(Equal([]string{"500"}))

					Eventually(app.Stdout.String, 10*time.Second).Should(ContainSubstring("No hosts available for the control connection"))
					Eventually(app.Stdout.String, 10*time.Second).Should(ContainSubstring("Cassandra\\\\DefaultCluster->connect()"))
				}
			})
		})
	})
})
