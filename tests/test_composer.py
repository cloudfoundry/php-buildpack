import os
import tempfile
import shutil
import re
from nose.tools import eq_
from dingus import Dingus
from dingus import patch
from build_pack_utils import utils
from common.dingus_extension import patches


class TestComposer(object):

    def __init__(self):
        self.extension_module = utils.load_extension('extensions/composer')

    def setUp(self):
        os.environ['COMPOSER_GITHUB_OAUTH_TOKEN'] = ""
        assert(os.getenv('COMPOSER_GITHUB_OAUTH_TOKEN') == "")
        self.buildpack_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

    def test_composer_tool_should_compile(self):
        ctx = utils.FormattedDict({
            'BP_DIR': '',
            'BUILD_DIR': 'tests/data/composer',
            'CACHE_DIR': '/cache/dir',
            'PHP_VM': 'will_default_to_php_strategy',
            'WEBDIR': 'htdocs',
            'LIBDIR': 'lib'
        })
        ct = self.extension_module.ComposerExtension(ctx)
        assert ct._should_compile()

    def test_composer_tool_should_compile_not_found(self):
        ctx = utils.FormattedDict({
            'BP_DIR': '',
            'BUILD_DIR': 'lib',
            'CACHE_DIR': '/cache/dir',
            'PHP_VM': 'will_default_to_php_strategy',
            'WEBDIR': 'htdocs',
            'LIBDIR': 'lib'
        })
        ct = self.extension_module.ComposerExtension(ctx)
        assert not ct._should_compile()

    def test_composer_tool_uses_default_version_for(self):
        ctx = utils.FormattedDict({
            'BP_DIR': os.path.join(self.buildpack_dir, 'tests/data/composer-default-versions/'),
            'PHP_VM': 'will_default_to_php_strategy',
            'BUILD_DIR': '/build/dir',
            'CACHE_DIR': '/cache/dir',
            'WEBDIR': ''
        })
        ct = self.extension_module.ComposerExtension(ctx)
        assert ct._ctx['COMPOSER_VERSION'] == '9.9.9'

    def test_composer_tool_install(self):
        ctx = utils.FormattedDict({
            'BP_DIR': '',
            'PHP_VM': 'will_default_to_php_strategy',
            'BUILD_DIR': '/build/dir',
            'CACHE_DIR': '/cache/dir',
            'WEBDIR': ''
        })
        builder = Dingus(_ctx=ctx)
        installer = Dingus()
        cfInstaller = Dingus()
        builder.install = Dingus(_installer=cfInstaller,
                                 return_value=installer)
        ct = self.extension_module.ComposerExtension(ctx)
        ct._builder = builder
        ct.install()
        eq_(2, len(builder.install.calls()))
        # make sure PHP is installed
        assert installer.package.calls().once()
        eq_('PHP', installer.package.calls()[0].args[0])
        call = installer.package.calls()[0]
        assert call.return_value.calls().once()
        assert installer.calls().once()
        # make sure composer is installed
        assert installer._installer.calls().once()
        assert re.match('/composer/[\d\.]+/composer.phar', installer._installer.calls()[0].args[0]), \
            "was %s" % installer._installer.calls()[0].args[0]

    def test_composer_tool_install_latest(self):
        ctx = utils.FormattedDict({
            'PHP_VM': 'will_default_to_php_strategy',
            'BUILD_DIR': '/build/dir',
            'CACHE_DIR': '/cache/dir',
            'COMPOSER_VERSION': 'latest',
            'BP_DIR': '',
            'WEBDIR': ''
        })
        builder = Dingus(_ctx=ctx)
        installer = Dingus()
        cfInstaller = Dingus()
        builder.install = Dingus(_installer=cfInstaller,
                                 return_value=installer)
        ct = self.extension_module.ComposerExtension(ctx)
        ct._builder = builder
        ct.install()
        eq_(2, len(builder.install.calls()))
        # make sure PHP is installed
        assert installer.package.calls().once()
        eq_('PHP', installer.package.calls()[0].args[0])
        call = installer.package.calls()[0]
        assert call.return_value.calls().once()
        assert installer.calls().once()
        # make sure composer is installed
        assert installer._installer.calls().once()
        assert installer._installer.calls()[0].args[0] == \
            'https://getcomposer.org/composer.phar', \
            "was %s" % installer._installer.calls()[0].args[0]

    def test_composer_tool_run_custom_composer_opts(self):
        ctx = utils.FormattedDict({
            'PHP_VM': 'php',
            'BUILD_DIR': '/build/dir',
            'CACHE_DIR': '/cache/dir',
            'TMPDIR': tempfile.gettempdir(),
            'WEBDIR': 'htdocs',
            'LIBDIR': 'lib',
            'COMPOSER_INSTALL_OPTIONS': ['--optimize-autoloader'],
            'BP_DIR': ''
        })

        instance_stub = Dingus()
        instance_stub._set_return_value("""{"rate": {"limit": 60, "remaining": 60}}""")

        stream_output_stub = Dingus()

        rewrite_stub = Dingus()

        builder = Dingus(_ctx=ctx)

        with patches({
            'StringIO.StringIO.getvalue': instance_stub,
            'composer.extension.stream_output': stream_output_stub,
            'composer.extension.utils.rewrite_cfgs': rewrite_stub
        }):
            ct = self.extension_module.ComposerExtension(ctx)
            ct._builder = builder
            ct.composer_runner = \
                self.extension_module.ComposerCommandRunner(ctx, builder)
            ct.run()
            eq_(1, len(builder.copy.calls()))
            assert rewrite_stub.calls().once()
            rewrite_args = rewrite_stub.calls()[0].args
            assert rewrite_args[0].endswith('php.ini')
            assert 'HOME' in rewrite_args[1]
            assert 'TMPDIR' in rewrite_args[1]
            instCmd = stream_output_stub.calls()[-1].args[1]
            assert instCmd.find('--optimize-autoloader') > 0

    def test_composer_tool_run_sanity_checks(self):
        ctx = utils.FormattedDict({
            'PHP_VM': 'php',
            'BUILD_DIR': '/build/dir',
            'CACHE_DIR': '/cache/dir',
            'WEBDIR': '',
            'TMPDIR': tempfile.gettempdir(),
            'LIBDIR': 'lib',
            'BP_DIR': ''
        })

        instance_stub = Dingus()
        instance_stub._set_return_value("""{"rate": {"limit": 60, "remaining": 60}}""")

        stream_output_stub = Dingus()

        rewrite_stub = Dingus()

        builder = Dingus(_ctx=ctx)

        exists_stub = Dingus()

        with patches({
            'StringIO.StringIO.getvalue': instance_stub,
            'composer.extension.stream_output': stream_output_stub,
            'composer.extension.utils.rewrite_cfgs': rewrite_stub
        }):
            composer_extension = \
                self.extension_module.ComposerExtension(ctx)
            composer_extension._log = Dingus()
            composer_extension._builder = builder
            composer_extension.composer_runner = \
                self.extension_module.ComposerCommandRunner(ctx, builder)

            composer_extension.run()

            composer_extension_calls = composer_extension._log.warning.calls()
            assert len(composer_extension_calls) > 0
            assert composer_extension_calls[0].args[0].find('PROTIP:') == 0
            exists = Dingus(return_value=True)
            with patch('os.path.exists', exists_stub):
                composer_extension._log = Dingus()
                composer_extension.run()
            assert len(composer_extension._log.warning.calls()) == 0

    def test_process_commands(self):
        eq_(0, len(self.extension_module.preprocess_commands({
            'BP_DIR': '',
            'BUILD_DIR': '',
            'WEBDIR': '',
            'PHP_VM': ''
            })))

    def test_service_commands(self):
        eq_(0, len(self.extension_module.service_commands({
            'BP_DIR': '',
            'BUILD_DIR': '',
            'WEBDIR': '',
            'PHP_VM': ''
            })))

    def test_service_environment(self):
        eq_(0, len(self.extension_module.service_environment({
            'BP_DIR': '',
            'BUILD_DIR': '',
            'WEBDIR': '',
            'PHP_VM': ''
            })))

    def test_configure_composer_with_php_version(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': 'tests/data/composer',
            'WEBDIR': '',
            'PHP_55_LATEST': '5.5.31'
        })
        config = self.extension_module.ComposerConfiguration(ctx)
        config.configure()
        assert 'PHP_EXTENSIONS' in ctx.keys()
        assert list == type(ctx['PHP_EXTENSIONS'])
        assert 4 == len(ctx['PHP_EXTENSIONS'])
        assert 'openssl' == ctx['PHP_EXTENSIONS'][0]
        assert 'zip' == ctx['PHP_EXTENSIONS'][1]
        assert 'fileinfo' == ctx['PHP_EXTENSIONS'][2]
        assert 'gd' == ctx['PHP_EXTENSIONS'][3]
        assert '5.5.31' == ctx['PHP_VERSION']
        assert 'php' == ctx['PHP_VM']

    def test_configure_composer_with_php_version_and_base_extensions(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': 'tests/data/composer',
            'WEBDIR': '',
            'PHP_EXTENSIONS': ['a', 'b'],
            'PHP_55_LATEST': '5.5.31'
        })
        config = self.extension_module.ComposerConfiguration(ctx)
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
        assert '5.5.31' == ctx['PHP_VERSION']
        assert 'php' == ctx['PHP_VM']

    def test_configure_composer_without_php_version(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': 'tests/data/composer-no-php',
            'WEBDIR': '',
            'PHP_VERSION': '5.4.31'  # uses bp default
        })
        config = self.extension_module.ComposerConfiguration(ctx)
        config.configure()
        assert '5.4.31' == ctx['PHP_VERSION']
        assert 'php' == ctx['PHP_VM']
        assert 'PHP_EXTENSIONS' in ctx.keys()
        assert list == type(ctx['PHP_EXTENSIONS'])
        assert 3 == len(ctx['PHP_EXTENSIONS'])
        assert 'openssl' == ctx['PHP_EXTENSIONS'][0]
        assert 'zip' == ctx['PHP_EXTENSIONS'][1]
        assert 'fileinfo' == ctx['PHP_EXTENSIONS'][2]

    def test_configure_does_not_run_when_no_composer_json(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': 'tests/data/app-1',
            'WEBDIR': '',
            'PHP_EXTENSIONS': ['a', 'b']
        })
        config = self.extension_module.ComposerConfiguration(ctx)
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
            'WEBDIR': '',
            'PHP_55_LATEST': '5.5.31'
        })
        fcp_orig = self.extension_module.find_composer_paths
        # test when no composer.json or composer.lock files found
        self.extension_module.find_composer_paths = fcp_test_none
        try:
            self.extension_module.ComposerConfiguration(ctx).configure()
            assert 'PHP_EXTENSIONS' not in ctx.keys()
        finally:
            self.extension_module.find_composer_paths = fcp_orig
        # test when composer.json found, but no composer.lock
        self.extension_module.find_composer_paths = fcp_test_json
        try:
            self.extension_module.ComposerConfiguration(ctx).configure()
            assert 'PHP_EXTENSIONS' in ctx.keys()
            assert 3 == len(ctx['PHP_EXTENSIONS'])
            assert 'openssl' in ctx['PHP_EXTENSIONS']
            assert 'fileinfo' in ctx['PHP_EXTENSIONS']
            assert 'zip' in ctx['PHP_EXTENSIONS']
        finally:
            self.extension_module.find_composer_paths = fcp_orig
        # test when composer.lock found, but no composer.json
        self.extension_module.find_composer_paths = fcp_test_lock
        try:
            self.extension_module.ComposerConfiguration(ctx).configure()
            assert 'PHP_EXTENSIONS' in ctx.keys()
            assert 4 == len(ctx['PHP_EXTENSIONS'])
            assert 'openssl' in ctx['PHP_EXTENSIONS']
            assert 'gd' in ctx['PHP_EXTENSIONS']
            assert 'fileinfo' in ctx['PHP_EXTENSIONS']
            assert 'zip' in ctx['PHP_EXTENSIONS']
        finally:
            self.extension_module.find_composer_paths = fcp_orig

    def test_find_composer_php_version(self):
        ctx = {'BUILD_DIR': 'tests/data/composer-lock', 'WEBDIR': ''}
        config = self.extension_module.ComposerConfiguration(ctx)
        php_version = config.read_version_from_composer('php')
        eq_('>=5.3', php_version)

    def test_pick_php_version(self):
        ctx = {
            'PHP_VERSION': '5.5.15',
            'BUILD_DIR': '',
            'PHP_55_LATEST': '5.5.15',
            'PHP_56_LATEST': '5.6.7',
            'PHP_70_LATEST': '7.0.100',
            'WEBDIR': ''
        }
        pick_php_version = \
            self.extension_module.ComposerConfiguration(ctx).pick_php_version
        # no PHP 5.3, default to 5.4
        # latest PHP 5.5 version
        eq_('5.5.15', pick_php_version('>=5.5'))
        eq_('5.5.15', pick_php_version('5.5.*'))
        # exact PHP 5.5 versions
        eq_('5.5.15', pick_php_version('5.5.15'))
        eq_('5.5.14', pick_php_version('5.5.14'))
        # latest PHP 5.6 version
        eq_('5.6.7', pick_php_version('>=5.6'))
        eq_('5.6.7', pick_php_version('5.6.*'))
        # exact PHP 5.6 versions
        eq_('5.6.7', pick_php_version('5.6.7'))
        eq_('5.6.6', pick_php_version('5.6.6'))
        # latest PHP 7.0 version
        eq_('7.0.100', pick_php_version('>=7.0'))
        eq_('7.0.100', pick_php_version('7.0.*'))
        # exact PHP 7.0 versions
        eq_('7.0.1', pick_php_version('7.0.1'))
        eq_('7.0.2', pick_php_version('7.0.2'))
        # not understood, should default to PHP_VERSION
        eq_('5.5.15', pick_php_version(''))
        eq_('5.5.15', pick_php_version(None))
        eq_('5.5.15', pick_php_version('5.61.1'))
        eq_('5.5.15', pick_php_version('<5.5'))
        eq_('5.5.15', pick_php_version('<5.4'))

    def test_empty_platform_section(self):
        exts = self.extension_module.ComposerConfiguration({
            'BUILD_DIR': '',
            'WEBDIR': ''
        }).read_exts_from_path(
            'tests/data/composer/composer-phalcon.lock')
        eq_(2, len(exts))
        eq_('curl', exts[0])
        eq_('tokenizer', exts[1])

    def test_none_for_extension_reading(self):
        exts = self.extension_module.ComposerConfiguration({
            'BUILD_DIR': '',
            'WEBDIR': ''
        }).read_exts_from_path(None)
        eq_(0, len(exts))

    def test_with_extensions(self):
        exts = self.extension_module.ComposerConfiguration({
            'BUILD_DIR': '',
            'WEBDIR': ''
        }).read_exts_from_path(
            'tests/data/composer/composer.json')
        eq_(2, len(exts))
        eq_('zip', exts[0])
        eq_('fileinfo', exts[1])

    def test_with_oddly_formatted_composer_file(self):
        exts = self.extension_module.ComposerConfiguration({
            'BUILD_DIR': '',
            'WEBDIR': ''
        }).read_exts_from_path(
            'tests/data/composer/composer-format.json')
        eq_(1, len(exts))
        eq_('mysqli', exts[0])

    def test_composer_defaults(self):
        ctx = utils.FormattedDict({
            'BP_DIR': '',
            'BUILD_DIR': '/tmp/build',
            'CACHE_DIR': '/tmp/cache',
            'PHP_VM': 'will_default_to_php_strategy',
            'LIBDIR': 'lib',
            'WEBDIR': ''
        })
        ct = self.extension_module.ComposerExtension(ctx)
        eq_('/tmp/build/lib/vendor', ct._ctx['COMPOSER_VENDOR_DIR'])
        eq_('/tmp/build/php/bin', ct._ctx['COMPOSER_BIN_DIR'])
        eq_('/tmp/cache/composer', ct._ctx['COMPOSER_CACHE_DIR'])

    def test_composer_custom_values(self):
        ctx = utils.FormattedDict({
            'BP_DIR': '',
            'BUILD_DIR': '/tmp/build',
            'CACHE_DIR': '/tmp/cache',
            'LIBDIR': 'lib',
            'COMPOSER_VENDOR_DIR': '{BUILD_DIR}/vendor',
            'COMPOSER_BIN_DIR': '{BUILD_DIR}/bin',
            'PHP_VM': 'will_default_to_php_strategy',
            'COMPOSER_CACHE_DIR': '{CACHE_DIR}/custom',
            'WEBDIR': ''
        })
        ct = self.extension_module.ComposerExtension(ctx)
        eq_('/tmp/build/vendor', ct._ctx['COMPOSER_VENDOR_DIR'])
        eq_('/tmp/build/bin', ct._ctx['COMPOSER_BIN_DIR'])
        eq_('/tmp/cache/custom', ct._ctx['COMPOSER_CACHE_DIR'])

    def test_binary_path_for_php(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': '/usr/awesome',
            'WEBDIR': '',
            'PHP_VM': 'php'
        })
        stg = self.extension_module.PHPComposerStrategy(ctx)
        path = stg.binary_path()
        eq_('/usr/awesome/php/bin/php', path)

    def test_build_composer_environment_inherits_from_ctx(self):
        ctx = utils.FormattedDict({
            'BP_DIR': '',
            'BUILD_DIR': '/usr/awesome',
            'WEBDIR': '',
            'PHPRC': '/usr/awesome/phpini',
            'PHP_VM': 'php',
            'TMPDIR': 'tmp',
            'LIBDIR': 'lib',
            'CACHE_DIR': 'cache',
            'OUR_SPECIAL_KEY': 'SPECIAL_VALUE'
        })

        environ_stub = Dingus()
        environ_stub._set_return_value(['OUR_SPECIAL_KEY'])

        write_config_stub = Dingus()

        with patches({
            'os.environ.keys': environ_stub,
            'composer.extension.PHPComposerStrategy.write_config': write_config_stub
        }):

            self.extension_module.ComposerExtension(ctx)
            cr = self.extension_module.ComposerCommandRunner(ctx, None)

            built_environment = cr._build_composer_environment()

        assert 'OUR_SPECIAL_KEY' in built_environment, \
            'OUR_SPECIAL_KEY was not found in the built_environment variable'
        assert built_environment['OUR_SPECIAL_KEY'] == 'SPECIAL_VALUE',  \
            '"OUR_SPECIAL_KEY" key in built_environment was %s; expected "SPECIAL_VALUE"' % built_environment['OUR_SPECIAL_KEY']

    def test_build_composer_environment_sets_composer_env_vars(self):
        ctx = utils.FormattedDict({
            'BP_DIR': '',
            'BUILD_DIR': '/tmp/build',
            'WEBDIR': '',
            'CACHE_DIR': '/tmp/cache',
            'LIBDIR': 'lib',
            'TMPDIR': '/tmp',
            'PHP_VM': 'php'
        })

        write_config_stub = Dingus()

        with patches({
            'composer.extension.PHPComposerStrategy.write_config': write_config_stub
        }):

            self.extension_module.ComposerExtension(ctx)
            cr = self.extension_module.ComposerCommandRunner(ctx, None)

            built_environment = cr._build_composer_environment()

        assert 'COMPOSER_VENDOR_DIR' in built_environment, \
            'Expect to find COMPOSER_VENDOR_DIR in built_environment'
        assert 'COMPOSER_BIN_DIR' in built_environment, \
            'Expect to find COMPOSER_BIN_DIR in built_environment'
        assert 'COMPOSER_CACHE_DIR' in built_environment, \
            'Expect to find COMPOSER_CACHE_DIR in built_environment'

    def test_build_composer_environment_forbids_overwriting_key_vars(self):
        ctx = utils.FormattedDict({
            'BP_DIR': '',
            'BUILD_DIR': '/usr/awesome',
            'WEBDIR': '',
            'PHP_VM': 'php',
            'TMPDIR': 'tmp',
            'LIBDIR': 'lib',
            'CACHE_DIR': 'cache',
            'PHPRC': '/usr/awesome/phpini',
        })

        write_config_stub = Dingus()

        with patches({
            'composer.extension.PHPComposerStrategy.write_config': write_config_stub
        }):
            self.extension_module.ComposerExtension(ctx)
            cr = self.extension_module.ComposerCommandRunner(ctx, None)

            built_environment = cr._build_composer_environment()

        eq_(built_environment['LD_LIBRARY_PATH'], '/usr/awesome/php/lib')
        eq_(built_environment['PHPRC'], 'tmp')

    def test_build_composer_environment_converts_vars_to_str(self):
        ctx = utils.FormattedDict({
            'BP_DIR': '',
            'BUILD_DIR': '/usr/awesome',
            'WEBDIR': '',
            'PHP_VM': 'php',
            'TMPDIR': 'tmp',
            'LIBDIR': 'lib',
            'CACHE_DIR': 'cache',
            'PHPRC': '/usr/awesome/phpini',
            'MY_DICTIONARY': {'KEY': 'VALUE'},
        })

        write_config_stub = Dingus()

        with patches({
            'composer.extension.PHPComposerStrategy.write_config': write_config_stub
        }):
            self.extension_module.ComposerExtension(ctx)
            cr = self.extension_module.ComposerCommandRunner(ctx, None)

            built_environment = cr._build_composer_environment()

        for key, val in built_environment.iteritems():
            assert type(val) == str, \
                "Expected [%s]:[%s] to be type `str`, but found type [%s]" % (
                    key, val, type(val))

    def test_build_composer_environment_has_missing_key(self):
        os.environ['SOME_KEY'] = 'does not matter'
        ctx = utils.FormattedDict({
            'BP_DIR': '',
            'BUILD_DIR': '/usr/awesome',
            'WEBDIR': '',
            'PHP_VM': 'php',
            'TMPDIR': 'tmp',
            'LIBDIR': 'lib',
            'CACHE_DIR': 'cache',
            'SOME_KEY': utils.wrap('{exact_match}')
        })

        write_config_stub = Dingus()

        with patches({
            'composer.extension.PHPComposerStrategy.write_config': write_config_stub
        }):
            self.extension_module.ComposerExtension(ctx)
            cr = self.extension_module.ComposerCommandRunner(ctx, None)

            try:
                built_environment = cr._build_composer_environment()
                assert "{exact_match}" == built_environment['SOME_KEY'], \
                    "value should match"
            except KeyError, e:
                assert 'exact_match' != e.message, \
                    "Should not try to evaluate value [%s]" % e
                raise

    def test_build_composer_environment_no_path(self):
        ctx = utils.FormattedDict({
            'BP_DIR': '',
            'BUILD_DIR': '/usr/awesome',
            'WEBDIR': '',
            'PHP_VM': 'php',
            'TMPDIR': 'tmp',
            'LIBDIR': 'lib',
            'CACHE_DIR': 'cache'
        })

        write_config_stub = Dingus()

        with patches({
            'composer.extension.PHPComposerStrategy.write_config': write_config_stub
        }):
            self.extension_module.ComposerExtension(ctx)
            cr = self.extension_module.ComposerCommandRunner(ctx, None)

            built_environment = cr._build_composer_environment()

        assert 'PATH' in built_environment, "should have PATH set"
        assert "/usr/awesome/php/bin" == built_environment['PATH'], \
            "PATH should contain path to PHP, found [%s]" \
            % built_environment['PATH']

    def test_build_composer_environment_existing_path(self):
        ctx = utils.FormattedDict({
            'BP_DIR': '',
            'BUILD_DIR': '/usr/awesome',
            'WEBDIR': '',
            'PHP_VM': 'php',
            'TMPDIR': 'tmp',
            'LIBDIR': 'lib',
            'CACHE_DIR': 'cache',
            'PATH': '/bin:/usr/bin'
        })

        write_config_stub = Dingus()

        with patches({
            'composer.extension.PHPComposerStrategy.write_config': write_config_stub
        }):
            self.extension_module.ComposerExtension(ctx)
            cr = self.extension_module.ComposerCommandRunner(ctx, None)

            built_environment = cr._build_composer_environment()

        assert 'PATH' in built_environment, "should have PATH set"
        assert built_environment['PATH'].endswith(":/usr/awesome/php/bin"), \
            "PATH should contain path to PHP, found [%s]" \
            % built_environment['PATH']

    def test_ld_library_path_for_php(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': '/usr/awesome',
            'WEBDIR': '',
            'PHP_VM': 'php'
        })
        stg = self.extension_module.PHPComposerStrategy(ctx)
        path = stg.ld_library_path()
        eq_('/usr/awesome/php/lib', path)

    def test_run_sets_github_oauth_token_if_present(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': '/usr/awesome',
            'PHP_VM': 'php',
            'TMPDIR': tempfile.gettempdir(),
            'LIBDIR': 'lib',
            'CACHE_DIR': 'cache',
            'COMPOSER_GITHUB_OAUTH_TOKEN': 'MADE_UP_TOKEN_VALUE',
            'BP_DIR': '',
            'WEBDIR': ''
        })

        instance_stub = Dingus()
        instance_stub._set_return_value("""{"rate": {"limit": 60, "remaining": 60}}""")

        stream_output_stub = Dingus()

        rewrite_stub = Dingus()

        environ_stub = Dingus()
        environ_stub._set_return_value('MADE_UP_TOKEN_VALUE')

        with patches({
            'StringIO.StringIO.getvalue': instance_stub,
            'composer.extension.stream_output': stream_output_stub,
            'composer.extension.utils.rewrite_cfgs': rewrite_stub,
            'os.environ.get': environ_stub
        }):
            ct = self.extension_module.ComposerExtension(ctx)

            builder_stub = Dingus(_ctx=ctx)
            ct._builder = builder_stub
            ct.composer_runner = \
                self.extension_module.ComposerCommandRunner(ctx, builder_stub)

            github_oauth_token_is_valid_stub = Dingus(
                'test_run_sets_github_oauth_token_if_present:'
                'github_oauth_token_is_valid_stub')
            github_oauth_token_is_valid_stub._set_return_value(True)
            ct._github_oauth_token_is_valid = github_oauth_token_is_valid_stub

            ct.run()

            executed_command = stream_output_stub.calls()[0].args[1]

        assert executed_command.find('config') > 0, 'did not see "config"'
        assert executed_command.find('-g') > 0, 'did not see "-g"'
        assert executed_command.find('github-oauth.github.com') > 0, \
            'did not see "github-oauth.github.com"'
        assert executed_command.find('"MADE_UP_TOKEN_VALUE"') > 0, \
            'did not see "MADE_UP_TOKEN_VALUE"'

    def test_run_does_not_set_github_oauth_if_missing(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': '/usr/awesome',
            'PHP_VM': 'php',
            'TMPDIR': tempfile.gettempdir(),
            'LIBDIR': 'lib',
            'CACHE_DIR': 'cache',
            'BP_DIR': '',
            'WEBDIR': ''
        })
        instance_stub = Dingus()
        instance_stub._set_return_value("""{"rate": {"limit": 60, "remaining": 60}}""")

        stream_output_stub = Dingus()

        rewrite_stub = Dingus()

        builder = Dingus(_ctx=ctx)

        setup_composer_github_token_stub = Dingus()

        with patches({
            'StringIO.StringIO.getvalue': instance_stub,
            'composer.extension.stream_output': stream_output_stub,
            'composer.extension.utils.rewrite_cfgs': rewrite_stub,
            'composer.extension.ComposerExtension.setup_composer_github_token': setup_composer_github_token_stub
        }):
            ct = self.extension_module.ComposerExtension(ctx)

            ct._builder = builder
            ct.composer_runner = \
                self.extension_module.ComposerCommandRunner(ctx, builder)
            ct.run()

            setup_composer_github_token_calls = setup_composer_github_token_stub.calls()

        assert 0 == len(setup_composer_github_token_calls), \
            'setup_composer_github_token() was called %s times, expected 0' % len(setup_composer_github_token_calls)

    def test_github_oauth_token_is_valid_uses_curl(self):
        ctx = utils.FormattedDict({
            'BP_DIR': '',
            'BUILD_DIR': '/usr/awesome',
            'PHP_VM': 'php',
            'TMPDIR': tempfile.gettempdir(),
            'LIBDIR': 'lib',
            'CACHE_DIR': 'cache',
            'WEBDIR': ''
        })

        instance_stub = Dingus()
        instance_stub._set_return_value("""{"resources": {}}""")

        stream_output_stub = Dingus(
            'test_github_oauth_token_uses_curl : stream_output')

        with patches({
            'StringIO.StringIO.getvalue': instance_stub,
            'composer.extension.stream_output': stream_output_stub,
        }):
            ct = self.extension_module.ComposerExtension(ctx)
            ct._github_oauth_token_is_valid('MADE_UP_TOKEN_VALUE')
            executed_command = stream_output_stub.calls()[0].args[1]

        assert stream_output_stub.calls().once(), \
            'stream_output() was called more than once'
        assert executed_command.find('curl') == 0, \
            'Curl was not called, executed_command was %s' % executed_command
        assert executed_command.find(
            '-H "Authorization: token MADE_UP_TOKEN_VALUE"') > 0, \
            'No token was passed to curl. Command was: %s' % executed_command
        assert executed_command.find('https://api.github.com/rate_limit') > 0,\
            'No URL was passed to curl. Command was: %s' % executed_command

    def test_github_oauth_token_is_valid_interprets_github_api_200_as_true(self):  # noqa
        ctx = utils.FormattedDict({
            'BP_DIR': '',
            'BUILD_DIR': tempfile.gettempdir(),
            'PHP_VM': 'php',
            'TMPDIR': tempfile.gettempdir(),
            'LIBDIR': 'lib',
            'CACHE_DIR': 'cache',
            'WEBDIR': ''
        })

        instance_stub = Dingus()
        instance_stub._set_return_value("""{"resources": {}}""")

        stream_output_stub = Dingus(
            'test_github_oauth_token_uses_curl : stream_output')

        with patches({
            'StringIO.StringIO.getvalue': instance_stub,
            'composer.extension.stream_output': stream_output_stub,
        }):
            ct = self.extension_module.ComposerExtension(ctx)
            result = ct._github_oauth_token_is_valid('MADE_UP_TOKEN_VALUE')

        assert result is True, \
            '_github_oauth_token_is_valid returned %s, expected True' % result

    def test_github_oauth_token_is_valid_interprets_github_api_401_as_false(self):  # noqa
        ctx = utils.FormattedDict({
            'BP_DIR': '',
            'BUILD_DIR': tempfile.gettempdir(),
            'PHP_VM': 'php',
            'TMPDIR': tempfile.gettempdir(),
            'LIBDIR': 'lib',
            'CACHE_DIR': 'cache',
            'WEBDIR': ''
        })

        instance_stub = Dingus()
        instance_stub._set_return_value("""{}""")

        stream_output_stub = Dingus(
            'test_github_oauth_token_uses_curl : stream_output')

        with patches({
            'StringIO.StringIO.getvalue': instance_stub,
            'composer.extension.stream_output': stream_output_stub,
        }):
            ct = self.extension_module.ComposerExtension(ctx)
            result = ct._github_oauth_token_is_valid('MADE_UP_TOKEN_VALUE')

        assert result is False, \
            '_github_oauth_token_is_valid returned %s, expected False' % result

    def test_no_github_api_call_with_cached_buildpack(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': tempfile.gettempdir(),
            'PHP_VM': 'php',
            'TMPDIR': tempfile.gettempdir(),
            'LIBDIR': 'lib',
            'CACHE_DIR': 'cache',
            'BP_DIR': '',
            'WEBDIR': ''
        })

        builder = Dingus(_ctx=ctx)

        path_exists_stub = Dingus()
        path_exists_stub._set_return_value(True)

        setup_composer_github_token_stub = Dingus()
        check_github_rate_exceeded_stub = Dingus()

        rewrite_stub = Dingus()

        stream_output_stub = Dingus(
            'test_github_oauth_token_uses_curl : stream_output')
        with patches({
            'os.path.exists': path_exists_stub,
            'composer.extension.ComposerExtension.setup_composer_github_token': setup_composer_github_token_stub,
            'composer.extension.ComposerExtension.check_github_rate_exceeded': check_github_rate_exceeded_stub,
            'composer.extension.utils.rewrite_cfgs': rewrite_stub,
            'composer.extension.stream_output': stream_output_stub
        }):
            ct = self.extension_module.ComposerExtension(ctx)
            ct._builder = builder
            ct.composer_runner = \
                    self.extension_module.ComposerCommandRunner(ctx, builder)
            ct.run()

        assert 0 == len(setup_composer_github_token_stub.calls()), \
                'setup_composer_github_token was called, expected no calls'
        assert 0 == len(check_github_rate_exceeded_stub.calls()), \
                'check_github_rate_exceeded was called, expected no calls'

    def test_github_download_rate_not_exceeded(self):  # noqa
        ctx = utils.FormattedDict({
            'BP_DIR': '',
            'BUILD_DIR': tempfile.gettempdir(),
            'PHP_VM': 'php',
            'TMPDIR': tempfile.gettempdir(),
            'LIBDIR': 'lib',
            'CACHE_DIR': 'cache',
            'WEBDIR': ''
        })

        instance_stub = Dingus()
        instance_stub._set_return_value("""{"rate": {"limit": 60, "remaining": 60}}""")

        stream_output_stub = Dingus(
            'test_github_oauth_token_uses_curl : stream_output')

        with patches({
            'StringIO.StringIO.getvalue': instance_stub,
            'composer.extension.stream_output': stream_output_stub,
        }):
            ct = self.extension_module.ComposerExtension(ctx)
            result = ct._github_rate_exceeded(False)

        assert result is False, \
            '_github_oauth_token_is_valid returned %s, expected False' % result

    def test_github_download_rate_is_exceeded(self):  # noqa
        ctx = utils.FormattedDict({
            'BP_DIR': '',
            'BUILD_DIR': tempfile.gettempdir(),
            'PHP_VM': 'php',
            'TMPDIR': tempfile.gettempdir(),
            'LIBDIR': 'lib',
            'CACHE_DIR': 'cache',
            'WEBDIR': ''
        })

        instance_stub = Dingus()
        instance_stub._set_return_value("""{"rate": {"limit": 60, "remaining": 0}}""")

        stream_output_stub = Dingus(
            'test_github_oauth_token_uses_curl : stream_output')

        with patches({
            'StringIO.StringIO.getvalue': instance_stub,
            'composer.extension.stream_output': stream_output_stub,
        }):
            ct = self.extension_module.ComposerExtension(ctx)
            result = ct._github_rate_exceeded(False)

        assert result is True, \
            '_github_oauth_token_is_valid returned %s, expected True' % result
