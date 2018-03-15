package main_test

import (
	"io/ioutil"
	"os"
	"os/exec"
	"path/filepath"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("varify", func() {
	var (
		cliPath  string
		buildDir string
	)

	BeforeEach(func() {
		var err error
		buildDir, err = ioutil.TempDir("", "php.builddir")
		Expect(err).ToNot(HaveOccurred())
		cliPath = filepath.Join(os.Getenv("GOPATH"), "bin", "detect")
		Expect(cliPath).To(BeAnExistingFile())
	})

	AfterEach(func() {
		os.RemoveAll(buildDir)
	})

	runCli := func() (string, error) {
		b, err := exec.Command(cliPath, buildDir).Output()
		return string(b), err
	}

	Describe("Run", func() {
		Context("files with php extension", func() {
			BeforeEach(func() {
				Expect(os.MkdirAll(filepath.Join(buildDir, "a", "b"), 0755)).To(Succeed())
				Expect(ioutil.WriteFile(filepath.Join(buildDir, "a", "b", "file.php"), []byte{}, 0644)).To(Succeed())
			})
			It("returns true", func() {
				Expect(runCli()).To(ContainSubstring("php"))
			})
		})
		Context("asp.net app", func() {
			BeforeEach(func() {
				Expect(os.MkdirAll(filepath.Join(buildDir, "src", "asp-app"), 0755)).To(Succeed())
				Expect(ioutil.WriteFile(filepath.Join(buildDir, "src", "asp-app", "Startup.cs"), []byte{}, 0644)).To(Succeed())
			})
			It("returns false", func() {
				output, err := runCli()
				Expect(err).To(HaveOccurred())
				Expect(output).To(Equal("no\n"))
			})
		})
	})
})
