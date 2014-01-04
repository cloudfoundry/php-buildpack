import os
from nose.tools import eq_
from nose.tools import raises
from nose.tools import with_setup
from dingus import Dingus
from httpd import HttpdModuleInstaller

class TestHttpdModuleInstaller(object):

    def setUp(self):
        self.ctx = {
            'BUILD_DIR': '/tmp/build',
            'BP_DIR': './',
            'CACHE_DIR': '/tmp/cache'
        }
        self.builder = Dingus(_ctx=self.ctx)

    @with_setup(setup=setUp)
    def test_load_modules(self):
        cfgPath = 'tests/data/httpd/extra/httpd-modules.conf'
        i = HttpdModuleInstaller(self.builder)
        eq_(11, len(i._load_modules(cfgPath)))

    @raises(ValueError)
    @with_setup(setup=setUp)
    def test_from_config_file_dne(self):
        cfgPath = 'tests/data/httpd/extra/httpd-dne.conf'
        i = HttpdModuleInstaller(self.builder)
        i.from_config(cfgPath)

    @with_setup(setup=setUp)
    def test_from_config_file(self):
        cfgPath = 'tests/data/httpd/extra/httpd-modules.conf'
        i = HttpdModuleInstaller(self.builder)
        i.from_config(cfgPath)
        eq_(11, len(i._modules))

    @with_setup(setup=setUp)
    def test_from_directory(self):
        cfgPath = 'tests/data/httpd/'
        i = HttpdModuleInstaller(self.builder)
        i.from_config(cfgPath)
        eq_(12, len(i._modules))
