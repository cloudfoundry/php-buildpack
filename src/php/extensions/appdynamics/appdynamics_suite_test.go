package appdynamics_test

import (
	"testing"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

func TestAppDynamics(t *testing.T) {
	RegisterFailHandler(Fail)
	RunSpecs(t, "AppDynamics Extension Suite")
}
