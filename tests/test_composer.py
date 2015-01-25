import tempfile
from nose.tools import eq_
from dingus import Dingus
from dingus import patch
from build_pack_utils import utils


class TestComposer(object):

    def __init__(self):
        self.ct = utils.load_extension('extensions/composer')

    def test_composer_tool_should_compile(self):
        ctx = utils.FormattedDict({
            'DOWNLOAD_URL': 'http://server/bins',
            'BUILD_DIR': 'tests/data/composer',
            'CACHE_DIR': '/cache/dir',
            'PHP_VM': 'will_default_to_php_strategy',
            'WEBDIR': 'htdocs',
            'LIBDIR': 'lib'
        })
        ct = self.ct.ComposerExtension(ctx)
        assert ct._should_compile()

    def test_composer_tool_should_compile_not_found(self):
        ctx = utils.FormattedDict({
            'DOWNLOAD_URL': 'http://server/bins',
            'BUILD_DIR': 'lib',
            'CACHE_DIR': '/cache/dir',
            'PHP_VM': 'will_default_to_php_strategy',
            'WEBDIR': 'htdocs',
            'LIBDIR': 'lib'
        })
        ct = self.ct.ComposerExtension(ctx)
        assert not ct._should_compile()

    def test_composer_tool_install(self):
        ctx = utils.FormattedDict({
            'DOWNLOAD_URL': 'http://server/bins',
            'CACHE_HASH_ALGORITHM': 'sha1',
            'PHP_VM': 'will_default_to_php_strategy',
            'BUILD_DIR': '/build/dir',
            'CACHE_DIR': '/cache/dir'
        })
        builder = Dingus(_ctx=ctx)
        installer = Dingus()
        cfInstaller = Dingus()
        builder.install = Dingus(_installer=cfInstaller,
                                 return_value=installer)
        ct = self.ct.ComposerExtension(ctx)
        ct._builder = builder
        ct.install()
        eq_(2, len(builder.install.calls()))
        assert installer.modules.calls().once()
        eq_('PHP', installer.modules.calls()[0].args[0])
        call = installer.modules.calls()[0]
        assert call.return_value.calls().once()
        eq_('cli', call.return_value.calls()[0].args[0])
        assert installer.calls().once()

    def test_composer_tool_run_with_php(self):
        ctx = utils.FormattedDict({
            'PHP_VM': 'php',
            'DOWNLOAD_URL': 'http://server/bins',
            'CACHE_HASH_ALGORITHM': 'sha1',
            'BUILD_DIR': '/build/dir',
            'CACHE_DIR': '/cache/dir',
            'TMPDIR': tempfile.gettempdir(),
            'WEBDIR': 'htdocs',
            'LIBDIR': 'lib'
        })
        builder = Dingus(_ctx=ctx)
        # patch utils.rewrite_cfg method
        old_rewrite = self.ct.utils.rewrite_cfgs
        rewrite = Dingus()
        self.ct.utils.rewrite_cfgs = rewrite
        try:
            ct = self.ct.ComposerExtension(ctx)
            ct._builder = builder
            ct.run()
            eq_(2, len(builder.move.calls()))
            eq_(1, len(builder.copy.calls()))
            assert rewrite.calls().once()
            rewrite_args = rewrite.calls()[0].args
            assert rewrite_args[0].endswith('php.ini')
            assert 'HOME' in rewrite_args[1]
            assert 'TMPDIR' in rewrite_args[1]
        finally:
            self.ct.utils.rewrite_cfgs = old_rewrite

    def test_composer_tool_run_with_hhvm(self):
        ctx = utils.FormattedDict({
            'PHP_VM': 'hhvm',
            'DOWNLOAD_URL': 'http://server/bins',
            'CACHE_HASH_ALGORITHM': 'sha1',
            'BUILD_DIR': '/build/dir',
            'CACHE_DIR': '/cache/dir',
            'TMPDIR': tempfile.gettempdir(),
            'WEBDIR': 'htdocs',
            'LIBDIR': 'lib'
        })
        builder = Dingus(_ctx=ctx)
        # patch utils.rewrite_cfg method
        old_rewrite = self.ct.utils.rewrite_cfgs
        rewrite = Dingus()
        self.ct.utils.rewrite_cfgs = rewrite
        try:
            ct = self.ct.ComposerExtension(ctx)
            ct._builder = builder
            ct.run()
            eq_(2, len(builder.move.calls()))
            eq_(0, len(builder.copy.calls()))
            eq_(0, len(rewrite.calls()))
        finally:
            self.ct.utils.rewrite_cfgs = old_rewrite

    def test_composer_run_streams_output(self):
        ctx = utils.FormattedDict({
            'PHP_VM': 'hhvm',  # PHP strategy does other stuff
            'DOWNLOAD_URL': 'http://server/bins',
            'CACHE_HASH_ALGORITHM': 'sha1',
            'BUILD_DIR': '/build/dir',
            'CACHE_DIR': '/cache/dir',
            'TMPDIR': tempfile.gettempdir(),
            'WEBDIR': 'htdocs',
            'LIBDIR': 'lib'
        })
        builder = Dingus(_ctx=ctx)
        # patch stream_output method
        old_stream_output = self.ct.stream_output
        co = Dingus()
        self.ct.stream_output = co
        try:
            ct = self.ct.ComposerExtension(ctx)
            ct._builder = builder
            ct.run()
            assert co.calls().once()
            instCmd = co.calls()[0].args[1]
            assert instCmd.find('install') > 0
            assert instCmd.find('--no-progress') > 0
            assert instCmd.find('--no-interaction') > 0
            assert instCmd.find('--no-dev') > 0
        finally:
            self.ct.stream_output = old_stream_output

    def test_composer_tool_run_custom_composer_opts(self):
        ctx = utils.FormattedDict({
            'PHP_VM': 'php',
            'DOWNLOAD_URL': 'http://server/bins',
            'CACHE_HASH_ALGORITHM': 'sha1',
            'BUILD_DIR': '/build/dir',
            'CACHE_DIR': '/cache/dir',
            'TMPDIR': tempfile.gettempdir(),
            'WEBDIR': 'htdocs',
            'LIBDIR': 'lib',
            'COMPOSER_INSTALL_OPTIONS': ['--optimize-autoloader']
        })
        builder = Dingus(_ctx=ctx)
        # patch stream_output method
        old_stream_output = self.ct.stream_output
        co = Dingus()
        self.ct.stream_output = co
        # patch utils.rewrite_cfg method
        old_rewrite = self.ct.utils.rewrite_cfgs
        rewrite = Dingus()
        self.ct.utils.rewrite_cfgs = rewrite
        try:
            ct = self.ct.ComposerExtension(ctx)
            ct._builder = builder
            ct.run()
            eq_(2, len(builder.move.calls()))
            eq_(1, len(builder.copy.calls()))
            assert rewrite.calls().once()
            rewrite_args = rewrite.calls()[0].args
            assert rewrite_args[0].endswith('php.ini')
            assert 'HOME' in rewrite_args[1]
            assert 'TMPDIR' in rewrite_args[1]
            assert co.calls().once()
            instCmd = co.calls()[0].args[1]
            assert instCmd.find('install') > 0
            assert instCmd.find('--no-progress') > 0
            assert instCmd.find('--no-interaction') == -1
            assert instCmd.find('--no-dev') == -1
            assert instCmd.find('--optimize-autoloader') > 0
        finally:
            self.ct.stream_output = old_stream_output
            self.ct.utils.rewrite_cfgs = old_rewrite

    def test_composer_tool_run_sanity_checks(self):
        ctx = utils.FormattedDict({
            'PHP_VM': 'php',
            'DOWNLOAD_URL': 'http://server/bins',
            'CACHE_HASH_ALGORITHM': 'sha1',
            'BUILD_DIR': '/build/dir',
            'CACHE_DIR': '/cache/dir',
            'TMPDIR': tempfile.gettempdir()
        })
        builder = Dingus(_ctx=ctx)
        # patch stream_output method
        old_stream_output = self.ct.stream_output
        co = Dingus()
        self.ct.stream_output = co
        # patch utils.rewrite_cfg method
        old_rewrite = self.ct.utils.rewrite_cfgs
        rewrite = Dingus()
        self.ct.utils.rewrite_cfgs = rewrite
        try:
            ct = self.ct.ComposerExtension(ctx)
            ct._log = Dingus()
            ct._builder = builder
            ct.run()
            assert len(ct._log.warning.calls()) > 0
            assert ct._log.warning.calls()[0].args[0].find('PROTIP:') == 0
            exists = Dingus(return_value=True)
            with patch('os.path.exists', exists):
                ct._log = Dingus()
                ct.run()
            assert len(exists.calls()) == 1
            assert len(ct._log.warning.calls()) == 0
        finally:
            self.ct.stream_output = old_stream_output
            self.ct.utils.rewrite_cfgs = old_rewrite

    def test_process_commands(self):
        eq_(0, len(self.ct.preprocess_commands({
            'BUILD_DIR': '',
            'PHP_VM': ''
            })))

    def test_service_commands(self):
        eq_(0, len(self.ct.service_commands({
            'BUILD_DIR': '',
            'PHP_VM': ''
            })))

    def test_service_environment(self):
        eq_(0, len(self.ct.service_environment({
            'BUILD_DIR': '',
            'PHP_VM': ''
            })))

    def test_configure_composer_with_php_version(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': 'tests/data/composer',
            'PHP_54_LATEST': '5.4.31'
        })
        config = self.ct.ComposerConfiguration(ctx)
        config.configure()
        assert 'PHP_EXTENSIONS' in ctx.keys()
        assert list == type(ctx['PHP_EXTENSIONS'])
        assert 4 == len(ctx['PHP_EXTENSIONS'])
        assert 'openssl' == ctx['PHP_EXTENSIONS'][0]
        assert 'zip' == ctx['PHP_EXTENSIONS'][1]
        assert 'fileinfo' == ctx['PHP_EXTENSIONS'][2]
        assert 'gd' == ctx['PHP_EXTENSIONS'][3]
        assert '5.4.31' == ctx['PHP_VERSION']
        assert 'php' == ctx['PHP_VM']

    def test_configure_composer_with_php_version_and_base_extensions(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': 'tests/data/composer',
            'PHP_EXTENSIONS': ['a', 'b'],
            'PHP_54_LATEST': '5.4.31'
        })
        config = self.ct.ComposerConfiguration(ctx)
        config.configure()
        assert 'PHP_EXTENSIONS' in ctx.keys()
        assert list == type(ctx['PHP_EXTENSIONS'])
        assert 6 == len(ctx['PHP_EXTENSIONS'])
        assert 'a' == ctx['PHP_EXTENSIONS'][0]
        assert 'b' == ctx['PHP_EXTENSIONS'][1]
        assert 'openssl' == ctx['PHP_EXTENSIONS'][2]
        assert 'zip' == ctx['PHP_EXTENSIONS'][3]
        assert 'fileinfo' == ctx['PHP_EXTENSIONS'][4]
        assert 'gd' == ctx['PHP_EXTENSIONS'][5]
        assert '5.4.31' == ctx['PHP_VERSION']
        assert 'php' == ctx['PHP_VM']

    def test_configure_composer_without_php_version(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': 'tests/data/composer-no-php',
            'PHP_VERSION': '5.4.31'  # uses bp default
        })
        config = self.ct.ComposerConfiguration(ctx)
        config.configure()
        assert '5.4.31' == ctx['PHP_VERSION']
        assert 'php' == ctx['PHP_VM']
        assert 'PHP_EXTENSIONS' in ctx.keys()
        assert list == type(ctx['PHP_EXTENSIONS'])
        assert 3 == len(ctx['PHP_EXTENSIONS'])
        assert 'openssl' == ctx['PHP_EXTENSIONS'][0]
        assert 'zip' == ctx['PHP_EXTENSIONS'][1]
        assert 'fileinfo' == ctx['PHP_EXTENSIONS'][2]

    def test_configure_composer_with_hhvm_version(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': 'tests/data/composer-with-hhvm',
            'HHVM_VERSION': '3.2.0'
        })
        config = self.ct.ComposerConfiguration(ctx)
        config.configure()
        assert '3.2.0' == ctx['HHVM_VERSION']
        assert 'hhvm' == ctx['PHP_VM']

    def test_configure_does_not_run_when_no_composer_json(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': 'tests/data/app-1',
            'PHP_EXTENSIONS': ['a', 'b']
        })
        config = self.ct.ComposerConfiguration(ctx)
        config.configure()
        assert 'PHP_EXTENSIONS' in ctx.keys()
        assert list == type(ctx['PHP_EXTENSIONS'])
        assert 2 == len(ctx['PHP_EXTENSIONS'])
        assert 'a' in ctx['PHP_EXTENSIONS']
        assert 'b' in ctx['PHP_EXTENSIONS']
        assert 'openssl' not in ctx['PHP_EXTENSIONS']

    def test_configure_paths_missing(self):
        def fcp_test_json(path):
            tmp = fcp_orig(path)
            return (tmp[0], None)

        def fcp_test_lock(path):
            tmp = fcp_orig(path)
            return (None, tmp[1])

        def fcp_test_none(path):
            return (None, None)
        ctx = utils.FormattedDict({
            'BUILD_DIR': 'tests/data/composer',
            'PHP_54_LATEST': '5.4.31'
        })
        fcp_orig = self.ct.find_composer_paths
        # test when no composer.json or composer.lock files found
        self.ct.find_composer_paths = fcp_test_none
        try:
            self.ct.ComposerConfiguration(ctx).configure()
            assert 'PHP_EXTENSIONS' not in ctx.keys()
        finally:
            self.ct.find_composer_paths = fcp_orig
        # test when composer.json found, but no composer.lock
        self.ct.find_composer_paths = fcp_test_json
        try:
            self.ct.ComposerConfiguration(ctx).configure()
            assert 'PHP_EXTENSIONS' in ctx.keys()
            assert 3 == len(ctx['PHP_EXTENSIONS'])
            assert 'openssl' in ctx['PHP_EXTENSIONS']
            assert 'fileinfo' in ctx['PHP_EXTENSIONS']
            assert 'zip' in ctx['PHP_EXTENSIONS']
        finally:
            self.ct.find_composer_paths = fcp_orig
        # test when composer.lock found, but no composer.json
        self.ct.find_composer_paths = fcp_test_lock
        try:
            self.ct.ComposerConfiguration(ctx).configure()
            assert 'PHP_EXTENSIONS' in ctx.keys()
            assert 4 == len(ctx['PHP_EXTENSIONS'])
            assert 'openssl' in ctx['PHP_EXTENSIONS']
            assert 'gd' in ctx['PHP_EXTENSIONS']
            assert 'fileinfo' in ctx['PHP_EXTENSIONS']
            assert 'zip' in ctx['PHP_EXTENSIONS']
        finally:
            self.ct.find_composer_paths = fcp_orig

    def test_find_composer_paths(self):
        (json_path, lock_path) = \
            self.ct.find_composer_paths('tests')
        assert json_path is not None
        assert lock_path is not None
        eq_('tests/data/composer/composer.json', json_path)
        eq_('tests/data/composer/composer.lock', lock_path)

    def test_find_composer_php_version(self):
        ctx = {'BUILD_DIR': 'tests'}
        config = self.ct.ComposerConfiguration(ctx)
        php_version = config.read_version_from_composer_json('php')
        eq_('>=5.3', php_version)
        # check lock file
        php_version = config.read_version_from_composer_lock('php')
        eq_('>=5.3', php_version)

    def test_pick_php_version(self):
        ctx = {
            'PHP_VERSION': '5.4.31',
            'PHP_54_LATEST': '5.4.31',
            'BUILD_DIR': '',
            'PHP_55_LATEST': '5.5.15'
        }
        pick_php_version = self.ct.ComposerConfiguration(ctx).pick_php_version
        # no PHP 5.3, default to 5.4
        eq_('5.4.31', pick_php_version('>=5.3'))
        eq_('5.4.31', pick_php_version('5.3.*'))
        # latest PHP 5.4 version
        eq_('5.4.31', pick_php_version('>=5.4'))
        eq_('5.4.31', pick_php_version('5.4.*'))
        # extact PHP 5.4 versions
        eq_('5.4.31', pick_php_version('5.4.31'))
        eq_('5.4.30', pick_php_version('5.4.30'))
        eq_('5.4.29', pick_php_version('5.4.29'))
        # latest PHP 5.5 version
        eq_('5.5.15', pick_php_version('>=5.5'))
        eq_('5.5.15', pick_php_version('5.5.*'))
        # exact PHP 5.5 versions
        eq_('5.5.15', pick_php_version('5.5.15'))
        eq_('5.5.14', pick_php_version('5.5.14'))
        # not understood, should default to PHP_VERSION
        eq_('5.4.31', pick_php_version(''))
        eq_('5.4.31', pick_php_version(None))
        eq_('5.4.31', pick_php_version('5.6.1'))
        eq_('5.4.31', pick_php_version('<5.5'))
        eq_('5.4.31', pick_php_version('<5.4'))

    def test_empty_platform_section(self):
        exts = self.ct.ComposerConfiguration({
            'BUILD_DIR': ''
        }).read_exts_from_path(
            'tests/data/composer/composer-phalcon.lock')
        eq_(2, len(exts))
        eq_('curl', exts[0])
        eq_('tokenizer', exts[1])

    def test_none_for_extension_reading(self):
        exts = self.ct.ComposerConfiguration({
            'BUILD_DIR': ''
        }).read_exts_from_path(None)
        eq_(0, len(exts))

    def test_composer_defaults(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': '/tmp/build',
            'CACHE_DIR': '/tmp/cache',
            'PHP_VM': 'will_default_to_php_strategy',
            'LIBDIR': 'lib'
        })
        ct = self.ct.ComposerExtension(ctx)
        eq_('/tmp/build/lib/vendor', ct._ctx['COMPOSER_VENDOR_DIR'])
        eq_('/tmp/build/php/bin', ct._ctx['COMPOSER_BIN_DIR'])
        eq_('/tmp/cache/composer', ct._ctx['COMPOSER_CACHE_DIR'])

    def test_composer_custom_values(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': '/tmp/build',
            'CACHE_DIR': '/tmp/cache',
            'LIBDIR': 'lib',
            'COMPOSER_VENDOR_DIR': '{BUILD_DIR}/vendor',
            'COMPOSER_BIN_DIR': '{BUILD_DIR}/bin',
            'PHP_VM': 'will_default_to_php_strategy',
            'COMPOSER_CACHE_DIR': '{CACHE_DIR}/custom'
        })
        ct = self.ct.ComposerExtension(ctx)
        eq_('/tmp/build/vendor', ct._ctx['COMPOSER_VENDOR_DIR'])
        eq_('/tmp/build/bin', ct._ctx['COMPOSER_BIN_DIR'])
        eq_('/tmp/cache/custom', ct._ctx['COMPOSER_CACHE_DIR'])

    def test_binary_path_for_hhvm(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': '/usr/awesome/',
            'PHP_VM': 'hhvm'
        })
        ct = self.ct.ComposerExtension(ctx)
        path = ct.binary_path()
        eq_('/usr/awesome/hhvm/usr/bin/hhvm', path)

    def test_binary_path_for_php(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': '/usr/awesome',
            'PHP_VM': 'php'
        })
        ct = self.ct.ComposerExtension(ctx)
        path = ct.binary_path()
        eq_('/usr/awesome/php/bin/php', path)

    def test_ld_library_path_for_hhvm(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': '/usr/awesome/',
            'PHP_VM': 'hhvm'
        })
        ct = self.ct.ComposerExtension(ctx)
        path = ct.ld_library_path()
        eq_('/usr/awesome/hhvm/usr/lib/hhvm', path)

    def test_ld_library_path_for_php(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': '/usr/awesome',
            'PHP_VM': 'php'
        })
        ct = self.ct.ComposerExtension(ctx)
        path = ct.ld_library_path()
        eq_('/usr/awesome/php/lib', path)
