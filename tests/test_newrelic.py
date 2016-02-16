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
from common.components import NewRelicAssertHelper
from common.components import DownloadAssertHelper
from common.base import BaseCompileApp


newrelic = utils.load_extension('extensions/newrelic')


class TestNewRelic(object):
    def setUp(self):
        self.build_dir = tempfile.mkdtemp('build-')
        self.php_dir = os.path.join(self.build_dir, 'php', 'etc')
        os.makedirs(self.php_dir)
        shutil.copy('defaults/config/php/5.5.x/php.ini', self.php_dir)

    def tearDown(self):
        if os.path.exists(self.build_dir):
            shutil.rmtree(self.build_dir)

    def testDefaults(self):
        nr = newrelic.NewRelicInstaller(utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VM': 'php'
        }))
        eq_(True, 'NEWRELIC_HOST' in nr._ctx.keys())
        eq_(True, 'NEWRELIC_VERSION' in nr._ctx.keys())
        eq_(True, 'NEWRELIC_PACKAGE' in nr._ctx.keys())
        eq_(True, 'NEWRELIC_DOWNLOAD_URL' in nr._ctx.keys())
        eq_(True, 'NEWRELIC_STRIP' in nr._ctx.keys())

    def testShouldNotInstall(self):
        nr = newrelic.NewRelicInstaller(utils.FormattedDict({
            'BUILD_DIR': self.build_dir
        }))
        eq_(False, nr.should_install())

    @with_setup(setup=setUp, teardown=tearDown)
    def testShouldInstall(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'NEWRELIC_LICENSE': 'JUNK_LICENSE',
            'VCAP_APPLICATION': {
                'name': 'app-name-1'
            },
            'PHP_VM': 'php'
        })
        nr = newrelic.NewRelicInstaller(ctx)
        eq_(True, nr.should_install())
        eq_('x64', nr._php_arch)
        eq_('@{HOME}/php/lib/php/extensions/no-debug-non-zts-20121212',
            nr._php_extn_dir)
        eq_(False, nr._php_zts)
        eq_('20121212', nr._php_api)
        eq_('@{HOME}/newrelic/agent/x64/newrelic-20121212.so', nr.newrelic_so)
        eq_('app-name-1', nr.app_name)
        eq_('JUNK_LICENSE', nr.license_key)
        eq_('@{HOME}/logs/newrelic-daemon.log', nr.log_path)
        eq_('@{HOME}/newrelic/daemon/newrelic-daemon.x64', nr.daemon_path)
        eq_('@{HOME}/newrelic/daemon.sock', nr.socket_path)
        eq_('@{HOME}/newrelic/daemon.pid', nr.pid_path)

    @with_setup(setup=setUp, teardown=tearDown)
    def testShouldInstallService(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'VCAP_SERVICES': {
                'newrelic': [{
                    'name': 'newrelic',
                    'label': 'newrelic',
                    'tags': ['Monitoring'],
                    'plan': 'standard',
                    'credentials': {'licenseKey': 'LICENSE'}}]
            },
            'VCAP_APPLICATION': {
                'name': 'app-name-1'
            },
            'PHP_VM': 'php'
        })
        nr = newrelic.NewRelicInstaller(ctx)
        eq_(True, nr.should_install())
        eq_('x64', nr._php_arch)
        eq_('@{HOME}/php/lib/php/extensions/no-debug-non-zts-20121212',
            nr._php_extn_dir)
        eq_(False, nr._php_zts)
        eq_('20121212', nr._php_api)
        eq_('@{HOME}/newrelic/agent/x64/newrelic-20121212.so', nr.newrelic_so)
        eq_('app-name-1', nr.app_name)
        eq_('LICENSE', nr.license_key)
        eq_('@{HOME}/logs/newrelic-daemon.log', nr.log_path)
        eq_('@{HOME}/newrelic/daemon/newrelic-daemon.x64', nr.daemon_path)
        eq_('@{HOME}/newrelic/daemon.sock', nr.socket_path)
        eq_('@{HOME}/newrelic/daemon.pid', nr.pid_path)

    @with_setup(setup=setUp, teardown=tearDown)
    def testShouldInstallServiceAndManual(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'VCAP_SERVICES': {
                'newrelic': [{
                    'name': 'newrelic',
                    'label': 'newrelic',
                    'tags': ['Monitoring'],
                    'plan': 'standard',
                    'credentials': {'licenseKey': 'LICENSE'}}]
            },
            'NEWRELIC_LICENSE': 'LICENSE2',
            'VCAP_APPLICATION': {
                'name': 'app-name-2'
            },
            'PHP_VM': 'php'
        })
        nr = newrelic.NewRelicInstaller(ctx)
        eq_(True, nr.should_install())
        eq_('x64', nr._php_arch)
        eq_('@{HOME}/php/lib/php/extensions/no-debug-non-zts-20121212',
            nr._php_extn_dir)
        eq_(False, nr._php_zts)
        eq_('20121212', nr._php_api)
        eq_('@{HOME}/newrelic/agent/x64/newrelic-20121212.so', nr.newrelic_so)
        eq_('app-name-2', nr.app_name)
        eq_('LICENSE2', nr.license_key)
        eq_('@{HOME}/logs/newrelic-daemon.log', nr.log_path)
        eq_('@{HOME}/newrelic/daemon/newrelic-daemon.x64', nr.daemon_path)
        eq_('@{HOME}/newrelic/daemon.sock', nr.socket_path)
        eq_('@{HOME}/newrelic/daemon.pid', nr.pid_path)

    @with_setup(setup=setUp, teardown=tearDown)
    def testModifyPhpIni(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'NEWRELIC_LICENSE': 'JUNK_LICENSE',
            'VCAP_APPLICATION': {
                'name': 'app-name-1'
            },
            'PHP_VM': 'php'
        })
        nr = newrelic.NewRelicInstaller(ctx)
        nr.modify_php_ini()
        with open(os.path.join(self.php_dir, 'php.ini'), 'rt') as php_ini:
            lines = php_ini.readlines()
        eq_(True, lines.index('extension=%s\n' % nr.newrelic_so) >= 0)
        eq_(True, lines.index('[newrelic]\n') >= 0)
        eq_(True, lines.index('newrelic.license=JUNK_LICENSE\n') >= 0)
        eq_(True, lines.index('newrelic.appname=%s\n' % nr.app_name) >= 0)


class TestNewRelicCompiled(BaseCompileApp):
    def __init__(self):
        self.app_name = 'app-1'

    def setUp(self):
        BaseCompileApp.setUp(self)
        os.environ['NEWRELIC_LICENSE'] = 'JUNK_LICENSE'
        os.environ['VCAP_APPLICATION'] = json.dumps({
            'name': 'app-name-1'
        })

    def test_with_httpd_and_newrelic(self):
        # helpers to confirm the environment
        bp = BuildPackAssertHelper()
        nr = NewRelicAssertHelper()
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
        nr.assert_files_installed(self.build_dir)

class TestNewRelicWithApp5(BaseCompileApp):
    def __init__(self):
        self.app_name = 'app-5'

    def setUp(self):
        BaseCompileApp.setUp(self)
        os.environ['NEWRELIC_LICENSE'] = 'JUNK_LICENSE'
        os.environ['VCAP_APPLICATION'] = json.dumps({
            'name': 'app-name-1'
        })

    def test_standalone(self):
        # helpers to confirm the environment
        bp = BuildPackAssertHelper()
        php = PhpAssertHelper()
        none = NoWebServerAssertHelper()
        nr = NewRelicAssertHelper()
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
        nr.assert_files_installed(self.build_dir)
