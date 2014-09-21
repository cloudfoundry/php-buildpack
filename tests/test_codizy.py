import os
import os.path
import tempfile
import shutil
import json
from nose.tools import eq_
from nose.tools import with_setup
from build_pack_utils import utils
from build_pack_utils import BuildPack


codizy = utils.load_extension('extensions/codizy')


class TestCodizy(object):
    def setUp(self):
        self.build_dir = tempfile.mkdtemp('build-')
        self.php_dir = os.path.join(self.build_dir, 'php', 'etc')
        os.makedirs(self.php_dir)
        shutil.copy('defaults/config/php/5.4.x/php.ini', self.php_dir)

    def tearDown(self):
        if os.path.exists(self.build_dir):
            shutil.rmtree(self.build_dir)

    def testDefaults(self):
        cy = codizy.CodizyInstaller(utils.FormattedDict({
            'BUILD_DIR': self.build_dir
        }))
        eq_(True, 'CODIZY_VERSION' in cy._ctx.keys())
        eq_(True, 'CODIZY_PACKAGE' in cy._ctx.keys())
        eq_(True, 'CODIZY_DOWNLOAD_URL' in cy._ctx.keys())
        eq_(True, 'CODIZY_STRIP' in cy._ctx.keys())

    def testShouldNotInstall(self):
        cy = codizy.CodizyInstaller(utils.FormattedDict({
            'BUILD_DIR': self.build_dir
        }))
        eq_(False, cy.should_install())

    @with_setup(setup=setUp, teardown=tearDown)
    def testShouldInstall(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'VCAP_APPLICATION': {
                'name': 'app-name-1'
            },
            'CODIZY_INSTALL': '1'
        })
        cy = codizy.CodizyInstaller(ctx)
        eq_(True, cy.should_install())
        eq_('x64', cy._php_arch)
        eq_('@{HOME}/php/lib/php/extensions/no-debug-non-zts-20100525',
            cy._php_extn_dir)
        eq_(False, cy._php_zts)
        eq_('20100525', cy._php_api)
        eq_('@{HOME}/codizy/codizy-20100525.so', cy.codizy_so)

    @with_setup(setup=setUp, teardown=tearDown)
    def testShouldInstallService(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'VCAP_SERVICES': {
                'codizy': [{
                    'name': 'codizy',
                    'label': 'codizy',
                    'tags': ['Monitoring', 'Performance', 'Optimizations'],
                    'plan': 'full',
                    'credentials': {'user': 'username', 'password' : 'password'}}]
            },
            'VCAP_APPLICATION': {
                'name': 'app-name-1'
            }
        })
        cy = codizy.CodizyInstaller(ctx)
        eq_(True, cy.should_install())
        eq_('x64', cy._php_arch)
        eq_('@{HOME}/php/lib/php/extensions/no-debug-non-zts-20100525',
            cy._php_extn_dir)
        eq_(False, cy._php_zts)
        eq_('20100525', cy._php_api)
        eq_('@{HOME}/codizy/codizy-20100525.so', cy.codizy_so)

    @with_setup(setup=setUp, teardown=tearDown)
    def testShouldInstallServiceAndManual(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'VCAP_SERVICES': {
                'codizy': [{
                    'name': 'codizy',
                    'label': 'codizy',
                    'tags': ['Monitoring', 'Performance', 'Optimizations'],
                    'plan': 'full',
                    'credentials': {'user': 'username', 'password' : 'password'}}]
            },
            'CODIZY_INSTALL': '1',
            'VCAP_APPLICATION': {
                'name': 'app-name-2'
            }
        })
        cy = codizy.CodizyInstaller(ctx)
        eq_(True, cy.should_install())
        eq_('x64', cy._php_arch)
        eq_('@{HOME}/php/lib/php/extensions/no-debug-non-zts-20100525',
            cy._php_extn_dir)
        eq_(False, cy._php_zts)
        eq_('20100525', cy._php_api)
        eq_('@{HOME}/codizy/codizy-20100525.so', cy.codizy_so)

    @with_setup(setup=setUp, teardown=tearDown)
    def testModifyPhpIni(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'CODIZY_INSTALL': '1',
            'VCAP_APPLICATION': {
                'name': 'app-name-1'
            }
        })
        cy = codizy.CodizyInstaller(ctx)
        cy.modify_php_ini()
        with open(os.path.join(self.php_dir, 'php.ini'), 'rt') as php_ini:
            lines = php_ini.readlines()
        eq_(True, lines.index('extension=%s\n' % cy.codizy_so) >= 0)


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

    def test_compile_httpd_with_codizy(self):
        os.environ['CODIZY_INSTALL'] = '1'
        os.environ['VCAP_APPLICATION'] = json.dumps({
            'name': 'app-name-1'
        })
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
            eq_(22, len([l for l in outputLines
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
            self.assert_exists(self.build_dir, 'codizy', 'codizy-20100525.so')
            with open(os.path.join(self.build_dir,
                                   'php', 'etc', 'php.ini'), 'rt') as php_ini:
                lines = php_ini.readlines()
            extn_path = '@{HOME}/codizy/codizy-20100525.so'
            eq_(True, lines.index('extension=%s\n' % extn_path) >= 0)
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


class TestCompileCodizyWithHHVM(BaseCompileCodizy):
    def setUp(self):
        BaseCompileCodizy.initialize(self, 'app-1')

    def tearDown(self):
        BaseCompileCodizy.cleanup(self)

    def test_compile_httpd_with_codizy(self):
        os.environ['CODIZY_INSTALL'] = '1'
        os.environ['VCAP_APPLICATION'] = json.dumps({
            'name': 'app-name-1'
        })
        bp = BuildPack({
            'BUILD_DIR': self.build_dir,
            'CACHE_DIR': self.cache_dir,
        }, '.')
        self.copy_build_pack(bp.bp_dir)
        # set php & web server
        optsFile = os.path.join(bp.bp_dir, 'defaults', 'options.json')
        self._set_php(optsFile, 'hhvm')
        self._set_web_server(optsFile, 'httpd')

        try:
            output = ''
            output = bp._compile()
            outputLines = output.split('\n')
            eq_(16, len([l for l in outputLines
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
                eq_('$HOME/.bp/bin/rewrite "$HOME/.env"', lines[2])
                eq_('$HOME/.bp/bin/rewrite "$HOME/hhvm/etc"', lines[3])
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
                eq_('LD_LIBRARY_PATH=@LD_LIBRARY_PATH:@HOME/hhvm',
                    lines[1])
            with open(os.path.join(self.build_dir, '.procs')) as procs:
                lines = [line.strip() for line in procs.readlines()]
                eq_(2, len(lines))
                eq_('httpd: $HOME/httpd/bin/apachectl -f '
                    '"$HOME/httpd/conf/httpd.conf" -k start -DFOREGROUND',
                    lines[0])
                eq_('hhvm: $HOME/hhvm/hhvm --mode server -c '
                    '$HOME/hhvm/etc/config.hdf', lines[1])

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
            self.assert_exists(self.build_dir, 'hhvm')
            self.assert_exists(self.build_dir, 'hhvm', 'hhvm')
            self.assert_exists(self.build_dir, 'hhvm', 'etc', 'config.hdf')
            self.assert_exists(self.build_dir, 'hhvm', 'libmemcached.so.11')
            self.assert_exists(self.build_dir, 'hhvm', 'libevent-1.4.so.2.2.0')
            self.assert_exists(self.build_dir, 'hhvm', 'libevent-1.4.so.2')
            self.assert_exists(self.build_dir, 'hhvm',
                               'libboost_system.so.1.55.0')
            self.assert_exists(self.build_dir, 'hhvm',
                               'libc-client.so.2007e.0')
            self.assert_exists(self.build_dir, 'hhvm', 'libstdc++.so.6')
            self.assert_exists(self.build_dir, 'hhvm', 'libMagickWand.so.2')
            self.assert_exists(self.build_dir, 'hhvm', 'libicui18n.so.48')
            # Test Codizy (should not be installed with HHVM)
            eq_(False,
                os.path.exists(os.path.join(self.build_dir, 'codizy')))
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
