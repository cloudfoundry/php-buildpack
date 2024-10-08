package unit_test

import (
	"os"
	"os/exec"
	"time"

	"github.com/cloudfoundry/libbuildpack/cutlass"
	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
	"github.com/onsi/gomega/gexec"
	"github.com/onsi/gomega/gbytes"
)

var _ = Describe("Compile", func() {
	Context("when running in an unsupported stack", func() {
		var cmd *exec.Cmd
		BeforeEach(func() {
			bpDir, err := cutlass.FindRoot()
			Expect(err).NotTo(HaveOccurred())

			if IsDockerAvailable() {
				cmd = exec.Command("docker", "run", "--rm", "-e", "'CF_STACK=unsupported'", "-e", "USE_SYSTEM_PYTHON=1", "-v", bpDir+":/buildpack:ro", "-w", "/buildpack", "cloudfoundry/cflinuxfs3", "./bin/compile", "/tmp/abcd", "/tmp/efgh")
			} else {
				cmd = exec.Command("./bin/compile", "/tmp/abcd", "/tmp/efgh")
				cmd.Env = append(os.Environ(), "CF_STACK=unsupported")
			}
			cmd.Dir = bpDir
		})

		It("fails with a very helpful error message", func() {
			session, err := gexec.Start(cmd, GinkgoWriter, GinkgoWriter)
			Expect(err).ToNot(HaveOccurred())

			Eventually(session.ExitCode, 120*time.Second).Should(Equal(44))
			Expect(session.Err).Should(gbytes.Say("not supported by this buildpack"))
		})
	})
})
