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
        DownloadAssertHelper(2, 2).assert_downloads_from_output(output)
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
        DownloadAssertHelper(2, 2).assert_downloads_from_output(output)
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


class TestCompileWithInvalidJSON(BaseCompileApp):
    def __init__(self):
        self.app_name = 'app-invalid-json'

    @raises(CalledProcessError)
    def test_compile_with_invalid_json(self):
        ErrorHelper().compile(self.bp)

