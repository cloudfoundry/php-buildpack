package newrelic_test

import (
	"testing"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
)

func TestNewRelic(t *testing.T) {
	RegisterFailHandler(Fail)
	RunSpecs(t, "NewRelic Extension Suite")
}
