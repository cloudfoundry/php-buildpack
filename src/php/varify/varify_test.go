package main_test

import (
	"io/ioutil"
	"os"
	"path/filepath"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("varify", func() {
	var (
		tmpDir string
	)

	BeforeEach(func() {
		var err error
		tmpDir, err = ioutil.TempDir("", "php.tmpdir")
		Expect(err).ToNot(HaveOccurred())
	})

	AfterEach(func() {
		os.RemoveAll(tmpDir)
	})

	Describe("Run", func() {
		It("replaces {{.Port}} in all files under dir", func() {
			Expect(os.MkdirAll(filepath.Join(tmpDir, "a", "b"), 0755)).To(Succeed())
			Expect(ioutil.WriteFile(filepath.Join(tmpDir, "a", "b", "file"), []byte("Hi the port is {{.Port}}."), 0644)).To(Succeed())

			runCli(tmpDir, []string{"PORT=8080"})

			body, err := ioutil.ReadFile(filepath.Join(tmpDir, "a", "b", "file"))
			Expect(err).ToNot(HaveOccurred())
			Expect(string(body)).To(Equal("Hi the port is 8080."))
		})
	})
})
