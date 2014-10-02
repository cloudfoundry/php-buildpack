import os
import os.path
import tempfile
import shutil
import json
from nose.tools import eq_
from nose.tools import with_setup
from build_pack_utils import utils
from build_pack_utils import BuildPack
from dingus import Dingus


codizy_extn = utils.load_extension('extensions/codizy')


class TestCodizyInstaller(object):
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

    def test_configure(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.4.33',
            'PHP_EXTENSIONS': []
        })
        codizy = codizy_extn.CodizyExtension(ctx)
        codizy._configure()
        eq_(True, 'xhprof' in ctx['PHP_EXTENSIONS'])
        eq_(True, 'codizy' in ctx['PHP_EXTENSIONS'])
        eq_(True, 'curl' in ctx['PHP_EXTENSIONS'])
        eq_(True, 'gettext' in ctx['PHP_EXTENSIONS'])
        eq_(True, 'mbstring' in ctx['PHP_EXTENSIONS'])
        eq_(True, 'openssl' in ctx['PHP_EXTENSIONS'])
        eq_(6, len(ctx['PHP_EXTENSIONS']))
        eq_(True, 'ioncube' in ctx['ZEND_EXTENSIONS'])
        eq_(1, len(ctx['ZEND_EXTENSIONS']))

    def test_configure_doesnt_override_extns(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.4.33',
            'PHP_EXTENSIONS': ['a', 'b'],
            'ZEND_EXTENSIONS': ['opcache', 'xdebug']
        })
        codizy = codizy_extn.CodizyExtension(ctx)
        codizy._configure()
        eq_(True, 'xhprof' in ctx['PHP_EXTENSIONS'])
        eq_(True, 'codizy' in ctx['PHP_EXTENSIONS'])
        eq_(True, 'curl' in ctx['PHP_EXTENSIONS'])
        eq_(True, 'gettext' in ctx['PHP_EXTENSIONS'])
        eq_(True, 'mbstring' in ctx['PHP_EXTENSIONS'])
        eq_(True, 'openssl' in ctx['PHP_EXTENSIONS'])
        eq_(True, 'a' in ctx['PHP_EXTENSIONS'])
        eq_(True, 'b' in ctx['PHP_EXTENSIONS'])
        eq_(8, len(ctx['PHP_EXTENSIONS']))
        eq_(True, 'ioncube' in ctx['ZEND_EXTENSIONS'])
        eq_('ioncube', ctx['ZEND_EXTENSIONS'][0])
        eq_(3, len(ctx['ZEND_EXTENSIONS']))

    def test_should_not_compile_php56(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.6.0'
        })
        codizy = codizy_extn.CodizyExtension(ctx)
        eq_(False, codizy._should_compile())

    def test_should_compile_not_set(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.4.33'
        })
        codizy = codizy_extn.CodizyExtension(ctx)
        eq_(False, codizy._should_compile())

    def test_should_compile_enabled(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.4.33',
            'CODIZY_INSTALL': True
        })
        codizy = codizy_extn.CodizyExtension(ctx)
        eq_(True, codizy._should_compile())

    def test_should_compile_enabled_but_not_supported(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.6.0',
            'CODIZY_INSTALL': True
        })
        codizy = codizy_extn.CodizyExtension(ctx)
        eq_(False, codizy._should_compile())

    def test_should_compile_service(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.4.33',
            'VCAP_SERVICES': {
                "rediscloud": [{"credentials": {}, "label": "rediscloud"}],
                "codizy": [{"credentials": {}, "label": "codizy"}]
            }
        })
        codizy = codizy_extn.CodizyExtension(ctx)
        eq_(True, codizy._should_compile())

    def test_should_compile_service_but_not_supported(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.6.0',
            'VCAP_SERVICES': {
                "rediscloud": [{"credentials": {}, "label": "rediscloud"}],
                "codizy": [{"credentials": {}, "label": "codizy"}]
            }
        })
        codizy = codizy_extn.CodizyExtension(ctx)
        eq_(False, codizy._should_compile())

    def test_compile(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.4.33',
            'VCAP_SERVICES': {
                "rediscloud": [{"credentials": {}, "label": "rediscloud"}],
                "codizy": [{"credentials": {}, "label": "codizy"}]
            }
        })
        codizy = codizy_extn.CodizyExtension(ctx)
        codizy._setup_codizy = Dingus()
        inst = Dingus()
        codizy.compile(inst)
        eq_(1, len(inst.package.calls()))
        eq_('CODIZY', inst.package.calls()[0].args[0])
        eq_(1, len(codizy._setup_codizy.calls()))

    def test_setup_codizy_no_auto_prepend_file(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.4.33',
            'CODIZY_INSTALL': True
        })
        codizy = codizy_extn.CodizyExtension(ctx)
        codizy.load_config()
        codizy._php_ini._lines = []
        eq_(0, len([line for line in codizy._php_ini._lines
                    if line.startswith('auto_prepend_file')]))
        codizy._setup_codizy()
        eq_(1, len([line for line in codizy._php_ini._lines
                    if line.startswith('auto_prepend_file')]))
        eq_('auto_prepend_file = @{HOME}/codizy/client/application/setup.php',
            codizy._php_ini._lines[0])

    def test_setup_codizy_empty_auto_prepend_file(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.4.33',
            'CODIZY_INSTALL': True
        })
        codizy = codizy_extn.CodizyExtension(ctx)
        codizy.load_config()
        codizy._php_ini._lines = ['auto_prepend_file =']
        eq_(1, len([line for line in codizy._php_ini._lines
                    if line.startswith('auto_prepend_file')]))
        codizy._setup_codizy()
        eq_(1, len([line for line in codizy._php_ini._lines
                    if line.startswith('auto_prepend_file')]))
        eq_('auto_prepend_file = @{HOME}/codizy/client/application/setup.php',
            codizy._php_ini._lines[0])

    def test_setup_codizy_existing_auto_prepend_file(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'PHP_VERSION': '5.4.33',
            'CODIZY_INSTALL': True
        })
        codizy = codizy_extn.CodizyExtension(ctx)
        codizy.load_config()
        codizy._php_ini._lines = ['auto_prepend_file = @{HOME}/php/file.php']
        eq_(1, len([line for line in codizy._php_ini._lines
                    if line.startswith('auto_prepend_file')]))
        codizy._setup_codizy()
        eq_(1, len([line for line in codizy._php_ini._lines
                    if line.startswith('auto_prepend_file')]))
        eq_('auto_prepend_file = @{HOME}/php/auto_prepend_file.php',
            codizy._php_ini._lines[0])
        path = os.path.join(ctx['BUILD_DIR'], 'php', 'auto_prepend_file.php')
        with open(path, 'rt') as fp:
            lines = fp.readlines()
        eq_(4, len(lines))
        eq_('    require("@{HOME}/php/file.php");\n', lines[1])
        eq_('    require("@{HOME}/codizy/client/application/setup.php");\n',
            lines[2])


