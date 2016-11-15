import os
import os.path
import tempfile
import shutil
import json
from nose.tools import eq_
from nose.tools import with_setup
from build_pack_utils import utils
from common.integration import ErrorHelper
from common.components import BuildPackAssertHelper
from common.components import HttpdAssertHelper
from common.components import PhpAssertHelper
from common.components import NoWebServerAssertHelper
from common.components import AppDynamicsAssertHelper
from common.components import HhvmAssertHelper
from common.components import DownloadAssertHelper
from common.base import BaseCompileApp


appdynamics = utils.load_extension('extensions/appdynamics')


class TestAppDynamics(object):
    def setUp(self):
        self.build_dir = tempfile.mkdtemp('build-')
        self.php_dir = os.path.join(self.build_dir, 'php', 'etc')
        os.makedirs(self.php_dir)
        shutil.copy('defaults/config/php/5.5.x/php.ini', self.php_dir)

    def tearDown(self):
        if os.path.exists(self.build_dir):
            shutil.rmtree(self.build_dir)

    def testDefaults(self):
        ad = appdynamics.AppDynamicsInstaller(utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VM': 'php'
        }))
        eq_(True, 'APPDYNAMICS_HOST' in ad._ctx.keys())
        eq_(True, 'APPDYNAMICS_VERSION' in ad._ctx.keys())
        eq_(True, 'APPDYNAMICS_PACKAGE' in ad._ctx.keys())
        eq_(True, 'APPDYNAMICS_DOWNLOAD_URL' in ad._ctx.keys())
        eq_(True, 'APPDYNAMICS_STRIP' in ad._ctx.keys())

    def testShouldNotInstall(self):
        ad = appdynamics.AppDynamicsInstaller(utils.FormattedDict({
            'BUILD_DIR': self.build_dir
        }))
        eq_(False, ad.should_install())

    @with_setup(setup=setUp, teardown=tearDown)
    def testShouldInstall(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'APPDYNAMICS_LICENSE': 'JUNK_LICENSE',
            'VCAP_APPLICATION': {
                'name': 'app-name-1'
            },
            'PHP_VM': 'php'
        })
        ad = appdynamics.AppDynamicsInstaller(ctx)
        eq_(True, ad.should_install())
        eq_('x64', ad._php_arch)
        eq_('@{HOME}/php/lib/php/extensions/no-debug-non-zts-20121212',
            ad._php_extn_dir)
        eq_(False, ad._php_zts)
        eq_('20121212', ad._php_api)
        eq_('@{HOME}/appdynamics/agent/x64/appdynamics-20121212.so', ad.appdynamics_so)
        eq_('app-name-1', ad.app_name)
        eq_('JUNK_LICENSE', ad.license_key)
        eq_('@{HOME}/logs/appdynamics-daemon.log', ad.log_path)
        eq_('@{HOME}/appdynamics/daemon/appdynamics-daemon.x64', ad.daemon_path)
        eq_('@{HOME}/appdynamics/daemon.sock', ad.socket_path)
        eq_('@{HOME}/appdynamics/daemon.pid', ad.pid_path)

    @with_setup(setup=setUp, teardown=tearDown)
    def testShouldInstallService(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'VCAP_SERVICES': {
                'appdynamics': [{
                    'name': 'appdynamics',
                    'label': 'appdynamics',
                    'tags': ['Monitoring'],
                    'plan': 'standard',
                    'credentials': {'licenseKey': 'LICENSE'}}]
            },
            'VCAP_APPLICATION': {
                'name': 'app-name-1'
            },
            'PHP_VM': 'php'
        })
        ad = appdynamics.AppDynamicsInstaller(ctx)
        eq_(True, ad.should_install())
        eq_('x64', ad._php_arch)
        eq_('@{HOME}/php/lib/php/extensions/no-debug-non-zts-20121212',
            ad._php_extn_dir)
        eq_(False, ad._php_zts)
        eq_('20121212', ad._php_api)
        eq_('@{HOME}/appdynamics/agent/x64/appdynamics-20121212.so', ad.appdynamics_so)
        eq_('app-name-1', ad.app_name)
        eq_('LICENSE', ad.license_key)
        eq_('@{HOME}/logs/appdynamics-daemon.log', ad.log_path)
        eq_('@{HOME}/appdynamics/daemon/appdynamics-daemon.x64', ad.daemon_path)
        eq_('@{HOME}/appdynamics/daemon.sock', ad.socket_path)
        eq_('@{HOME}/appdynamics/daemon.pid', ad.pid_path)

    @with_setup(setup=setUp, teardown=tearDown)
    def testShouldInstallServiceAndManual(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'VCAP_SERVICES': {
                'appdynamics': [{
                    'name': 'appdynamics',
                    'label': 'appdynamics',
                    'tags': ['Monitoring'],
                    'plan': 'standard',
                    'credentials': {'licenseKey': 'LICENSE'}}]
            },
            'APPDYNAMICS_LICENSE': 'LICENSE2',
            'VCAP_APPLICATION': {
                'name': 'app-name-2'
            },
            'PHP_VM': 'php'
        })
        ad = appdynamics.AppDynamicsInstaller(ctx)
        eq_(True, ad.should_install())
        eq_('x64', ad._php_arch)
        eq_('@{HOME}/php/lib/php/extensions/no-debug-non-zts-20121212',
            ad._php_extn_dir)
        eq_(False, ad._php_zts)
        eq_('20121212', ad._php_api)
        eq_('@{HOME}/appdynamics/agent/x64/appdynamics-20121212.so', ad.appdynamics_so)
        eq_('app-name-2', ad.app_name)
        eq_('LICENSE2', ad.license_key)
        eq_('@{HOME}/logs/appdynamics-daemon.log', ad.log_path)
        eq_('@{HOME}/appdynamics/daemon/appdynamics-daemon.x64', ad.daemon_path)
        eq_('@{HOME}/appdynamics/daemon.sock', ad.socket_path)
        eq_('@{HOME}/appdynamics/daemon.pid', ad.pid_path)

    @with_setup(setup=setUp, teardown=tearDown)
    def testModifyPhpIni(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'APPDYNAMICS_LICENSE': 'JUNK_LICENSE',
            'VCAP_APPLICATION': {
                'name': 'app-name-1'
            },
            'PHP_VM': 'php'
        })
        ad = appdynamics.AppDynamicsInstaller(ctx)
        ad.modify_php_ini()
        with open(os.path.join(self.php_dir, 'php.ini'), 'rt') as php_ini:
            lines = php_ini.readlines()
        eq_(True, lines.index('extension=%s\n' % ad.appdynamics_so) >= 0)
        eq_(True, lines.index('[appdynamics]\n') >= 0)
        eq_(True, lines.index('appdynamics.license=JUNK_LICENSE\n') >= 0)
        eq_(True, lines.index('appdynamics.appname=%s\n' % ad.app_name) >= 0)


