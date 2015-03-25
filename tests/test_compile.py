import shutil
import tempfile
import os.path
from nose.tools import eq_
from nose.tools import raises
from nose.tools import with_setup
from build_pack_utils import BuildPack
from build_pack_utils.runner import CalledProcessError 
from common.integration import FileAssertHelper
from common.integration import ErrorHelper
from common.components import BuildPackAssertHelper
from common.components import HttpdAssertHelper
from common.components import NginxAssertHelper
from common.components import PhpAssertHelper
from common.components import HhvmAssertHelper
from common.components import NoWebServerAssertHelper
from common.components import DownloadAssertHelper
from common.base import BaseCompileApp


class TestCompileApp1(BaseCompileApp):
    def __init__(self):
        self.app_name = 'app-1'

    def test_with_httpd(self):
        # helpers to confirm the environment
        bp = BuildPackAssertHelper()
        httpd = HttpdAssertHelper()
        php = PhpAssertHelper()
        # set web server to httpd, since that's what we're expecting here
        self.opts.set_web_server('httpd')
        # run the compile step of the build pack
        output = ErrorHelper().compile(self.bp)
        # confirm downloads
        DownloadAssertHelper(21, 2).assert_downloads_from_output(output)
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

    def test_with_nginx(self):
        # helpers to confirm the environment
        bp = BuildPackAssertHelper()
        nginx = NginxAssertHelper()
        php = PhpAssertHelper()
        # set web server to httpd, since that's what we're expecting here
        self.opts.set_web_server('nginx')
        # run the compile step of the build pack
        output = ErrorHelper().compile(self.bp)
        # confirm downloads
        DownloadAssertHelper(7, 2).assert_downloads_from_output(output)
        # confirm start script
        bp.assert_start_script_is_correct(self.build_dir)
        nginx.assert_start_script_is_correct(self.build_dir)
        php.assert_start_script_is_correct(self.build_dir)
        # confirm bp utils installed
        bp.assert_scripts_are_installed(self.build_dir)
        bp.assert_config_options(self.build_dir)
        # check env & proc files
        nginx.assert_contents_of_procs_file(self.build_dir)
        php.assert_contents_of_procs_file(self.build_dir)
        php.assert_contents_of_env_file(self.build_dir)
        # webdir exists
        nginx.assert_web_dir_exists(self.build_dir, self.opts.get_webdir())
        # check php & nginx installed
        nginx.assert_files_installed(self.build_dir)
        php.assert_files_installed(self.build_dir)


class TestCompileApp6(TestCompileApp1):
    def __init__(self):
        self.app_name = 'app-6'

    def setUp(self):
        TestCompileApp1.setUp(self)
        self.opts.set_webdir('public')

    def assert_app6_specifics(self):
        fah = FileAssertHelper()
        (fah.expect()
            .root(self.build_dir)
                .path('public')  # noqa
                .path('public', 'index.php')
                .path('public', 'info.php')
                .path('vendor')
                .path('vendor', 'lib.php')
                .path('.bp-config', 'options.json')
            .exists())

    def test_with_httpd(self):
        TestCompileApp1.test_with_httpd(self)
        # some app specific tests
        self.assert_app6_specifics()

    def test_with_nginx(self):
        TestCompileApp1.test_with_nginx(self)
        # some app specific tests
        self.assert_app6_specifics()


class TestCompileApp5(BaseCompileApp):
    def __init__(self):
        self.app_name = 'app-5'

    def test_standalone(self):
        # helpers to confirm the environment
        bp = BuildPackAssertHelper()
        php = PhpAssertHelper()
        none = NoWebServerAssertHelper()
        # no web server
        self.opts.set_web_server('none')
        # run the compile step of the build pack
        output = ErrorHelper().compile(self.bp)
        # confirm downloads
        none.assert_downloads_from_output(output)
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