class BaseCompileCodizy(object):
    def _set_web_server(self, optsFile, webServer):
        options = json.load(open(optsFile))
        options['WEB_SERVER'] = webServer
        options['DOWNLOAD_URL'] = 'http://localhost:5000/binaries/{STACK}'
        options['CODIZY_DOWNLOAD_URL'] = \
            '{DOWNLOAD_URL}/codizy/{CODIZY_VERSION}/{CODIZY_PACKAGE}'
        json.dump(options, open(optsFile, 'wt'))

    def _set_php(self, optsFile, phpVm, phpVersion=None):
        options = json.load(open(optsFile))
        options['PHP_VM'] = phpVm
        if phpVm == 'hhvm':
            options['HHVM_DOWNLOAD_URL'] = \
                '{DOWNLOAD_URL}/hhvm/{HHVM_VERSION}/{HHVM_PACKAGE}'
        if phpVersion:
            options['PHP_VERSION'] = phpVersion
        json.dump(options, open(optsFile, 'wt'))

    def initialize(self, app):
        self.build_dir = tempfile.mkdtemp(prefix='build-')
        self.cache_dir = tempfile.mkdtemp(prefix='cache-')
        os.rmdir(self.build_dir)  # delete otherwise copytree complains
        os.rmdir(self.cache_dir)  # cache dir does not exist normally
        shutil.copytree('tests/data/%s' % app, self.build_dir)

    def copy_build_pack(self, bp_dir):
        # simulate clone, makes debugging easier
        os.rmdir(bp_dir)
        shutil.copytree('.', bp_dir,
                        ignore=shutil.ignore_patterns("binaries",
                                                      "env",
                                                      "tests"))
        binPath = os.path.join(bp_dir, 'binaries', 'lucid')
        os.makedirs(binPath)
        shutil.copy('binaries/lucid/index-all.json', binPath)
        shutil.copy('binaries/lucid/index-latest.json', binPath)

    def cleanup(self):
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


