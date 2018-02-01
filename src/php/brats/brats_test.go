package brats_test

import (
	"path/filepath"
	"strings"

	"github.com/cloudfoundry/libbuildpack"
	"github.com/cloudfoundry/libbuildpack/bratshelper"
	"github.com/cloudfoundry/libbuildpack/cutlass"
	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

var _ = Describe("PHP buildpack", func() {
	bratshelper.DeployingAnAppWithAnUpdatedVersionOfTheSameBuildpack(CopyBrats)
	bratshelper.StagingWithBuildpackThatSetsEOL("php", CopyBrats)
	bratshelper.StagingWithADepThatIsNotTheLatest("php", CopyBrats)
	bratshelper.StagingWithCustomBuildpackWithCredentialsInDependencies(`php7\-[\d\.]+\-linux\-x64\-[\da-f]+\.tgz`, CopyBrats)
	bratshelper.DeployAppWithExecutableProfileScript("php", CopyBrats)
	bratshelper.DeployAnAppWithSensitiveEnvironmentVariables(CopyBrats)

	compatible := func(phpVersion, webserverVersion string) bool { return true }
	for _, webserver := range []string{"nginx", "httpd"} {
		webserver := webserver
		copyFunc := func(phpVersion, webserverVersion string) *cutlass.App {
			return CopyBratsWithFramework(phpVersion, webserver, webserverVersion)
		}
		bratshelper.ForAllSupportedVersions2("php", webserver, compatible, "with php-%s and web_server: "+webserver+"-%s", copyFunc, func(phpVersion, webserverVersion string, app *cutlass.App) {
			PushApp(app)

			var options struct {
				Extensions []string `json:"PHP_EXTENSIONS"`
			}
			Expect(libbuildpack.NewJSON().Load(filepath.Join(app.Path, ".bp-config", "options.json"), &options)).To(Succeed())
			Expect(options.Extensions).ToNot(BeEmpty())

			By("should have the correct version", func() {
				Expect(app.Stdout.String()).To(ContainSubstring("Installing PHP"))
				Expect(app.Stdout.String()).To(ContainSubstring("PHP " + phpVersion))
			})
			By("should load all of the modules specified in options.json", func() {
				body, err := app.GetBody("/?" + strings.Join(options.Extensions, ","))
				Expect(err).ToNot(HaveOccurred())
				for _, extension := range options.Extensions {
					Expect(body).To(ContainSubstring("SUCCESS: " + extension + " loads"))
				}
			})
			By("should not include any warning messages when loading all the extensions", func() {
				Expect(app.Stdout.String()).ToNot(MatchRegexp(`The extension .* is not provided by this buildpack.`))
			})
			By("should not load unknown module", func() {
				Expect(app.GetBody("/?something")).To(ContainSubstring("ERROR: something failed to load."))
			})
		})
	}
})
