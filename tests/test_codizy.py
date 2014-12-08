import os
import os.path
import tempfile
import shutil
from nose.tools import eq_
from build_pack_utils import utils
from dingus import Dingus
from common.integration import ErrorHelper
from common.components import BuildPackAssertHelper
from common.components import HttpdAssertHelper
from common.components import PhpAssertHelper
from common.components import DownloadAssertHelper
from common.components import CodizyAssertHelper
from common.base import BaseCompileApp


codizy_extn = utils.load_extension('extensions/codizy')


class TestCodizyInstaller(object):
    def setUp(self):
        self.build_dir = tempfile.mkdtemp(prefix='build-')
        phpCfgDir = os.path.join(self.build_dir, 'php', 'etc')
        os.makedirs(phpCfgDir)
        shutil.copy('defaults/config/php/5.4.x/php.ini',
                    phpCfgDir)
        shutil.copy('defaults/config/php/5.4.x/php-fpm.conf',
                    phpCfgDir)

    def tearDown(self):
        if os.path.exists(self.build_dir):
            shutil.rmtree(self.build_dir)

    def test_configure(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.4.33',
            'PHP_EXTENSIONS': []
        })
        codizy = codizy_extn.CodizyExtension(ctx)
        codizy._configure()
        eq_(True, 'xhprof' in ctx['PHP_EXTENSIONS'])
        eq_(True, 'codizy' in ctx['PHP_EXTENSIONS'])
        eq_(True, 'curl' in ctx['PHP_EXTENSIONS'])
        eq_(True, 'gettext' in ctx['PHP_EXTENSIONS'])
        eq_(True, 'mbstring' in ctx['PHP_EXTENSIONS'])
        eq_(True, 'openssl' in ctx['PHP_EXTENSIONS'])
        eq_(True, 'zlib' in ctx['PHP_EXTENSIONS'])
        eq_(7, len(ctx['PHP_EXTENSIONS']))
        eq_(True, 'ioncube' in ctx['ZEND_EXTENSIONS'])
        eq_(1, len(ctx['ZEND_EXTENSIONS']))

    def test_configure_doesnt_override_extns(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.4.33',
            'PHP_EXTENSIONS': ['a', 'b'],
            'ZEND_EXTENSIONS': ['opcache', 'xdebug']
        })
        codizy = codizy_extn.CodizyExtension(ctx)
        codizy._configure()
        eq_(True, 'xhprof' in ctx['PHP_EXTENSIONS'])
        eq_(True, 'codizy' in ctx['PHP_EXTENSIONS'])
        eq_(True, 'curl' in ctx['PHP_EXTENSIONS'])
        eq_(True, 'gettext' in ctx['PHP_EXTENSIONS'])
        eq_(True, 'mbstring' in ctx['PHP_EXTENSIONS'])
        eq_(True, 'openssl' in ctx['PHP_EXTENSIONS'])
        eq_(True, 'zlib' in ctx['PHP_EXTENSIONS'])
        eq_(True, 'a' in ctx['PHP_EXTENSIONS'])
        eq_(True, 'b' in ctx['PHP_EXTENSIONS'])
        eq_(9, len(ctx['PHP_EXTENSIONS']))
        eq_(True, 'ioncube' in ctx['ZEND_EXTENSIONS'])
        eq_('ioncube', ctx['ZEND_EXTENSIONS'][0])
        eq_(3, len(ctx['ZEND_EXTENSIONS']))

    def test_should_not_compile_php56(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.6.0'
        })
        codizy = codizy_extn.CodizyExtension(ctx)
        eq_(False, codizy._should_compile())

    def test_should_compile_not_set(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.4.33'
        })
        codizy = codizy_extn.CodizyExtension(ctx)
        eq_(False, codizy._should_compile())

    def test_should_compile_enabled(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.4.33',
            'CODIZY_INSTALL': True
        })
        codizy = codizy_extn.CodizyExtension(ctx)
        eq_(True, codizy._should_compile())

    def test_should_compile_enabled_but_not_supported(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.6.0',
            'CODIZY_INSTALL': True
        })
        codizy = codizy_extn.CodizyExtension(ctx)
        eq_(False, codizy._should_compile())

    def test_should_compile_service(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.4.33',
            'VCAP_SERVICES': {
                "rediscloud": [{"credentials": {}, "label": "rediscloud"}],
                "codizy": [{"credentials": {}, "label": "codizy"}]
            }
        })
        codizy = codizy_extn.CodizyExtension(ctx)
        eq_(True, codizy._should_compile())

    def test_should_compile_service_but_not_supported(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.6.0',
            'VCAP_SERVICES': {
                "rediscloud": [{"credentials": {}, "label": "rediscloud"}],
                "codizy": [{"credentials": {}, "label": "codizy"}]
            }
        })
        codizy = codizy_extn.CodizyExtension(ctx)
        eq_(False, codizy._should_compile())

    def test_compile(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.4.33',
            'VCAP_SERVICES': {
                "rediscloud": [{"credentials": {}, "label": "rediscloud"}],
                "codizy": [{"credentials": {}, "label": "codizy"}]
            }
        })
        codizy = codizy_extn.CodizyExtension(ctx)
        codizy._setup_codizy = Dingus()
        inst = Dingus()
        codizy.compile(inst)
        eq_(1, len(inst.package.calls()))
        eq_('CODIZY', inst.package.calls()[0].args[0])
        eq_(1, len(codizy._setup_codizy.calls()))

    def test_setup_codizy_no_auto_prepend_file(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.4.33',
            'CODIZY_INSTALL': True
        })
        codizy = codizy_extn.CodizyExtension(ctx)
        codizy.load_config()
        codizy._php_ini._lines = []
        eq_(0, len([line for line in codizy._php_ini._lines
                    if line.startswith('auto_prepend_file')]))
        codizy._setup_codizy()
        eq_(1, len([line for line in codizy._php_ini._lines
                    if line.startswith('auto_prepend_file')]))
        eq_('auto_prepend_file = @{HOME}/codizy/client/application/setup.php',
            codizy._php_ini._lines[0])

    def test_setup_codizy_empty_auto_prepend_file(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.4.33',
            'CODIZY_INSTALL': True
        })
        codizy = codizy_extn.CodizyExtension(ctx)
        codizy.load_config()
        codizy._php_ini._lines = ['auto_prepend_file =']
        eq_(1, len([line for line in codizy._php_ini._lines
                    if line.startswith('auto_prepend_file')]))
        codizy._setup_codizy()
        eq_(1, len([line for line in codizy._php_ini._lines
                    if line.startswith('auto_prepend_file')]))
        eq_('auto_prepend_file = @{HOME}/codizy/client/application/setup.php',
            codizy._php_ini._lines[0])

    def test_setup_codizy_existing_auto_prepend_file(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.4.33',
            'CODIZY_INSTALL': True
        })
        codizy = codizy_extn.CodizyExtension(ctx)
        codizy.load_config()
        codizy._php_ini._lines = ['auto_prepend_file = @{HOME}/php/file.php']
        eq_(1, len([line for line in codizy._php_ini._lines
                    if line.startswith('auto_prepend_file')]))
        codizy._setup_codizy()
        eq_(1, len([line for line in codizy._php_ini._lines
                    if line.startswith('auto_prepend_file')]))
        eq_('auto_prepend_file = @{HOME}/php/auto_prepend_file.php',
            codizy._php_ini._lines[0])
        path = os.path.join(ctx['BUILD_DIR'], 'php', 'auto_prepend_file.php')
        with open(path, 'rt') as fp:
            lines = fp.readlines()
        eq_(4, len(lines))
        eq_('    require("@{HOME}/php/file.php");\n', lines[1])
        eq_('    require("@{HOME}/codizy/client/application/setup.php");\n',
            lines[2])


class TestCompileCodizyWithPHP(BaseCompileApp):
    def __init__(self):
        self.app_name = 'app-1'

    def setUp(self):
        BaseCompileApp.setUp(self)
        self.opts.set_codizy_download_url(
            '{DOWNLOAD_URL}/codizy/{CODIZY_VERSION}/{CODIZY_PACKAGE}')
        os.environ['CODIZY_INSTALL'] = 'True'

    def test_compile_php_with_codizy(self):
        # helpers to confirm the environment
        bp = BuildPackAssertHelper()
        codizy = CodizyAssertHelper()
        httpd = HttpdAssertHelper()
        php = PhpAssertHelper()
        # set web server to httpd, since that's what we're expecting here
        self.opts.set_web_server('httpd')
        # run the compile step of the build pack
        output = ErrorHelper().compile(self.bp)
        # confirm downloads
        DownloadAssertHelper(28, 2).assert_downloads_from_output(output)
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
        codizy.assert_files_installed(self.build_dir)
