import tempfile
from nose.tools import eq_
from dingus import Dingus
from dingus import patch
from build_pack_utils import utils


class TestComposer(object):

    def __init__(self):
        self.ct = utils.load_extension('extensions/composer')

    def test_composer_tool_detect(self):
        ctx = utils.FormattedDict({
            'DOWNLOAD_URL': 'http://server/bins',
            'BUILD_DIR': 'tests/data/composer',
            'CACHE_DIR': '/cache/dir',
            'WEBDIR': 'htdocs',
            'LIBDIR': 'lib'
        })
        builder = Dingus(_ctx=ctx)
        ct = self.ct.ComposerTool(builder)
        assert ct.detect()

    def test_composer_tool_detect_not_found(self):
        ctx = utils.FormattedDict({
            'DOWNLOAD_URL': 'http://server/bins',
            'BUILD_DIR': 'lib',
            'CACHE_DIR': '/cache/dir',
            'WEBDIR': 'htdocs',
            'LIBDIR': 'lib'
        })
        builder = Dingus(_ctx=ctx)
        ct = self.ct.ComposerTool(builder)
        assert not ct.detect()

    def test_composer_tool_install(self):
        ctx = utils.FormattedDict({
            'DOWNLOAD_URL': 'http://server/bins',
            'CACHE_HASH_ALGORITHM': 'sha1',
            'BUILD_DIR': '/build/dir',
            'CACHE_DIR': '/cache/dir'
        })
        builder = Dingus(_ctx=ctx)
        installer = Dingus()
        cfInstaller = Dingus()
        builder.install = Dingus(_installer=cfInstaller,
                                 return_value=installer)
        ct = self.ct.ComposerTool(builder)
        ct.install()
        eq_(2, len(builder.install.calls()))
        assert installer.modules.calls().once()
        eq_('PHP', installer.modules.calls()[0].args[0])
        call = installer.modules.calls()[0]
        assert call.return_value.calls().once()
        eq_('cli', call.return_value.calls()[0].args[0])
        assert installer.calls().once()

    def test_composer_tool_run(self):
        ctx = utils.FormattedDict({
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
        # patch utils.rewrite_cfg method
        old_rewrite = self.ct.utils.rewrite_cfgs
        rewrite = Dingus()
        self.ct.utils.rewrite_cfgs = rewrite
        try:
            ct = self.ct.ComposerTool(builder)
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
            assert instCmd.find('--no-interaction') > 0
            assert instCmd.find('--no-dev') > 0
        finally:
            self.ct.stream_output = old_stream_output
            self.ct.utils.rewrite_cfgs = old_rewrite

    def test_composer_tool_run_custom_composer_opts(self):
        ctx = utils.FormattedDict({
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
            ct = self.ct.ComposerTool(builder)
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
            ct = self.ct.ComposerTool(builder)
            ct._log = Dingus()
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
        eq_(0, len(self.ct.preprocess_commands({})))

    def test_service_commands(self):
        eq_(0, len(self.ct.service_commands({})))

    def test_service_environment(self):
        eq_(0, len(self.ct.service_environment({})))

    def test_compile(self):
        composer = Dingus()
        composer.return_value.detect.return_value = True
        builder = Dingus()
        old_composer_tool = self.ct.ComposerTool
        self.ct.ComposerTool = composer
        try:
            self.ct.compile(builder)
            assert composer.calls().once()
            assert composer.return_value.detect.calls().once()
            assert composer.return_value.install.calls().once()
            assert composer.return_value.run.calls().once()
        finally:
            self.ct.ComposerTool = old_composer_tool

    def test_compile_detect_fails(self):
        composer = Dingus()
        composer.return_value.detect.return_value = False
        builder = Dingus()
        old_composer_tool = self.ct.ComposerTool
        self.ct.ComposerTool = composer
        try:
            self.ct.compile(builder)
            assert composer.calls().once()
            assert composer.return_value.detect.calls().once()
            eq_(0, len(composer.return_value.install.calls()))
            eq_(0, len(composer.return_value.run.calls()))
        finally:
            self.ct.ComposerTool = old_composer_tool

    def test_configure(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': 'tests/data/composer',
            'PHP_54_LATEST': '5.4.31'
        })
        self.ct.ComposerTool.configure(ctx)
        assert 'PHP_EXTENSIONS' in ctx.keys()
        assert list == type(ctx['PHP_EXTENSIONS'])
        assert 4 == len(ctx['PHP_EXTENSIONS'])
        assert 'openssl' in ctx['PHP_EXTENSIONS']
        assert 'gd' in ctx['PHP_EXTENSIONS']
        assert 'fileinfo' in ctx['PHP_EXTENSIONS']
        assert 'zip' in ctx['PHP_EXTENSIONS']
        assert '5.4.31' == ctx['PHP_VERSION']
        ctx = utils.FormattedDict({
            'BUILD_DIR': 'tests/data/composer',
            'PHP_EXTENSIONS': ['a', 'b'],
            'PHP_54_LATEST': '5.4.31'
        })
        self.ct.ComposerTool.configure(ctx)
        assert 'PHP_EXTENSIONS' in ctx.keys()
        assert list == type(ctx['PHP_EXTENSIONS'])
        assert 6 == len(ctx['PHP_EXTENSIONS'])
        assert 'a' in ctx['PHP_EXTENSIONS']
        assert 'b' in ctx['PHP_EXTENSIONS']
        assert 'openssl' in ctx['PHP_EXTENSIONS']
        assert 'gd' in ctx['PHP_EXTENSIONS']
        assert 'fileinfo' in ctx['PHP_EXTENSIONS']
        assert 'zip' in ctx['PHP_EXTENSIONS']
        assert '5.4.31' == ctx['PHP_VERSION']

    def test_configure_no_composer(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': 'tests/data/app-1',
            'PHP_EXTENSIONS': ['a', 'b']
        })
        self.ct.ComposerTool.configure(ctx)
        assert 'PHP_EXTENSIONS' in ctx.keys()
        assert list == type(ctx['PHP_EXTENSIONS'])
        assert 2 == len(ctx['PHP_EXTENSIONS'])
        assert 'a' in ctx['PHP_EXTENSIONS']
        assert 'b' in ctx['PHP_EXTENSIONS']
        assert 'openssl' not in ctx['PHP_EXTENSIONS']

    def test_configure_paths_missing(self):
        @staticmethod
        def fcp_test_json(path):
            tmp = fcp_orig(path)
            return (tmp[0], None)

        @staticmethod
        def fcp_test_lock(path):
            tmp = fcp_orig(path)
            return (None, tmp[1])

        @staticmethod
        def fcp_test_none(path):
            return (None, None)
        ctx = utils.FormattedDict({
            'BUILD_DIR': 'tests/data/composer',
            'PHP_54_LATEST': '5.4.31'
        })
        fcp_orig = self.ct.ComposerTool._find_composer_paths
        # test when no composer.json or composer.lock files found
        self.ct.ComposerTool._find_composer_paths = fcp_test_none
        try:
            self.ct.ComposerTool.configure(ctx)
            assert 'PHP_EXTENSIONS' not in ctx.keys()
        finally:
            self.ct.ComposerTool._find_composer_paths = staticmethod(fcp_orig)
        # test when composer.json found, but no composer.lock
        self.ct.ComposerTool._find_composer_paths = fcp_test_json
        try:
            self.ct.ComposerTool.configure(ctx)
            assert 'PHP_EXTENSIONS' in ctx.keys()
            assert 3 == len(ctx['PHP_EXTENSIONS'])
            assert 'openssl' in ctx['PHP_EXTENSIONS']
            assert 'fileinfo' in ctx['PHP_EXTENSIONS']
            assert 'zip' in ctx['PHP_EXTENSIONS']
        finally:
            self.ct.ComposerTool._find_composer_paths = staticmethod(fcp_orig)
        # test when composer.lock found, but no composer.json
        self.ct.ComposerTool._find_composer_paths = fcp_test_lock
        try:
            self.ct.ComposerTool.configure(ctx)
            assert 'PHP_EXTENSIONS' in ctx.keys()
            assert 4 == len(ctx['PHP_EXTENSIONS'])
            assert 'openssl' in ctx['PHP_EXTENSIONS']
            assert 'gd' in ctx['PHP_EXTENSIONS']
            assert 'fileinfo' in ctx['PHP_EXTENSIONS']
            assert 'zip' in ctx['PHP_EXTENSIONS']
        finally:
            self.ct.ComposerTool._find_composer_paths = staticmethod(fcp_orig)

    def test_find_composer_paths(self):
        (json_path, lock_path) = \
            self.ct.ComposerTool._find_composer_paths('tests')
        assert json_path is not None
        assert lock_path is not None
        eq_('tests/data/composer/composer.json', json_path)
        eq_('tests/data/composer/composer.lock', lock_path)

    def test_find_composer_php_version(self):
        (json_path, lock_path) = \
            self.ct.ComposerTool._find_composer_paths('tests')
        php_version = \
            self.ct.ComposerTool.read_php_version_from_composer_json(json_path)
        eq_('>=5.3', php_version)
        # check lock file
        php_version = \
            self.ct.ComposerTool.read_php_version_from_composer_lock(lock_path)
        eq_('>=5.3', php_version)

    def test_pick_php_version(self):
        ctx = {
            'PHP_VERSION': '5.4.31',
            'PHP_54_LATEST': '5.4.31',
            'PHP_55_LATEST': '5.5.15'
        }
        # no PHP 5.3, default to 5.4
        eq_('5.4.31', self.ct.ComposerTool.pick_php_version(ctx, '>=5.3'))
        eq_('5.4.31', self.ct.ComposerTool.pick_php_version(ctx, '5.3.*'))
        # latest PHP 5.4 version
        eq_('5.4.31', self.ct.ComposerTool.pick_php_version(ctx, '>=5.4'))
        eq_('5.4.31', self.ct.ComposerTool.pick_php_version(ctx, '5.4.*'))
        # extact PHP 5.4 versions
        eq_('5.4.31', self.ct.ComposerTool.pick_php_version(ctx, '5.4.31'))
        eq_('5.4.30', self.ct.ComposerTool.pick_php_version(ctx, '5.4.30'))
        eq_('5.4.29', self.ct.ComposerTool.pick_php_version(ctx, '5.4.29'))
        # latest PHP 5.5 version
        eq_('5.5.15', self.ct.ComposerTool.pick_php_version(ctx, '>=5.5'))
        eq_('5.5.15', self.ct.ComposerTool.pick_php_version(ctx, '5.5.*'))
        # exact PHP 5.5 versions
        eq_('5.5.15', self.ct.ComposerTool.pick_php_version(ctx, '5.5.15'))
        eq_('5.5.14', self.ct.ComposerTool.pick_php_version(ctx, '5.5.14'))
        # not understood, should default to PHP_VERSION
        eq_('5.4.31', self.ct.ComposerTool.pick_php_version(ctx, ''))
        eq_('5.4.31', self.ct.ComposerTool.pick_php_version(ctx, None))
        eq_('5.4.31', self.ct.ComposerTool.pick_php_version(ctx, '5.6.1'))
        eq_('5.4.31', self.ct.ComposerTool.pick_php_version(ctx, '<5.5'))
        eq_('5.4.31', self.ct.ComposerTool.pick_php_version(ctx, '<5.4'))

    def test_empty_platform_section(self):
        exts = self.ct.ComposerTool.read_exts_from_composer_lock(
            'tests/data/composer/composer-phalcon.lock')
        eq_(1, len(exts))
        eq_('curl', exts[0])

    def test_composer_defaults(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': '/tmp/build',
            'CACHE_DIR': '/tmp/cache',
            'LIBDIR': 'lib'
        })
        builder = Dingus(_ctx=ctx)
        ct = self.ct.ComposerTool(builder)
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
            'COMPOSER_CACHE_DIR': '{CACHE_DIR}/custom'
        })
        builder = Dingus(_ctx=ctx)
        ct = self.ct.ComposerTool(builder)
        eq_('/tmp/build/vendor', ct._ctx['COMPOSER_VENDOR_DIR'])
        eq_('/tmp/build/bin', ct._ctx['COMPOSER_BIN_DIR'])
        eq_('/tmp/cache/custom', ct._ctx['COMPOSER_CACHE_DIR'])
