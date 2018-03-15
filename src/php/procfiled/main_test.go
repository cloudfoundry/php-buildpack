package main_test

import (
	"io/ioutil"
	"os"
	"os/exec"
	"path/filepath"

	"github.com/cloudfoundry/libbuildpack"
	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
	"github.com/onsi/gomega/gexec"
)

var _ = Describe("procfiled", func() {
	var (
		tmpDir  string
		session *gexec.Session
	)

	BeforeEach(func() {
		var err error
		tmpDir, err = ioutil.TempDir("", "php.tmpdir")
		Expect(err).ToNot(HaveOccurred())
	})

	AfterEach(func() {
		if session != nil {
			session.Kill()
		}
		os.RemoveAll(tmpDir)
	})

	runCli := func(procfile map[string]string) *gexec.Session {
		Expect(libbuildpack.NewYAML().Write(filepath.Join(tmpDir, "Procfile"), procfile)).To(Succeed())
		session, err := gexec.Start(exec.Command(pathToCli, filepath.Join(tmpDir, "Procfile")), GinkgoWriter, GinkgoWriter)
		Expect(err).ToNot(HaveOccurred())
		return session
	}

	It("runs all processes in procfile", func() {
		session = runCli(map[string]string{"web": "echo hello web; sleep 100", "worker": "echo hello worker; sleep 100"})
		stdout := func() string { return string(session.Out.Contents()) }
		Eventually(stdout).Should(ContainSubstring("hello web"))
		Eventually(stdout).Should(ContainSubstring("hello worker"))
		Expect(session).ToNot(gexec.Exit())
	})

	It("exits with the exit code of the first exiter", func() {
		session = runCli(map[string]string{"web": "sleep 100", "worker": "exit 13"})
		Eventually(session).Should(gexec.Exit(13))
	})
})
