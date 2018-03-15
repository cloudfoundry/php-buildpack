package main_test

import (
	"testing"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
	"github.com/onsi/gomega/gexec"
)

func TestProcfiled(t *testing.T) {
	RegisterFailHandler(Fail)
	RunSpecs(t, "Procfiled Suite")
}

var pathToCli string
var _ = BeforeSuite(func() {
	var err error
	pathToCli, err = gexec.Build("php/procfiled")
	Expect(err).ToNot(HaveOccurred())
})

var _ = AfterSuite(func() {
	gexec.CleanupBuildArtifacts()
})