class TestCompileCodizyWithPHP(BaseCompileCodizy):
    def setUp(self):
        BaseCompileCodizy.initialize(self, 'app-1')

    def tearDown(self):
        BaseCompileCodizy.cleanup(self)

    def test_compile_php_with_codizy(self):
        #os.environ['BP_DEBUG'] = 'True'
        os.environ['CODIZY_INSTALL'] = 'True'
        bp = BuildPack({
            'BUILD_DIR': self.build_dir,
            'CACHE_DIR': self.cache_dir,
        }, '.')
        self.copy_build_pack(bp.bp_dir)
        # set php & web server
        optsFile = os.path.join(bp.bp_dir, 'defaults', 'options.json')
        self._set_php(optsFile, 'php')
        self._set_web_server(optsFile, 'httpd')
        try:
            output = ''
            output = bp._compile()
            outputLines = output.split('\n')
            eq_(28, len([l for l in outputLines
                         if l.startswith('Downloaded')]))
            eq_(2, len([l for l in outputLines if l.startswith('Installing')]))
            eq_(True, outputLines[-1].startswith('Finished:'))
            # Test scripts and config
            self.assert_exists(self.build_dir, 'start.sh')
            with open(os.path.join(self.build_dir, 'start.sh')) as start:
                lines = [line.strip() for line in start.readlines()]
                eq_(5, len(lines))
                eq_('export PYTHONPATH=$HOME/.bp/lib', lines[0])
                eq_('$HOME/.bp/bin/rewrite "$HOME/httpd/conf"', lines[1])
                eq_('$HOME/.bp/bin/rewrite "$HOME/php/etc"', lines[2])
                eq_('$HOME/.bp/bin/rewrite "$HOME/.env"', lines[3])
                eq_('$HOME/.bp/bin/start', lines[4])
            # Check scripts and bp are installed
            self.assert_exists(self.build_dir, '.bp', 'bin', 'rewrite')
            self.assert_exists(self.build_dir, '.bp', 'lib')
            bpu_path = os.path.join(self.build_dir, '.bp', 'lib',
                                    'build_pack_utils')
            eq_(22, len(os.listdir(bpu_path)))
            self.assert_exists(bpu_path, 'utils.py')
            self.assert_exists(bpu_path, 'process.py')
            # Check env and procs files
            self.assert_exists(self.build_dir, '.env')
            self.assert_exists(self.build_dir, '.procs')
            with open(os.path.join(self.build_dir, '.env')) as env:
                lines = [line.strip() for line in env.readlines()]
                eq_(2, len(lines))
                eq_('HTTPD_SERVER_ADMIN=dan@mikusa.com', lines[0])
                eq_('LD_LIBRARY_PATH=@LD_LIBRARY_PATH:@HOME/php/lib',
                    lines[1])
            with open(os.path.join(self.build_dir, '.procs')) as procs:
                lines = [line.strip() for line in procs.readlines()]
                eq_(3, len(lines))
                eq_('httpd: $HOME/httpd/bin/apachectl -f '
                    '"$HOME/httpd/conf/httpd.conf" -k start -DFOREGROUND',
                    lines[0])
                eq_('php-fpm: $HOME/php/sbin/php-fpm -p "$HOME/php/etc" -y '
                    '"$HOME/php/etc/php-fpm.conf" -c "$HOME/php/etc"',
                    lines[1])
                eq_('php-fpm-logs: tail -F $HOME/logs/php-fpm.log',
                    lines[2])

            # Check htdocs and config
            self.assert_exists(self.build_dir, 'htdocs')
            self.assert_exists(self.build_dir, '.bp-config')
            self.assert_exists(self.build_dir, '.bp-config', 'options.json')
            # Test HTTPD
            self.assert_exists(self.build_dir)
            self.assert_exists(self.build_dir, 'httpd')
            self.assert_exists(self.build_dir, 'httpd', 'conf')
            self.assert_exists(self.build_dir, 'httpd', 'conf', 'httpd.conf')
            self.assert_exists(self.build_dir, 'httpd', 'conf', 'extra')
            self.assert_exists(self.build_dir, 'httpd', 'conf',
                               'extra', 'httpd-modules.conf')
            self.assert_exists(self.build_dir, 'httpd', 'conf',
                               'extra', 'httpd-remoteip.conf')
            self.assert_exists(self.build_dir, 'httpd', 'modules',
                               'mod_authz_core.so')
            self.assert_exists(self.build_dir, 'httpd', 'modules',
                               'mod_authz_host.so')
            self.assert_exists(self.build_dir, 'httpd', 'modules',
                               'mod_dir.so')
            self.assert_exists(self.build_dir, 'httpd', 'modules',
                               'mod_env.so')
            self.assert_exists(self.build_dir, 'httpd', 'modules',
                               'mod_log_config.so')
            self.assert_exists(self.build_dir, 'httpd', 'modules',
                               'mod_mime.so')
            self.assert_exists(self.build_dir, 'httpd', 'modules',
                               'mod_mpm_event.so')
            self.assert_exists(self.build_dir, 'httpd', 'modules',
                               'mod_proxy.so')
            self.assert_exists(self.build_dir, 'httpd', 'modules',
                               'mod_proxy_fcgi.so')
            self.assert_exists(self.build_dir, 'httpd', 'modules',
                               'mod_reqtimeout.so')
            self.assert_exists(self.build_dir, 'httpd', 'modules',
                               'mod_unixd.so')
            self.assert_exists(self.build_dir, 'httpd', 'modules',
                               'mod_remoteip.so')
            # Test PHP
            self.assert_exists(self.build_dir, 'php')
            self.assert_exists(self.build_dir, 'php', 'etc')
            self.assert_exists(self.build_dir, 'php', 'etc', 'php-fpm.conf')
            self.assert_exists(self.build_dir, 'php', 'etc', 'php.ini')
            self.assert_exists(self.build_dir, 'php', 'sbin', 'php-fpm')
            self.assert_exists(self.build_dir, 'php', 'bin')
            self.assert_exists(self.build_dir, 'php', 'lib', 'php',
                               'extensions', 'no-debug-non-zts-20100525',
                               'bz2.so')
            self.assert_exists(self.build_dir, 'php', 'lib', 'php',
                               'extensions', 'no-debug-non-zts-20100525',
                               'zlib.so')
            self.assert_exists(self.build_dir, 'php', 'lib', 'php',
                               'extensions', 'no-debug-non-zts-20100525',
                               'curl.so')
            self.assert_exists(self.build_dir, 'php', 'lib', 'php',
                               'extensions', 'no-debug-non-zts-20100525',
                               'mcrypt.so')
            # Test Codizy
            self.assert_exists(self.build_dir, 'codizy')
            self.assert_exists(self.build_dir, 'codizy', 'client',
                               'application', 'setup.php')
            self.assert_exists(self.build_dir, 'codizy', 'client',
                               'application', 'class', 'Codizy_utils.php')
            self.assert_exists(self.build_dir, 'php', 'lib', 'php',
                               'extensions', 'no-debug-non-zts-20100525',
                               'xhprof.so')
            self.assert_exists(self.build_dir, 'php', 'lib', 'php',
                               'extensions', 'no-debug-non-zts-20100525',
                               'ioncube.so')
            self.assert_exists(self.build_dir, 'php', 'lib', 'php',
                               'extensions', 'no-debug-non-zts-20100525',
                               'codizy.so')
            self.assert_exists(self.build_dir, 'php', 'lib', 'php',
                               'extensions', 'no-debug-non-zts-20100525',
                               'curl.so')
            self.assert_exists(self.build_dir, 'php', 'lib', 'php',
                               'extensions', 'no-debug-non-zts-20100525',
                               'gettext.so')
            self.assert_exists(self.build_dir, 'php', 'lib', 'php',
                               'extensions', 'no-debug-non-zts-20100525',
                               'mbstring.so')
            self.assert_exists(self.build_dir, 'php', 'lib', 'php',
                               'extensions', 'no-debug-non-zts-20100525',
                               'openssl.so')
            with open(os.path.join(self.build_dir,
                                   'php', 'etc', 'php.ini'), 'rt') as php_ini:
                lines = php_ini.readlines()
            auto_prepend_line = [line for line in lines
                                 if line.startswith('auto_prepend_file')][0]
            eq_('auto_prepend_file = '
                '@{HOME}/codizy/client/application/setup.php\n',
                auto_prepend_line)
        except Exception, e:
            print str(e)
            if hasattr(e, 'output'):
                print e.output
            if output:
                print output
            raise
        finally:
            if os.path.exists(bp.bp_dir):
                shutil.rmtree(bp.bp_dir)