class TestAppDynamicsCompiled(BaseCompileApp):
    def __init__(self):
        self.app_name = 'app-1'

    def setUp(self):
        BaseCompileApp.setUp(self)
        os.environ['APPDYNAMICS_LICENSE'] = 'JUNK_LICENSE'
        os.environ['VCAP_APPLICATION'] = json.dumps({
            'name': 'app-name-1'
        })

    def test_with_httpd_and_appdynamics(self):
        # helpers to confirm the environment
        bp = BuildPackAssertHelper()
        ad = AppDynamicsAssertHelper()
        httpd = HttpdAssertHelper()
        php = PhpAssertHelper()
        # set web server to httpd, since that's what we're expecting here
        self.opts.set_web_server('httpd')
        # run the compile step of the build pack
        output = ErrorHelper().compile(self.bp)
        # confirm downloads
        DownloadAssertHelper(3, 2).assert_downloads_from_output(output)
        # confirm start script
        bp.assert_start_script_is_correct(self.build_dir)
        httpd.assert_start_script_is_correct(self.build_dir)
        php.assert_start_script_is_correct(self.build_dir)
        # confirm bp utils installed
        bp.assert_scripts_are_installed(self.build_dir)
        bp.assert_config_options(self.build_dir)
        # check env & proc files
        httpd.assert_contents_of_procs_file(self.build_dir)
        httpd.assert_contents_of_env_file(self.build_dir)
        php.assert_contents_of_procs_file(self.build_dir)
        php.assert_contents_of_env_file(self.build_dir)
        # webdir exists
        httpd.assert_web_dir_exists(self.build_dir, self.opts.get_webdir())
        # check php & httpd installed
        httpd.assert_files_installed(self.build_dir)
        php.assert_files_installed(self.build_dir)
        ad.assert_files_installed(self.build_dir)

    def test_with_httpd_hhvm_and_appdynamics(self):
        # helpers to confirm the environment
        bp = BuildPackAssertHelper()
        ad = AppDynamicsAssertHelper()
        httpd = HttpdAssertHelper()
        hhvm = HhvmAssertHelper()
        # set web server to httpd, since that's what we're expecting here
        self.opts.set_php_vm('hhvm')
        self.opts.set_hhvm_download_url(
            '/hhvm/{HHVM_VERSION}/{HHVM_PACKAGE}')
        self.opts.set_web_server('httpd')
        # run the compile step of the build pack
        output = ErrorHelper().compile(self.bp)
        # confirm downloads
        DownloadAssertHelper(2, 2).assert_downloads_from_output(output)
        # confirm start script
        bp.assert_start_script_is_correct(self.build_dir)
        httpd.assert_start_script_is_correct(self.build_dir)
        hhvm.assert_start_script_is_correct(self.build_dir)
        # confirm bp utils installed
        bp.assert_scripts_are_installed(self.build_dir)
        bp.assert_config_options(self.build_dir)
        # check env & proc files
        httpd.assert_contents_of_procs_file(self.build_dir)
        httpd.assert_contents_of_env_file(self.build_dir)
        hhvm.assert_contents_of_procs_file(self.build_dir)
        hhvm.assert_contents_of_env_file(self.build_dir)
        # webdir exists
        httpd.assert_web_dir_exists(self.build_dir, self.opts.get_webdir())
        # check php & httpd installed
        httpd.assert_files_installed(self.build_dir)
        hhvm.assert_files_installed(self.build_dir)
        # Test AppDynamics should not be installed w/HHVM
        ad.is_not_installed(self.build_dir)


