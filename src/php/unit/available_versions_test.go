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

	It("PHP_80_LATEST will have the latest 8.0 version", func() {
		latest, err := libbuildpack.FindMatchingVersion("8.0.x", versions)
		Expect(err).NotTo(HaveOccurred())

		Expect(defaults["PHP_80_LATEST"]).To(Equal(latest))
	})

	It("PHP_81_LATEST will have the latest 8.1 version", func() {
		latest, err := libbuildpack.FindMatchingVersion("8.1.x", versions)
		Expect(err).NotTo(HaveOccurred())

		Expect(defaults["PHP_81_LATEST"]).To(Equal(latest))
	})

	It("PHP_DEFAULT will have the latest 8.1 version", func() {
		latest, err := libbuildpack.FindMatchingVersion("8.1.x", versions)
		Expect(err).NotTo(HaveOccurred())

		Expect(defaults["PHP_DEFAULT"]).To(Equal(latest))
	})
})
