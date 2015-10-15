import os
import os.path
import tempfile
import shutil
import subprocess
import imp
from nose.tools import eq_


class BaseRewriteScript(object):
    def __init__(self):
        info = imp.find_module('runner', ['lib/build_pack_utils'])
        self.run = imp.load_module('runner', *info)

    def setUp(self):
        self.rewrite = os.path.abspath("bin/rewrite")
        self.env = {'PYTHONPATH': os.path.abspath('lib')}
        self.env.update(os.environ)
        # setup config
        self.cfg_dir = tempfile.mkdtemp(prefix='config-')
        os.rmdir(self.cfg_dir)
        # setup directory to run from
        self.run_dir = tempfile.mkdtemp(prefix='run-')
        os.makedirs(os.path.join(self.run_dir, 'logs'))
        os.makedirs(os.path.join(self.run_dir, 'bin'))

    def tearDown(self):
        if os.path.exists(self.cfg_dir):
            shutil.rmtree(self.cfg_dir)
        if os.path.exists(self.run_dir):
            shutil.rmtree(self.run_dir)


class TestRewriteScriptPhp(BaseRewriteScript):
    def __init__(self):
        BaseRewriteScript.__init__(self)

    def setUp(self):
        BaseRewriteScript.setUp(self)
        shutil.copytree('defaults/config/php/5.5.x', self.cfg_dir)

    def tearDown(self):
        BaseRewriteScript.tearDown(self)

    def test_rewrite_no_args(self):
        try:
            self.run.check_output(self.rewrite,
                                  cwd=self.run_dir,
                                  env=self.env,
                                  stderr=subprocess.STDOUT,
                                  shell=True)
            assert False
        except self.run.CalledProcessError, e:
            eq_('Argument required!  Specify path to configuration '
                'directory.\n', e.output)
            eq_(255, e.returncode)

    def test_rewrite_arg_file(self):
        cfg_file = os.path.join(self.cfg_dir, 'php.ini')
        res = self.run.check_output("%s %s" % (self.rewrite, cfg_file),
                                    env=self.env,
                                    cwd=self.run_dir,
                                    stderr=subprocess.STDOUT,
                                    shell=True)
        eq_('', res)
        with open(os.path.join(self.cfg_dir, 'php.ini')) as fin:
            cfgFile = fin.read()
            eq_(-1, cfgFile.find('@{HOME}'))
            eq_(-1, cfgFile.find('@{TMPDIR}'))

    def test_rewrite_arg_dir(self):
        res = self.run.check_output("%s %s" % (self.rewrite, self.cfg_dir),
                                    env=self.env,
                                    cwd=self.run_dir,
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


class TestRewriteScriptWithHttpd(BaseRewriteScript):
    def __init__(self):
        BaseRewriteScript.__init__(self)

    def setUp(self):
        BaseRewriteScript.setUp(self)
        shutil.copytree('defaults/config/httpd', self.cfg_dir)

    def tearDown(self):
        BaseRewriteScript.tearDown(self)

    def test_rewrite_with_sub_dirs(self):
        res = self.run.check_output("%s %s" % (self.rewrite, self.cfg_dir),
                                    env=self.env,
                                    cwd=self.run_dir,
                                    stderr=subprocess.STDOUT,
                                    shell=True)
        eq_('', res)
        for root, dirs, files in os.walk(self.cfg_dir):
            for f in files:
                with open(os.path.join(root, f)) as fin:
                    eq_(-1, fin.read().find('@{'))


class TestRewriteScriptWithNginx(BaseRewriteScript):
    def __init__(self):
        BaseRewriteScript.__init__(self)

    def setUp(self):
        BaseRewriteScript.setUp(self)
        self.env = {'PYTHONPATH': os.path.abspath('lib'),
                    'PORT': '80'}
        self.env.update(os.environ)
        shutil.copytree('defaults/config/nginx', self.cfg_dir)

    def tearDown(self):
        BaseRewriteScript.tearDown(self)

    def test_rewrite(self):
        res = self.run.check_output("%s %s" % (self.rewrite, self.cfg_dir),
                                    env=self.env,
                                    cwd=self.run_dir,
                                    stderr=subprocess.STDOUT,
                                    shell=True)
        eq_('', res)
        for root, dirs, files in os.walk(self.cfg_dir):
            for f in files:
                with open(os.path.join(root, f)) as fin:
                    eq_(-1, fin.read().find('@{'), f)