class TestAppDynamicsWithApp5(BaseCompileApp):
    def __init__(self):
        self.app_name = 'app-5'

    def setUp(self):
        BaseCompileApp.setUp(self)
        os.environ['APPDYNAMICS_LICENSE'] = 'JUNK_LICENSE'
        os.environ['VCAP_APPLICATION'] = json.dumps({
            'name': 'app-name-1'
        })

    def test_standalone(self):
        # helpers to confirm the environment
        bp = BuildPackAssertHelper()
        php = PhpAssertHelper()
        none = NoWebServerAssertHelper()
        ad = AppDynamicsAssertHelper()
        # no web server
        self.opts.set_web_server('none')
        # run the compile step of the build pack
        output = ErrorHelper().compile(self.bp)
        # confirm downloads
        DownloadAssertHelper(2, 1).assert_downloads_from_output(output)
        # confirm httpd and nginx are not installed
        none.assert_no_web_server_is_installed(self.build_dir)
        # confirm start script
        bp.assert_start_script_is_correct(self.build_dir)
        php.assert_start_script_is_correct(self.build_dir)
        # confirm bp utils installed
        bp.assert_scripts_are_installed(self.build_dir)
        # check env & proc files
        none.assert_contents_of_procs_file(self.build_dir)
        php.assert_contents_of_env_file(self.build_dir)
        # webdir exists
        none.assert_no_web_dir(self.build_dir, self.opts.get_webdir())
        # check php cli installed
        none.assert_files_installed(self.build_dir)
        ad.assert_files_installed(self.build_dir)