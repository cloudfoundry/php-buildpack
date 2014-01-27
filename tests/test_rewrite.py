import os
import os.path
import tempfile
import shutil
import subprocess
import imp
from nose.tools import eq_
from nose.tools import with_setup


class TestRewriteScript(object):
    def __init__(self):
        info = imp.find_module('runner', ['lib/build_pack_utils'])
        self.run = imp.load_module('runner', *info)

    def setUp(self):
        self.cfg_dir = tempfile.mkdtemp(prefix='config-')
        os.rmdir(self.cfg_dir)
        shutil.copytree('defaults/config/php/5.5.x', self.cfg_dir)

    def tearDown(self):
        if os.path.exists(self.cfg_dir):
            shutil.rmtree(self.cfg_dir)

    @with_setup(setup=setUp, teardown=tearDown)
    def test_rewrite_no_args(self):
        try:
            self.run.check_output("bin/rewrite",
                                  stderr=subprocess.STDOUT,
                                  shell=True)
        except self.run.CalledProcessError, e:
            eq_('Argument required!  Specify path to configuration '
                'directory.\n', e.output)
            eq_(255, e.returncode)

    @with_setup(setup=setUp, teardown=tearDown)
    def test_rewrite_arg_file(self):
        try:
            cfg_file = os.path.join(self.cfg_dir, 'php.ini')
            self.run.check_output("bin/rewrite %s" % cfg_file,
                                  stderr=subprocess.STDOUT,
                                  shell=True)
        except self.run.CalledProcessError, e:
            eq_('Path [%s] is not a directory.\n' % cfg_file, e.output)
            eq_(255, e.returncode)

    @with_setup(setup=setUp, teardown=tearDown)
    def test_rewrite_arg_dir(self):
        res = self.run.check_output("bin/rewrite %s" % self.cfg_dir,
                                    stderr=subprocess.STDOUT,
                                    shell=True)
        eq_('', res)
        with open(os.path.join(self.cfg_dir, 'php.ini')) as fin:
            cfgFile = fin.read()
            eq_(-1, cfgFile.find('@{HOME}'))
            eq_(-1, cfgFile.find('@{TMPDIR}'))
        with open(os.path.join(self.cfg_dir, 'php-fpm.conf')) as fin:
            cfgFile = fin.read()
            eq_(-1, cfgFile.find('@{HOME}'))
            eq_(-1, cfgFile.find('@{TMPDIR}'))
            eq_(True, cfgFile.find('www@my.domain.com') >= 0)

