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

	It("PHP_56_LATEST has the latest 5.6 version", func() {
		latest, err := libbuildpack.FindMatchingVersion("5.6.x", versions)
		Expect(err).NotTo(HaveOccurred())

		Expect(defaults["PHP_56_LATEST"]).To(Equal(latest))
	})

	It("PHP_70_LATEST has the latest 7.0 version", func() {
		latest, err := libbuildpack.FindMatchingVersion("7.0.x", versions)
		Expect(err).NotTo(HaveOccurred())

		Expect(defaults["PHP_70_LATEST"]).To(Equal(latest))
	})

	It("PHP_71_LATEST has the latest 7.1 version", func() {
		latest, err := libbuildpack.FindMatchingVersion("7.1.x", versions)
		Expect(err).NotTo(HaveOccurred())

		Expect(defaults["PHP_71_LATEST"]).To(Equal(latest))
	})

	It("PHP_72_LATEST has the latest 7.2 version", func() {
		latest, err := libbuildpack.FindMatchingVersion("7.2.x", versions)
		Expect(err).NotTo(HaveOccurred())

		Expect(defaults["PHP_72_LATEST"]).To(Equal(latest))
	})
})
