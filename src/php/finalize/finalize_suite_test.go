package finalize_test

import (
	"testing"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

func TestFinalize(t *testing.T) {
	RegisterFailHandler(Fail)
	RunSpecs(t, "Finalize Suite")
}
