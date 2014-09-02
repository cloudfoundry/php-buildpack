import os
import os.path
import tempfile
import shutil
import json
from nose.tools import eq_
from nose.tools import with_setup
from build_pack_utils import utils
from build_pack_utils import BuildPack


newrelic = utils.load_extension('extensions/newrelic')


class TestNewRelic(object):
    def setUp(self):
        self.build_dir = tempfile.mkdtemp('build-')
        self.php_dir = os.path.join(self.build_dir, 'php', 'etc')
        os.makedirs(self.php_dir)
        shutil.copy('defaults/config/php/5.4.x/php.ini', self.php_dir)

    def tearDown(self):
        if os.path.exists(self.build_dir):
            shutil.rmtree(self.build_dir)

    def testDefaults(self):
        nr = newrelic.NewRelicInstaller(utils.FormattedDict({
            'BUILD_DIR': self.build_dir
        }))
        eq_(True, 'NEWRELIC_HOST' in nr._ctx.keys())
        eq_(True, 'NEWRELIC_VERSION' in nr._ctx.keys())
        eq_(True, 'NEWRELIC_PACKAGE' in nr._ctx.keys())
        eq_(True, 'NEWRELIC_DOWNLOAD_URL' in nr._ctx.keys())
        eq_(True, 'NEWRELIC_HASH_DOWNLOAD_URL' in nr._ctx.keys())
        eq_(True, 'NEWRELIC_STRIP' in nr._ctx.keys())

    def testShouldNotInstall(self):
        nr = newrelic.NewRelicInstaller(utils.FormattedDict({
            'BUILD_DIR': self.build_dir
        }))
        eq_(False, nr.should_install())

    @with_setup(setup=setUp, teardown=tearDown)
    def testShouldInstall(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'NEWRELIC_LICENSE': 'JUNK_LICENSE',
            'VCAP_APPLICATION': {
                'name': 'app-name-1'
            }
        })
        nr = newrelic.NewRelicInstaller(ctx)
        eq_(True, nr.should_install())
        eq_('x64', nr._php_arch)
        eq_('@{HOME}/php/lib/php/extensions/no-debug-non-zts-20100525',
            nr._php_extn_dir)
        eq_(False, nr._php_zts)
        eq_('20100525', nr._php_api)
        eq_('@{HOME}/newrelic/agent/x64/newrelic-20100525.so', nr.newrelic_so)
        eq_('app-name-1', nr.app_name)
        eq_('JUNK_LICENSE', nr.license_key)
        eq_('@{HOME}/logs/newrelic-daemon.log', nr.log_path)
        eq_('@{HOME}/newrelic/daemon/newrelic-daemon.x64', nr.daemon_path)
        eq_('@{HOME}/newrelic/daemon.sock', nr.socket_path)
        eq_('@{HOME}/newrelic/daemon.pid', nr.pid_path)

    @with_setup(setup=setUp, teardown=tearDown)
    def testShouldInstallService(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'VCAP_SERVICES': {
                'newrelic': [{
                    'name': 'newrelic',
                    'label': 'newrelic',
                    'tags': ['Monitoring'],
                    'plan': 'standard',
                    'credentials': {'licenseKey': 'LICENSE'}}]
            },
            'VCAP_APPLICATION': {
                'name': 'app-name-1'
            }
        })
        nr = newrelic.NewRelicInstaller(ctx)
        eq_(True, nr.should_install())
        eq_('x64', nr._php_arch)
        eq_('@{HOME}/php/lib/php/extensions/no-debug-non-zts-20100525',
            nr._php_extn_dir)
        eq_(False, nr._php_zts)
        eq_('20100525', nr._php_api)
        eq_('@{HOME}/newrelic/agent/x64/newrelic-20100525.so', nr.newrelic_so)
        eq_('app-name-1', nr.app_name)
        eq_('LICENSE', nr.license_key)
        eq_('@{HOME}/logs/newrelic-daemon.log', nr.log_path)
        eq_('@{HOME}/newrelic/daemon/newrelic-daemon.x64', nr.daemon_path)
        eq_('@{HOME}/newrelic/daemon.sock', nr.socket_path)
        eq_('@{HOME}/newrelic/daemon.pid', nr.pid_path)

    @with_setup(setup=setUp, teardown=tearDown)
    def testShouldInstallServiceAndManual(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'VCAP_SERVICES': {
                'newrelic': [{
                    'name': 'newrelic',
                    'label': 'newrelic',
                    'tags': ['Monitoring'],
                    'plan': 'standard',
                    'credentials': {'licenseKey': 'LICENSE'}}]
            },
            'NEWRELIC_LICENSE': 'LICENSE2',
            'VCAP_APPLICATION': {
                'name': 'app-name-2'
            }
        })
        nr = newrelic.NewRelicInstaller(ctx)
        eq_(True, nr.should_install())
        eq_('x64', nr._php_arch)
        eq_('@{HOME}/php/lib/php/extensions/no-debug-non-zts-20100525',
            nr._php_extn_dir)
        eq_(False, nr._php_zts)
        eq_('20100525', nr._php_api)
        eq_('@{HOME}/newrelic/agent/x64/newrelic-20100525.so', nr.newrelic_so)
        eq_('app-name-2', nr.app_name)
        eq_('LICENSE2', nr.license_key)
        eq_('@{HOME}/logs/newrelic-daemon.log', nr.log_path)
        eq_('@{HOME}/newrelic/daemon/newrelic-daemon.x64', nr.daemon_path)
        eq_('@{HOME}/newrelic/daemon.sock', nr.socket_path)
        eq_('@{HOME}/newrelic/daemon.pid', nr.pid_path)

    @with_setup(setup=setUp, teardown=tearDown)
    def testModifyPhpIni(self):
        ctx = utils.FormattedDict({
            'BUILD_DIR': self.build_dir,
            'NEWRELIC_LICENSE': 'JUNK_LICENSE',
            'VCAP_APPLICATION': {
                'name': 'app-name-1'
            }
        })
        nr = newrelic.NewRelicInstaller(ctx)
        nr.modify_php_ini()
        with open(os.path.join(self.php_dir, 'php.ini'), 'rt') as php_ini:
            lines = php_ini.readlines()
        eq_(True, lines.index('extension=%s\n' % nr.newrelic_so) >= 0)
        eq_(True, lines.index('[newrelic]\n') >= 0)
        eq_(True, lines.index('newrelic.license=JUNK_LICENSE\n') >= 0)
        eq_(True, lines.index('newrelic.appname=%s\n' % nr.app_name) >= 0)


