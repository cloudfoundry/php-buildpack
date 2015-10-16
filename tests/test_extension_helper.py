import os
import sys
import tempfile
import shutil
from dingus import Dingus
from nose.tools import eq_
from build_pack_utils import utils
from extension_helpers import ExtensionHelper
from extension_helpers import PHPExtensionHelper


class TestPHPExtensionHelper(object):
    def setUp(self):
        self.build_dir = tempfile.mkdtemp(prefix='build-')
        self.phpCfgDir = os.path.join(self.build_dir, 'php', 'etc')
        os.makedirs(self.phpCfgDir)
        shutil.copy('defaults/config/php/5.5.x/php.ini',
                    self.phpCfgDir)
        shutil.copy('defaults/config/php/5.5.x/php-fpm.conf',
                    self.phpCfgDir)

    def tearDown(self):
        if os.path.exists(self.build_dir):
            shutil.rmtree(self.build_dir)

    def test_basic(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.5.30'
        })
        ext = PHPExtensionHelper(ctx)
        ext.load_config()
        eq_(2, len(ext._ctx))
        eq_({}, ext._services)
        eq_({}, ext._application)
        eq_(os.path.join(self.phpCfgDir, 'php.ini'), ext._php_ini_path)
        eq_(os.path.join(self.phpCfgDir, 'php-fpm.conf'), ext._php_fpm_path)
        eq_(1922, len(ext._php_ini._lines))
        eq_(518, len(ext._php_fpm._lines))
        eq_('20121212', ext._php_api)
        eq_(False, ext._should_compile())
        eq_(False, ext._should_configure())
        eq_(None, ext.configure())
        eq_((), ext.preprocess_commands())
        eq_({}, ext.service_commands())
        eq_({}, ext.service_environment())
        eq_(0, ext.compile(None))

    def test_merge_defaults(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.5.30',
            'SOME_JUNK': 'jkl;'
        })

        class MyExtn(PHPExtensionHelper):
            def _defaults(self):
                return {
                    'DEFAULT_JUNK': 'asdf',
                    'SOME_JUNK': 'qwerty'
                }
        ext = MyExtn(ctx)
        eq_(4, len(ext._ctx))
        eq_('asdf', ext._ctx['DEFAULT_JUNK'])
        eq_('jkl;', ext._ctx['SOME_JUNK'])
        eq_('5.5.30', ext._ctx['PHP_VERSION'])

    def test_compile_runs(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.5.30'
        })

        class MyExtn(PHPExtensionHelper):
            _compile = Dingus()

            def _should_compile(self):
                return True
        ext = MyExtn(ctx)
        ext.compile(None)
        eq_(1, len(MyExtn._compile.calls()))

    def test_compile_doesnt_run(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.5.30'
        })

        class MyExtn(PHPExtensionHelper):
            _compile = Dingus()

            def _should_compile(self):
                return False
        ext = MyExtn(ctx)
        ext.compile(None)
        eq_(0, len(MyExtn._compile.calls()))

    def test_configure_runs(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.5.30'
        })

        class MyExtn(PHPExtensionHelper):
            _configure = Dingus()

            def _should_configure(self):
                return True
        ext = MyExtn(ctx)
        ext.configure()
        eq_(1, len(MyExtn._configure.calls()))

    def test_configure_doesnt_run(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.5.30'
        })

        class MyExtn(PHPExtensionHelper):
            _configure = Dingus()

            def _should_configure(self):
                return False
        ext = MyExtn(ctx)
        ext.configure()
        eq_(0, len(MyExtn._configure.calls()))

    def test_preprocess_commands_runs(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.5.30'
        })

        class MyExtn(PHPExtensionHelper):
            _preprocess_commands = Dingus()

            def _should_compile(self):
                return True
        ext = MyExtn(ctx)
        ext.preprocess_commands()
        eq_(1, len(MyExtn._preprocess_commands.calls()))

    def test_preprocess_commands_doesnt_run(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.5.30'
        })

        class MyExtn(PHPExtensionHelper):
            _preprocess_commands = Dingus()

            def _should_compile(self):
                return False
        ext = MyExtn(ctx)
        ext.preprocess_commands()
        eq_(0, len(MyExtn._preprocess_commands.calls()))

    def test_service_commands_runs(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.5.30'
        })

        class MyExtn(PHPExtensionHelper):
            _service_commands = Dingus()

            def _should_compile(self):
                return True
        ext = MyExtn(ctx)
        ext.service_commands()
        eq_(1, len(MyExtn._service_commands.calls()))

    def test_service_commands_doesnt_run(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.5.30'
        })

        class MyExtn(PHPExtensionHelper):
            _service_commands = Dingus()

            def _should_compile(self):
                return False
        ext = MyExtn(ctx)
        ext.service_commands()
        eq_(0, len(MyExtn._service_commands.calls()))

    def test_service_environment_runs(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.5.30'
        })

        class MyExtn(PHPExtensionHelper):
            _service_environment = Dingus()

            def _should_compile(self):
                return True
        ext = MyExtn(ctx)
        ext.service_environment()
        eq_(1, len(MyExtn._service_environment.calls()))

    def test_service_environment_doesnt_run(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.5.30'
        })

        class MyExtn(PHPExtensionHelper):
            _service_environment = Dingus()

            def _should_compile(self):
                return False
        ext = MyExtn(ctx)
        ext.service_environment()
        eq_(0, len(MyExtn._service_environment.calls()))

    def test_register_extension_methods(self):
        ExtensionHelper.register(__name__)
        module = sys.modules[__name__]
        assert hasattr(module, 'configure')
        assert hasattr(module, 'preprocess_commands')
        assert hasattr(module, 'service_commands')
        assert hasattr(module, 'service_environment')
        assert hasattr(module, 'compile')
        assert None is configure({})  # noqa
        assert {} == service_commands({})  # noqa
        assert {} == service_environment({})  # noqa
        assert () == preprocess_commands({})  # noqa
