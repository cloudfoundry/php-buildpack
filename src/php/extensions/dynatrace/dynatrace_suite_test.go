package dynatrace_test

import (
	"testing"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

func TestDynatrace(t *testing.T) {
	RegisterFailHandler(Fail)
	RunSpecs(t, "Dynatrace Extension Suite")
}