class BaseCompileNewRelic(object):
    def _set_web_server(self, optsFile, webServer):
        options = json.load(open(optsFile))
        options['WEB_SERVER'] = webServer
        options['DOWNLOAD_URL'] = 'http://localhost:5000/binaries/{STACK}'
        options['NEWRELIC_DOWNLOAD_URL'] = \
            '{DOWNLOAD_URL}/newrelic/{NEWRELIC_VERSION}/{NEWRELIC_PACKAGE}'
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


class TestCompileNewRelicWithPHP(BaseCompileNewRelic):
    def setUp(self):
        BaseCompileNewRelic.initialize(self, 'app-1')

    def tearDown(self):
        BaseCompileNewRelic.cleanup(self)

    def test_compile_httpd_with_newrelic(self):
        os.environ['NEWRELIC_LICENSE'] = 'JUNK_LICENSE'
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
            # Test NewRelic
            self.assert_exists(self.build_dir, 'newrelic')
            self.assert_exists(self.build_dir, 'newrelic', 'daemon',
                               'newrelic-daemon.x64')
            self.assert_exists(self.build_dir, 'newrelic', 'agent', 'x64',
                               'newrelic-20100525.so')
            with open(os.path.join(self.build_dir,
                                   'php', 'etc', 'php.ini'), 'rt') as php_ini:
                lines = php_ini.readlines()
            extn_path = '@{HOME}/newrelic/agent/x64/newrelic-20100525.so'
            eq_(True, lines.index('extension=%s\n' % extn_path) >= 0)
            eq_(True, lines.index('[newrelic]\n') >= 0)
            eq_(True, lines.index('newrelic.license=JUNK_LICENSE\n') >= 0)
            eq_(True, lines.index('newrelic.appname=app-name-1\n') >= 0)
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


class TestCompileNewRelicWithHHVM(BaseCompileNewRelic):
    def setUp(self):
        BaseCompileNewRelic.initialize(self, 'app-1')

    def tearDown(self):
        BaseCompileNewRelic.cleanup(self)

    def test_compile_httpd_with_newrelic(self):
        os.environ['NEWRELIC_LICENSE'] = 'JUNK_LICENSE'
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
            # Test NewRelic (should not be installed with HHVM)
            eq_(False,
                os.path.exists(os.path.join(self.build_dir, 'newrelic')))
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
