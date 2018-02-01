package brats_test

import (
	"flag"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/cloudfoundry/libbuildpack"
	"github.com/cloudfoundry/libbuildpack/bratshelper"
	"github.com/cloudfoundry/libbuildpack/cutlass"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

func init() {
	flag.StringVar(&cutlass.DefaultMemory, "memory", "256M", "default memory for pushed apps")
	flag.StringVar(&cutlass.DefaultDisk, "disk", "384M", "default disk for pushed apps")
	flag.Parse()
}

var _ = SynchronizedBeforeSuite(func() []byte {
	// Run once
	return bratshelper.InitBpData().Marshal()
}, func(data []byte) {
	// Run on all nodes
	bratshelper.Data.Unmarshal(data)
	Expect(cutlass.CopyCfHome()).To(Succeed())
	cutlass.SeedRandom()
	cutlass.DefaultStdoutStderr = GinkgoWriter
})

var _ = SynchronizedAfterSuite(func() {
	// Run on all nodes
}, func() {
	// Run once
	_ = cutlass.DeleteOrphanedRoutes()
	Expect(cutlass.DeleteBuildpack(strings.Replace(bratshelper.Data.Cached, "_buildpack", "", 1))).To(Succeed())
	Expect(cutlass.DeleteBuildpack(strings.Replace(bratshelper.Data.Uncached, "_buildpack", "", 1))).To(Succeed())
	Expect(os.Remove(bratshelper.Data.CachedFile)).To(Succeed())
})

func TestBrats(t *testing.T) {
	RegisterFailHandler(Fail)
	RunSpecs(t, "Brats Suite")
}

func FirstOfVersionLine(line string) string {
	bpDir, err := cutlass.FindRoot()
	if err != nil {
		panic(err)
	}
	manifest, err := libbuildpack.NewManifest(bpDir, nil, time.Now())
	if err != nil {
		panic(err)
	}
	deps := manifest.AllDependencyVersions("php")
	versions, err := libbuildpack.FindMatchingVersions(line, deps)
	if err != nil {
		panic(err)
	}
	return versions[0]
}

func CopyBratsWithFramework(phpVersion, webserver, webserverVersion string) *cutlass.App {
	manifest, err := libbuildpack.NewManifest(bratshelper.Data.BpDir, nil, time.Now())
	Expect(err).ToNot(HaveOccurred())

	if phpVersion == "" {
		phpVersion = "x"
	}
	if strings.Contains(phpVersion, "x") {
		deps := manifest.AllDependencyVersions("php")
		phpVersion, err = libbuildpack.FindMatchingVersion(phpVersion, deps)
		Expect(err).ToNot(HaveOccurred())
	}

	if webserver == "" {
		webserver = "httpd"
	}
	if webserverVersion == "" {
		webserverVersion = "x"
	}
	if strings.Contains(webserverVersion, "x") {
		deps := manifest.AllDependencyVersions(webserver)
		webserverVersion, err = libbuildpack.FindMatchingVersion(webserverVersion, deps)
		Expect(err).ToNot(HaveOccurred())
	}

	dir, err := cutlass.CopyFixture(filepath.Join(bratshelper.Data.BpDir, "fixtures", "brats"))
	Expect(err).ToNot(HaveOccurred())

	commonExtensions := []string{"amqp", "apcu", "bz2", "cassandra", "curl", "dba", "exif", "fileinfo", "ftp", "gd", "geoip", "gettext", "gmp", "imagick", "imap", "ldap", "lua", "mailparse", "mbstring", "mongodb", "msgpack", "mysqli", "openssl", "pcntl", "pdo", "pdo_mysql", "pdo_pgsql", "pdo_sqlite", "pgsql", "phpiredis", "pspell", "rdkafka", "redis", "soap", "sockets", "xsl", "yaf", "zip", "zlib"}
	extraExtensions := map[string][]string{
		"5.6": {"mcrypt", "solr", "gearman", "igbinary", "memcache", "memcached", "mongo", "mssql", "mysql", "pdo_dblib", "phalcon", "protobuf", "protocolbuffers", "readline", "suhosin", "sundown", "twig", "xcache", "xhprof"},
		"7.0": {"mcrypt", "phalcon", "solr"},
		"7.1": {"mcrypt", "solr"},
		"7.2": {},
	}
	zendExtensions := map[string][]string{
		"5.6": {"ioncube", "opcache", "xdebug"},
		"7.0": {"ioncube", "opcache", "xdebug"},
		"7.1": {"ioncube", "opcache"},
		"7.2": {"ioncube", "opcache"},
	}

	options := make(map[string]interface{})
	options["PHP_VM"] = "php"
	options["PHP_VERSION"] = phpVersion
	options["WEB_SERVER"] = webserver
	options[strings.ToUpper(webserver)+"_VERSION"] = webserverVersion
	options["PHP_EXTENSIONS"] = append(commonExtensions, extraExtensions[phpVersion[:3]]...)
	options["ZEND_EXTENSIONS"] = zendExtensions[phpVersion[:3]]
	Expect(libbuildpack.NewJSON().Write(filepath.Join(dir, ".bp-config", "options.json"), options)).To(Succeed())

	return cutlass.New(dir)
}

func CopyBrats(version string) *cutlass.App {
	return CopyBratsWithFramework(version, "", "")
}

func PushApp(app *cutlass.App) {
	Expect(app.Push()).To(Succeed())
	Eventually(app.InstanceStates, 20*time.Second).Should(Equal([]string{"RUNNING"}))
}