class TestCompileWithProfileD(BaseCompileApp):
    def __init__(self):
        self.app_name = 'app-with-profile-d'

    def testProfileDNotOverridden(self):
        ErrorHelper().compile(self.bp)
        fah = FileAssertHelper()
        fah.expect().path(self.build_dir, '.profile.d',
                          'dontdelete.sh').exists()


class TestCompileUsingHHVM(BaseCompileApp):
    def __init__(self):
        self.app_name = 'app-1'

    def test_with_httpd(self):
        # helpers to confirm the environment
        bp = BuildPackAssertHelper()
        httpd = HttpdAssertHelper()
        hhvm = HhvmAssertHelper()
        # set web server to httpd, since that's what we're expecting here
        self.opts.set_php_vm('hhvm')
        self.opts.set_web_server('httpd')
        # run the compile step of the build pack
        output = ErrorHelper().compile(self.bp)
        # confirm downloads
        DownloadAssertHelper(16, 2).assert_downloads_from_output(output)
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
        # check for Apache TCP port
        hhvm.assert_server_ini_contains(self.build_dir,
                                        'hhvm.server.port = 9000')

    def test_with_nginx(self):
        # helpers to confirm the environment
        bp = BuildPackAssertHelper()
        nginx = NginxAssertHelper()
        hhvm = HhvmAssertHelper()
        self.opts.set_php_vm('hhvm')
        self.opts.set_web_server('nginx')
        # run the compile step of the build pack
        output = ErrorHelper().compile(self.bp)
        # confirm downloads
        DownloadAssertHelper(2, 2).assert_downloads_from_output(output)
        # confirm start script
        bp.assert_start_script_is_correct(self.build_dir)
        nginx.assert_start_script_is_correct(self.build_dir)
        hhvm.assert_start_script_is_correct(self.build_dir)
        # confirm bp utils installed
        bp.assert_scripts_are_installed(self.build_dir)
        bp.assert_config_options(self.build_dir)
        # check env & proc files
        nginx.assert_contents_of_procs_file(self.build_dir)
        hhvm.assert_contents_of_procs_file(self.build_dir)
        hhvm.assert_contents_of_env_file(self.build_dir)
        # webdir exists
        nginx.assert_web_dir_exists(self.build_dir, self.opts.get_webdir())
        # check hhvm & nginx installed
        nginx.assert_files_installed(self.build_dir)
        hhvm.assert_files_installed(self.build_dir)
        # check for Nginx socket config
        hhvm.assert_server_ini_contains(self.build_dir,
                                        'hhvm.server.file_socket')
        hhvm.assert_server_ini_contains(self.build_dir, 'php-fpm.socket')


class TestCompileWithInvalidJSON(object):
    def setUp(self):
        self.build_dir = tempfile.mkdtemp(prefix='build-')
        self.cache_dir = tempfile.mkdtemp(prefix='cache-')
        os.rmdir(self.build_dir)  # delete otherwise copytree complains
        os.rmdir(self.cache_dir)  # cache dir does not exist normally

    def tearDown(self):
        if os.path.exists(self.build_dir):
            shutil.rmtree(self.build_dir)
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)
        for name in os.listdir(os.environ['TMPDIR']):
            if name.startswith('httpd-') and name.endswith('.gz'):
                os.remove(os.path.join(os.environ['TMPDIR'], name))
            if name.startswith('php-') and name.endswith('.gz'):
                os.remove(os.path.join(os.environ['TMPDIR'], name))

    @with_setup(setup=setUp, teardown=tearDown)
    @raises(CalledProcessError)
    def test_compile_with_invalid_json(self):
        shutil.copytree('tests/data/app-invalid-json', self.build_dir)
        bp = BuildPack({
            'BUILD_DIR': self.build_dir,
            'CACHE_DIR': self.cache_dir,
            'WEBDIR': 'htdocs'
        }, '.')
        # simulate clone, makes debugging easier
        os.rmdir(bp.bp_dir)
        shutil.copytree('.', bp.bp_dir,
                        ignore=shutil.ignore_patterns("binaries",
                                                      "env",
                                                      "tests"))
        bp._compile().strip()


