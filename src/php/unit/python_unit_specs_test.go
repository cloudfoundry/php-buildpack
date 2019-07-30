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

		var cmd *exec.Cmd
		if IsDockerAvailable() {
			image := "cloudfoundry/cflinuxfs2"

			err = exec.Command("docker", "pull", image).Run()
			Expect(err).ToNot(HaveOccurred())
			cmd = exec.Command("docker", "run", "--rm", "-e", "COMPOSER_GITHUB_OAUTH_TOKEN="+os.Getenv("COMPOSER_GITHUB_OAUTH_TOKEN"), "-e", "CF_STACK=cflinuxfs2", "-v", bpDir+":/buildpack2:ro", image, "bash", "-c", "cp -r /buildpack2 /buildpack; cd /buildpack; export TMPDIR=$(mktemp -d) && sudo apt-get install -y python-dev python-pip && pip install -r requirements.txt && ./run_tests.sh")
		} else {
			tmpDir, err := ioutil.TempDir("", "php-unit")
			Expect(err).ToNot(HaveOccurred())
			defer os.RemoveAll(tmpDir)

			cmd = exec.Command("./run_tests.sh")
			cmd.Env = append(os.Environ(), "TMPDIR="+tmpDir)
			cmd.Dir = bpDir
		}

		session, err := gexec.Start(cmd, GinkgoWriter, GinkgoWriter)
		Expect(err).ToNot(HaveOccurred())
		session.Wait(20 * time.Minute)
		Expect(session.ExitCode()).To(Equal(0))
	})
})
