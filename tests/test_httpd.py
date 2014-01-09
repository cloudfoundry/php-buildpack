import os
import tempfile
import shutil
from nose.tools import eq_
from nose.tools import raises
from nose.tools import with_setup
from dingus import Dingus
from httpd import HttpdModuleInstaller

class TestHttpdModuleInstaller(object):

    def setUp(self):
        self.ctx = {
            'BUILD_DIR': tempfile.mkdtemp('build-'),
            'BP_DIR': './',
            'CACHE_DIR': tempfile.mkdtemp('cache-')
        }
        self.builder = Dingus(_ctx=self.ctx)
        self.installer = Dingus()

    def tearDown(self):
        if os.path.exists(self.ctx['BUILD_DIR']):
            shutil.rmtree(self.ctx['BUILD_DIR'])
        if os.path.exists(self.ctx['CACHE_DIR']):
            shutil.rmtree(self.ctx['CACHE_DIR'])

    @with_setup(setup=setUp, teardown=tearDown)
    def test_load_modules(self):
        cfgPath = 'tests/data/httpd/extra/httpd-modules.conf'
        i = HttpdModuleInstaller(self.builder, self.installer)
        eq_(11, len(i._load_modules(cfgPath)))

    @with_setup(setup=setUp, teardown=tearDown)
    def test_from_config_file_dne(self):
        cfgPath = 'tests/data/httpd/extra/httpd-dne.conf'
        i = HttpdModuleInstaller(self.builder, self.installer)
        res = i.from_config(cfgPath)
        eq_(i, res)
        eq_(0, len(i._modules))

    @with_setup(setup=setUp, teardown=tearDown)
    def test_from_config_file(self):
        cfgPath = 'tests/data/httpd/extra/httpd-modules.conf'
        i = HttpdModuleInstaller(self.builder, self.installer)
        res = i.from_config(cfgPath)
        eq_(i, res)
        eq_(11, len(i._modules))

    @with_setup(setup=setUp, teardown=tearDown)
    def test_from_directory(self):
        cfgPath = 'tests/data/httpd/'
        i = HttpdModuleInstaller(self.builder, self.installer)
        res = i.from_config(cfgPath)
        eq_(i, res)
        eq_(12, len(i._modules))

    @with_setup(setup=setUp, teardown=tearDown)
    def test_exists_in_both_bp_and_app_and_unique(self):
        cfg_folder = os.path.join(
            self.ctx['BUILD_DIR'],
            'tests/data/httpd/extra')
        os.makedirs(cfg_folder)
        with open(os.path.join(cfg_folder, 'httpd-modules.conf'), 'wt') as f:
            f.write('LoadModule authn_dbd_module modules/mod_authn_dbd.so\n')
            f.write(
                'LoadModule authn_socache_module modules/mod_authn_socache.so\n')
            f.write('LoadModule dir_module modules/mod_dir.so\n')
        cfgPath = 'tests/data/httpd/extra/httpd-modules.conf'
        i = HttpdModuleInstaller(self.builder, self.installer)
        res = i.from_config(cfgPath)
        eq_(i, res)
        eq_(13, len(i._modules))

    @with_setup(setup=setUp, teardown=tearDown)
    def test_done(self):
        cfgPath = 'tests/data/httpd/'
        i = HttpdModuleInstaller(self.builder, self.installer)
        i._cf = Dingus()
        res = i.from_config(cfgPath)
        eq_(i, res)
        res = i.done()
        eq_(self.installer, res)
        eq_(12, len(i._cf.install_binary_direct.calls()))
        eq_(True, i._cf.install_binary_direct.calls()[0].args[0].endswith('.tar.gz'))
        eq_(True, i._cf.install_binary_direct.calls()[0].args[1].endswith('.tar.gz.sha1'))
        eq_(True, i._cf.install_binary_direct.calls()[0].args[2].endswith('httpd/modules'))
