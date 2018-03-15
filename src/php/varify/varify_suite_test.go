package main_test

import (
	"os/exec"
	"testing"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
	"github.com/onsi/gomega/gexec"
)

func TestVarify(t *testing.T) {
	RegisterFailHandler(Fail)
	RunSpecs(t, "Varify Suite")
}

var pathToCli string
var _ = BeforeSuite(func() {
	var err error
	pathToCli, err = gexec.Build("php/varify")
	Expect(err).ToNot(HaveOccurred())
})

var _ = AfterSuite(func() {
	gexec.CleanupBuildArtifacts()
})

func runCli(tmpDir string, env []string) {
	command := exec.Command(pathToCli, tmpDir)
	command.Env = env
	session, err := gexec.Start(command, GinkgoWriter, GinkgoWriter)
	Expect(err).ToNot(HaveOccurred())
	Eventually(session).Should(gexec.Exit(0))
}
