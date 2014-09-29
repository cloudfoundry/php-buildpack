import os
import tempfile
import shutil
from nose.tools import eq_
from build_pack_utils import utils
from extension_helpers import PHPExtensionHelper

class TestPHPExtensionHelper(object):
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

    def test_basic(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.4.32'
        })
        ext = PHPExtensionHelper(ctx)
        eq_(2, len(ext._ctx))
        eq_({}, ext._services)
        eq_({}, ext._application)
        eq_(1822, len(ext._php_ini._lines))
        eq_(517, len(ext._php_fpm._lines))
        eq_('20100525', ext._php_api)
        eq_(False, ext.should_install())
        eq_(False, ext.should_configure())
        eq_(None, ext.configure())
        eq_((), ext.preprocess_commands())
        eq_({}, ext.service_commands())
        eq_({}, ext.service_environment())

    def test_merge_defaults(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.4.32',
            'SOME_JUNK': 'jkl;'
        })
        class MyExtn(PHPExtensionHelper):
            def defaults(self):
                return {
                    'DEFAULT_JUNK': 'asdf',
                    'SOME_JUNK': 'qwerty'
                }
        ext = MyExtn(ctx)
        eq_(4, len(ext._ctx))
        eq_('asdf', ext._ctx['DEFAULT_JUNK'])
        eq_('jkl;', ext._ctx['SOME_JUNK'])
        eq_('5.4.32', ext._ctx['PHP_VERSION'])
