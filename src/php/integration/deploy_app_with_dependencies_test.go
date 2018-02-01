package integration_test

import (
	. "github.com/onsi/ginkgo"
)

var _ = Describe("CF PHP Buildpack", func() {
	AssertUsesProxyDuringStagingIfPresent("local_dependencies")
	AssertNoInternetTraffic("local_dependencies")
})
