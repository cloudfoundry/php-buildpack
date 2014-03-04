import os
import os.path
import tempfile
import shutil
from nose.tools import eq_
from nose.tools import with_setup
from build_pack_utils import utils
from compile_helpers import setup_htdocs_if_it_doesnt_exist
from compile_helpers import convert_php_extensions
from compile_helpers import build_php_environment


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

    @with_setup(setup=setUp, teardown=tearDown)
    def test_setup_if_htdocs_exists(self):
        shutil.copytree('tests/data/app-1', self.build_dir)
        setup_htdocs_if_it_doesnt_exist(utils.FormattedDict({
            'BUILD_DIR': self.build_dir
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

    @with_setup(setup=setUp, teardown=tearDown)
    def test_setup_if_htdocs_does_not_exist(self):
        shutil.copytree('tests/data/app-2', self.build_dir)
        setup_htdocs_if_it_doesnt_exist(utils.FormattedDict({
            'BUILD_DIR': self.build_dir
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

    def test_convert_php_extensions(self):
        ctx = {
            'PHP_EXTENSIONS': ['mod1', 'mod2', 'mod3'],
            'ZEND_EXTENSIONS': ['zmod1', 'zmod2']
        }
        convert_php_extensions(ctx)
        eq_('extension=mod1.so\nextension=mod2.so\nextension=mod3.so',
            ctx['PHP_EXTENSIONS'])
        eq_('zend_extension="@{HOME}/php/lib/php/extensions/'
            'no-debug-non-zts-20100525/zmod1.so"\n'
            'zend_extension="@{HOME}/php/lib/php/extensions/'
            'no-debug-non-zts-20100525/zmod2.so"',
            ctx['ZEND_EXTENSIONS'])

    def test_convert_php_extensions_none(self):
        ctx = {
            'PHP_EXTENSIONS': [],
            'ZEND_EXTENSIONS': []
        }
        convert_php_extensions(ctx)
        eq_('', ctx['PHP_EXTENSIONS'])
        eq_('', ctx['ZEND_EXTENSIONS'])

    def test_convert_php_extensions_one(self):
        ctx = {
            'PHP_EXTENSIONS': ['mod1'],
            'ZEND_EXTENSIONS': ['zmod1']
        }
        convert_php_extensions(ctx)
        eq_('extension=mod1.so', ctx['PHP_EXTENSIONS'])
        eq_('zend_extension="@{HOME}/php/lib/php/extensions/'
            'no-debug-non-zts-20100525/zmod1.so"',
            ctx['ZEND_EXTENSIONS'])

    def test_build_php_environment(self):
        ctx = {}
        build_php_environment(ctx)
        eq_(True, 'PHP_ENV' in ctx.keys())
        eq_(True, ctx['PHP_ENV'].find('env[HOME]') >= 0)
        eq_(True, ctx['PHP_ENV'].find('env[PATH]') >= 0)
