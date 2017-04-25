import os
import os.path
import tempfile
import shutil
import mock
from nose.tools import eq_
from nose.tools import assert_raises_regexp
from build_pack_utils import utils
from compile_helpers import setup_webdir_if_it_doesnt_exist
from compile_helpers import convert_php_extensions
from compile_helpers import is_web_app
from compile_helpers import find_stand_alone_app_to_run
from compile_helpers import load_manifest
from compile_helpers import find_all_php_versions
from compile_helpers import validate_php_version
from compile_helpers import validate_php_ini_extensions
from compile_helpers import setup_log_dir


class TestCompileHelpers(object):
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

    def assert_exists(self, *args):
        eq_(True, os.path.exists(os.path.join(*args)),
            "Does not exists: %s" % os.path.join(*args))

    def test_setup_log_dir(self):
        eq_(False, os.path.exists(os.path.join(self.build_dir, 'logs')))
        setup_log_dir({
            'BUILD_DIR': self.build_dir
        })
        self.assert_exists(self.build_dir, 'logs')

    def test_setup_log_dir_when_exists(self):
        os.makedirs(os.path.join(self.build_dir, 'logs'))
        setup_log_dir({
            'BUILD_DIR': self.build_dir
        })
        self.assert_exists(self.build_dir, 'logs')

    def test_setup_if_webdir_exists(self):
        shutil.copytree('tests/data/app-1', self.build_dir)
        setup_webdir_if_it_doesnt_exist(utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'WEBDIR': 'htdocs',
            'LIBDIR': 'lib'
        }))
        self.assert_exists(self.build_dir, 'htdocs')
        self.assert_exists(self.build_dir, 'htdocs', 'index.php')
        self.assert_exists(self.build_dir, 'htdocs', 'info.php')
        self.assert_exists(self.build_dir, 'htdocs',
                           'technical-difficulties1.jpg')
        self.assert_exists(self.build_dir, '.bp-config')
        self.assert_exists(self.build_dir, '.bp-config', 'options.json')
        self.assert_exists(self.build_dir, '.bp-config', 'httpd', 'extra',
                           'httpd-remoteip.conf')
        eq_(2, len(os.listdir(self.build_dir)))
        eq_(3, len(os.listdir(os.path.join(self.build_dir, 'htdocs'))))

    def test_setup_if_custom_webdir_exists(self):
        shutil.copytree('tests/data/app-6', self.build_dir)
        setup_webdir_if_it_doesnt_exist(utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'WEBDIR': 'public',
            'LIBDIR': 'lib'
        }))
        self.assert_exists(self.build_dir, 'public')
        self.assert_exists(self.build_dir, 'public', 'index.php')
        self.assert_exists(self.build_dir, 'public', 'info.php')
        self.assert_exists(self.build_dir, 'public',
                           'technical-difficulties1.jpg')
        self.assert_exists(self.build_dir, '.bp-config')
        self.assert_exists(self.build_dir, '.bp-config', 'options.json')
        self.assert_exists(self.build_dir, '.bp-config', 'httpd', 'extra',
                           'httpd-remoteip.conf')
        eq_(3, len(os.listdir(self.build_dir)))
        eq_(3, len(os.listdir(os.path.join(self.build_dir, 'public'))))

    def test_setup_if_htdocs_does_not_exist(self):
        shutil.copytree('tests/data/app-2', self.build_dir)
        setup_webdir_if_it_doesnt_exist(utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'WEBDIR': 'htdocs',
            'LIBDIR': 'lib'
        }))
        self.assert_exists(self.build_dir, 'htdocs')
        self.assert_exists(self.build_dir, 'htdocs', 'index.php')
        self.assert_exists(self.build_dir, 'htdocs', 'info.php')
        self.assert_exists(self.build_dir, 'htdocs',
                           'technical-difficulties1.jpg')
        self.assert_exists(self.build_dir, '.bp-config')
        self.assert_exists(self.build_dir, '.bp-config', 'options.json')
        self.assert_exists(self.build_dir, '.bp-config', 'httpd', 'extra',
                           'httpd-remoteip.conf')
        eq_(2, len(os.listdir(self.build_dir)))
        eq_(3, len(os.listdir(os.path.join(self.build_dir, 'htdocs'))))

    def test_setup_if_htdocs_does_not_exist_but_library_does(self):
        shutil.copytree('tests/data/app-7', self.build_dir)
        setup_webdir_if_it_doesnt_exist(utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'WEBDIR': 'htdocs',
            'LIBDIR': 'lib'
        }))
        self.assert_exists(self.build_dir, 'htdocs')
        self.assert_exists(self.build_dir, 'htdocs', 'index.php')
        self.assert_exists(self.build_dir, 'htdocs', 'info.php')
        self.assert_exists(self.build_dir, 'htdocs',
                           'technical-difficulties1.jpg')
        self.assert_exists(self.build_dir, 'htdocs', 'library')
        self.assert_exists(self.build_dir, 'htdocs', 'library', 'junk.php')
        self.assert_exists(self.build_dir, 'lib')
        self.assert_exists(self.build_dir, 'lib', 'test.php')
        self.assert_exists(self.build_dir, '.bp-config')
        self.assert_exists(self.build_dir, '.bp-config', 'options.json')
        self.assert_exists(self.build_dir, '.bp-config', 'httpd', 'extra',
                           'httpd-remoteip.conf')
        eq_(4, len(os.listdir(self.build_dir)))
        eq_(4, len(os.listdir(os.path.join(self.build_dir, 'htdocs'))))

    def test_setup_if_custom_webdir_does_not_exist(self):
        shutil.copytree('tests/data/app-2', self.build_dir)
        setup_webdir_if_it_doesnt_exist(utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'WEBDIR': 'public',
            'LIBDIR': 'lib'
        }))
        self.assert_exists(self.build_dir, 'public')
        self.assert_exists(self.build_dir, 'public', 'index.php')
        self.assert_exists(self.build_dir, 'public', 'info.php')
        self.assert_exists(self.build_dir, 'public',
                           'technical-difficulties1.jpg')
        self.assert_exists(self.build_dir, '.bp-config')
        self.assert_exists(self.build_dir, '.bp-config', 'options.json')
        self.assert_exists(self.build_dir, '.bp-config', 'httpd', 'extra',
                           'httpd-remoteip.conf')
        eq_(2, len(os.listdir(self.build_dir)))
        eq_(3, len(os.listdir(os.path.join(self.build_dir, 'public'))))

    def test_setup_if_htdocs_does_not_exist_with_extensions(self):
        shutil.copytree('tests/data/app-4', self.build_dir)
        setup_webdir_if_it_doesnt_exist(utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'WEBDIR': 'htdocs',
            'LIBDIR': 'lib'
        }))
        self.assert_exists(self.build_dir, 'htdocs')
        self.assert_exists(self.build_dir, 'htdocs', 'index.php')
        self.assert_exists(self.build_dir, 'htdocs', 'info.php')
        self.assert_exists(self.build_dir, 'htdocs',
                           'technical-difficulties1.jpg')
        self.assert_exists(self.build_dir, '.bp-config')
        self.assert_exists(self.build_dir, '.bp-config', 'options.json')
        self.assert_exists(self.build_dir, '.bp-config', 'httpd', 'extra',
                           'httpd-remoteip.conf')
        self.assert_exists(self.build_dir, '.bp')
        self.assert_exists(self.build_dir, '.bp', 'logs')
        self.assert_exists(self.build_dir, '.bp', 'logs', 'some.log')
        self.assert_exists(self.build_dir, '.extensions')
        self.assert_exists(self.build_dir, '.extensions', 'some-ext')
        self.assert_exists(self.build_dir, '.extensions', 'some-ext',
                           'extension.py')
        eq_(4, len(os.listdir(self.build_dir)))
        eq_(3, len(os.listdir(os.path.join(self.build_dir, 'htdocs'))))

    def test_setup_if_custom_webdir_does_not_exist_with_extensions(self):
        shutil.copytree('tests/data/app-4', self.build_dir)
        setup_webdir_if_it_doesnt_exist(utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'WEBDIR': 'public',
            'LIBDIR': 'lib'
        }))
        self.assert_exists(self.build_dir, 'public')
        self.assert_exists(self.build_dir, 'public', 'index.php')
        self.assert_exists(self.build_dir, 'public', 'info.php')
        self.assert_exists(self.build_dir, 'public',
                           'technical-difficulties1.jpg')
        self.assert_exists(self.build_dir, '.bp-config')
        self.assert_exists(self.build_dir, '.bp-config', 'options.json')
        self.assert_exists(self.build_dir, '.bp-config', 'httpd', 'extra',
                           'httpd-remoteip.conf')
        self.assert_exists(self.build_dir, '.bp')
        self.assert_exists(self.build_dir, '.bp', 'logs')
        self.assert_exists(self.build_dir, '.bp', 'logs', 'some.log')
        self.assert_exists(self.build_dir, '.extensions')
        self.assert_exists(self.build_dir, '.extensions', 'some-ext')
        self.assert_exists(self.build_dir, '.extensions', 'some-ext',
                           'extension.py')
        eq_(4, len(os.listdir(self.build_dir)))
        eq_(3, len(os.listdir(os.path.join(self.build_dir, 'public'))))

    def test_system_files_not_moved_into_webdir(self):
        shutil.copytree('tests/data/app-with-all-possible-system-files-that-should-not-move', self.build_dir)
        setup_webdir_if_it_doesnt_exist(utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'WEBDIR': 'htdocs',
            'LIBDIR': 'lib'
        }))
        self.assert_exists(self.build_dir, '.bp')
        self.assert_exists(self.build_dir, '.extensions')
        self.assert_exists(self.build_dir, '.bp-config')
        self.assert_exists(self.build_dir, 'manifest.yml')
        self.assert_exists(self.build_dir, '.profile.d')
        self.assert_exists(self.build_dir, '.profile')

    def test_setup_if_htdocs_with_stand_alone_app(self):
        shutil.copytree('tests/data/app-5', self.build_dir)
        setup_webdir_if_it_doesnt_exist(utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'WEB_SERVER': 'none'
        }))
        self.assert_exists(self.build_dir, 'app.php')
        eq_(1, len(os.listdir(self.build_dir)))

    def test_convert_php_extensions_56(self):
        ctx = {
            'PHP_VERSION': '5.6.x',
            'PHP_EXTENSIONS': ['mod1', 'mod2', 'mod3'],
            'ZEND_EXTENSIONS': ['zmod1', 'zmod2']
        }
        convert_php_extensions(ctx)
        eq_('extension=mod1.so\nextension=mod2.so\nextension=mod3.so',
            ctx['PHP_EXTENSIONS'])
        eq_('zend_extension="zmod1.so"\nzend_extension="zmod2.so"',
            ctx['ZEND_EXTENSIONS'])

    def test_convert_php_extensions_56_none(self):
        ctx = {
            'PHP_VERSION': '5.6.x',
            'PHP_EXTENSIONS': [],
            'ZEND_EXTENSIONS': []
        }
        convert_php_extensions(ctx)
        eq_('', ctx['PHP_EXTENSIONS'])
        eq_('', ctx['ZEND_EXTENSIONS'])

    def test_convert_php_extensions_56_one(self):
        ctx = {
            'PHP_VERSION': '5.6.x',
            'PHP_EXTENSIONS': ['mod1'],
            'ZEND_EXTENSIONS': ['zmod1']
        }
        convert_php_extensions(ctx)
        eq_('zend_extension="zmod1.so"',
            ctx['ZEND_EXTENSIONS'])


    def setup_php_ini_dir(self, extensions):
        ini_dir = os.path.join(self.build_dir, '.bp-config', 'php', 'php.ini.d')
        os.makedirs(ini_dir)
        with open(os.path.join(ini_dir, 'somthing.ini'), 'w') as f:
            f.write(extensions)


    @mock.patch('compile_helpers._get_supported_php_extensions', return_value=['pumpkin'])
    @mock.patch('compile_helpers._get_compiled_modules', return_value=['pie'])
    def test_validate_php_ini_extensions_when_extension_not_available(self, supported_func, compiled_func):
        ctx = {
            'BUILD_DIR': self.build_dir
        }
        self.setup_php_ini_dir("extension =pumpkin.so\nextension=apple.so\nextension=pie.so")
        with assert_raises_regexp(RuntimeError, "The extension 'apple' is not provided by this buildpack."):
            validate_php_ini_extensions(ctx)

    @mock.patch('compile_helpers._get_supported_php_extensions', return_value=['pumpkin'])
    @mock.patch('compile_helpers._get_compiled_modules', return_value=['pie'])
    def test_validate_php_ini_extensions_when_extension_not_available_and_listed_in_section(self, supported_func, compiled_func):
        ctx = {
            'BUILD_DIR': self.build_dir
        }
        self.setup_php_ini_dir("[php]\nextension =pumpkin.so\nextension=blueberry.so\nextension=pie.so")
        with assert_raises_regexp(RuntimeError, "The extension 'blueberry' is not provided by this buildpack."):
            validate_php_ini_extensions(ctx)

    @mock.patch('compile_helpers._get_supported_php_extensions', return_value=['pumpkin', 'apple'])
    @mock.patch('compile_helpers._get_compiled_modules', return_value=['pie'])
    def test_validate_php_ini_extensions_when_extension_is_supported_php_extension(self, supported_func, compiled_func):
        ctx = {
            'BUILD_DIR': self.build_dir
        }
        self.setup_php_ini_dir("extension=pumpkin.so\nextension= apple.so\nextension=pie.so")
        validate_php_ini_extensions(ctx)

    @mock.patch('compile_helpers._get_supported_php_extensions', return_value=['pumpkin'])
    @mock.patch('compile_helpers._get_compiled_modules', return_value=['pie', 'apple'])
    def test_validate_php_ini_extensions_when_extension_is_compiled_module(self, supported_func, compiled_func):
        ctx = {
            'BUILD_DIR': self.build_dir
        }
        self.setup_php_ini_dir("extension=pumpkin.so\nextension=apple.so\nextension = \"pie.so\"")
        validate_php_ini_extensions(ctx)

    @mock.patch('compile_helpers._get_supported_php_extensions', return_value=['pumpkin'])
    @mock.patch('compile_helpers._get_compiled_modules', return_value=['pie', 'apple'])
    def test_validate_php_ini_extensions_when_no_php_ini_dir(self, supported_func, compiled_func):
        ctx = {
            'BUILD_DIR': self.build_dir
        }
        validate_php_ini_extensions(ctx)


    def test_is_web_app(self):
        ctx = {}
        eq_(True, is_web_app(ctx))
        ctx['WEB_SERVER'] = 'nginx'
        eq_(True, is_web_app(ctx))
        ctx['WEB_SERVER'] = 'httpd'
        eq_(True, is_web_app(ctx))
        ctx['WEB_SERVER'] = 'none'
        eq_(False, is_web_app(ctx))

    def test_find_stand_alone_app_to_run_app_start_cmd(self):
        ctx = {'APP_START_CMD': "echo 'Hello World!'"}
        eq_("echo 'Hello World!'", find_stand_alone_app_to_run(ctx))
        results = ('app.php', 'main.php', 'run.php', 'start.php', 'app.php')
        for i, res in enumerate(results):
            ctx = {'BUILD_DIR': 'tests/data/standalone/test%d' % (i + 1)}
            eq_(res, find_stand_alone_app_to_run(ctx))

    def test_load_manifest(self):
        ctx = {'BP_DIR': '.'}
        manifest = load_manifest(ctx)
        assert manifest is not None
        assert 'dependencies' in manifest.keys()
        assert 'language' in manifest.keys()
        assert 'url_to_dependency_map' in manifest.keys()
        assert 'exclude_files' in manifest.keys()

    def test_find_all_php_versions(self):
        ctx = {'BP_DIR': '.'}
        manifest = load_manifest(ctx)
        dependencies = manifest['dependencies']
        versions = find_all_php_versions(dependencies)
        eq_(2, len([v for v in versions if v.startswith('5.6.')]))
        eq_(2, len([v for v in versions if v.startswith('7.0.')]))
        eq_(2, len([v for v in versions if v.startswith('7.1.')]))

    def test_validate_php_version(self):
        ctx = {
            'ALL_PHP_VERSIONS': ['5.6.31', '5.6.30'],
            'PHP_56_LATEST': '5.6.31',
            'PHP_VERSION': '5.6.30'
        }
        validate_php_version(ctx)
        eq_('5.6.30', ctx['PHP_VERSION'])
        ctx['PHP_VERSION'] = '5.6.29'
        validate_php_version(ctx)
        eq_('5.6.31', ctx['PHP_VERSION'])
        ctx['PHP_VERSION'] = '5.6.30'
        validate_php_version(ctx)
        eq_('5.6.30', ctx['PHP_VERSION'])
