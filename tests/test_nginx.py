import tempfile
import shutil
import imp
import os
from nose.tools import eq_


class TestNginxExtension(object):
    def test_rewrite_config_file(self):
        ctx = {
            'HOME': '/home/user',
            'TMPDIR': '/tmp'
        }
        cfg_path = os.path.join(tempfile.gettempdir(), 'conf')
        cfg_file = os.path.join(tempfile.gettempdir(), 'conf', 'test-cfg.txt')
        try:
            os.makedirs(cfg_path)
            shutil.copy('tests/data/test-cfg.txt', cfg_file)
            info = imp.find_module('extension', ['lib/nginx'])
            module = imp.load_module('extension', *info)
            module.rewrite_nginx_conf(cfg_path, ctx)
            lines = open(cfg_file).readlines()
            eq_(2, len(lines))
            eq_('/home/user/test.cfg\n', lines[0])
            eq_('/tmp/some-file.txt\n', lines[1])
        finally:
            shutil.rmtree(cfg_path)
