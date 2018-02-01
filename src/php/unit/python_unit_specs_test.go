package unit_test

import (
	"io/ioutil"
	"os"
	"os/exec"
	"time"

	"github.com/cloudfoundry/libbuildpack/cutlass"
	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
	"github.com/onsi/gomega/gexec"
)

var _ = Describe("python unit tests", func() {
	It("should all pass", func() {
		bpDir, err := cutlass.FindRoot()
		Expect(err).NotTo(HaveOccurred())

		cmd := exec.Command("docker", "system", "info")
		session, err := gexec.Start(cmd, nil, nil)
		Expect(err).ToNot(HaveOccurred())
		session.Wait()
		dockerAvailable := session.ExitCode() == 0

		if dockerAvailable {
			cmd = exec.Command("docker", "run", "--rm", "-e", "COMPOSER_GITHUB_OAUTH_TOKEN="+os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"), "-v", bpDir+":/buildpack2:ro", "cfbuildpacks/ci", "bash", "-c", "cp -r /buildpack2 /buildpack; cd /buildpack; export TMPDIR=$(mktemp -d) && pip install -r requirements.txt && ./run_tests.sh")
		} else {
			tmpDir, err := ioutil.TempDir("", "php-unit")
			Expect(err).ToNot(HaveOccurred())
			defer os.RemoveAll(tmpDir)

			cmd = exec.Command("./run_tests.sh")
			cmd.Env = []string{"TMPDIR=" + tmpDir, "COMPOSER_GITHUB_OAUTH_TOKEN=" + os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN")}
			cmd.Dir = bpDir
		}

		session, err = gexec.Start(cmd, GinkgoWriter, GinkgoWriter)
		Expect(err).ToNot(HaveOccurred())
		session.Wait(20 * time.Minute)
		Expect(session.ExitCode()).To(Equal(0))
	})
})
