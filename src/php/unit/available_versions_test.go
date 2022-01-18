package unit_test

import (
	"path/filepath"
	"time"

	"github.com/cloudfoundry/libbuildpack"
	"github.com/cloudfoundry/libbuildpack/cutlass"
	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("Options.JSON", func() {
	var versions []string
	var defaults map[string]interface{}
	BeforeEach(func() {
		bpDir, err := cutlass.FindRoot()
		Expect(err).NotTo(HaveOccurred())

		Expect(libbuildpack.NewJSON().Load(filepath.Join(bpDir, "defaults", "options.json"), &defaults)).To(Succeed())

		manifest, err := libbuildpack.NewManifest(bpDir, nil, time.Now())
		Expect(err).NotTo(HaveOccurred())
		versions = manifest.AllDependencyVersions("php")
	})

	It("PHP_74_LATEST will have the latest 7.4 version", func() {
		latest, err := libbuildpack.FindMatchingVersion("7.4.x", versions)
		Expect(err).NotTo(HaveOccurred())

		Expect(defaults["PHP_74_LATEST"]).To(Equal(latest))
	})
})
