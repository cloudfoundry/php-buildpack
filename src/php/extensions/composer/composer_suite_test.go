package composer_test

import (
	"testing"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

func TestComposer(t *testing.T) {
	RegisterFailHandler(Fail)
	RunSpecs(t, "Composer Extension Suite")
}
