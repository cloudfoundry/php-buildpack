import shutil
import tempfile
import os.path
import json
from nose.tools import eq_
from build_pack_utils import BuildPack


class BaseTestCompile(object):
    def set_web_server(self, optsFile, webServer):
        options = json.load(open(optsFile))
        options['WEB_SERVER'] = webServer
        options['DOWNLOAD_URL'] = 'http://localhost:5000/binaries/{STACK}'
        options['NEWRELIC_DOWNLOAD_URL'] = \
            '{DOWNLOAD_URL}/newrelic/{NEWRELIC_VERSION}/{NEWRELIC_PACKAGE}'
        json.dump(options, open(optsFile, 'wt'))

    def set_php_version(self, optsFile, version):
        options = json.load(open(optsFile))
        options['PHP_VERSION'] = version
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
            if name.startswith('nginx-') and name.endswith('.gz'):
                os.remove(os.path.join(os.environ['TMPDIR'], name))
            if name.startswith('php-') and name.endswith('.gz'):
                os.remove(os.path.join(os.environ['TMPDIR'], name))

    def assert_exists(self, *args):
        eq_(True, os.path.exists(os.path.join(*args)),
            "Does not exists: %s" % os.path.join(*args))


class TestCompile(BaseTestCompile):
    def setUp(self):
        BaseTestCompile.initialize(self, 'app-1')

    def tearDown(self):
        BaseTestCompile.cleanup(self)

    def test_setup(self):
        eq_(True, os.path.exists(self.build_dir))
        eq_(False, os.path.exists(self.cache_dir))
        eq_(True, os.path.exists(os.path.join(self.build_dir, 'htdocs')))

    def test_compile_httpd(self):
        bp = BuildPack({
            'BUILD_DIR': self.build_dir,
            'CACHE_DIR': self.cache_dir
        }, '.')
        self.copy_build_pack(bp.bp_dir)
        # set web server
        self.set_web_server(os.path.join(bp.bp_dir,
                                         'defaults',
                                         'options.json'),
                            'httpd')
        try:
            output = ''
            output = bp._compile()
            outputLines = output.split('\n')
            eq_(21, len([l for l in outputLines
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
            self.assert_exists(self.build_dir, 'httpd', 'modules',
                               'mod_rewrite.so')
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

    def test_compile_nginx(self):
        bp = BuildPack({
            'BUILD_DIR': self.build_dir,
            'CACHE_DIR': self.cache_dir
        }, '.')
        self.copy_build_pack(bp.bp_dir)
        # set web server
        self.set_web_server(os.path.join(bp.bp_dir,
                                         'defaults',
                                         'options.json'),
                            'nginx')
        try:
            output = ''
            output = bp._compile()
            # Test Output
            outputLines = output.split('\n')
            eq_(7, len([l for l in outputLines if l.startswith('Downloaded')]))
            eq_(2, len([l for l in outputLines if l.startswith('Installing')]))
            eq_(True, outputLines[-1].startswith('Finished:'))
            # Test scripts and config
            self.assert_exists(self.build_dir, 'start.sh')
            with open(os.path.join(self.build_dir, 'start.sh')) as start:
                lines = [line.strip() for line in start.readlines()]
                eq_(5, len(lines))
                eq_('export PYTHONPATH=$HOME/.bp/lib', lines[0])
                eq_('$HOME/.bp/bin/rewrite "$HOME/nginx/conf"', lines[1])
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
                eq_(1, len(lines))
                eq_('LD_LIBRARY_PATH=@LD_LIBRARY_PATH:@HOME/php/lib',
                    lines[0])
            with open(os.path.join(self.build_dir, '.procs')) as procs:
                lines = [line.strip() for line in procs.readlines()]
                eq_(3, len(lines))
                eq_('nginx: $HOME/nginx/sbin/nginx -c '
                    '"$HOME/nginx/conf/nginx.conf"', lines[0])
                eq_('php-fpm: $HOME/php/sbin/php-fpm -p "$HOME/php/etc" -y '
                    '"$HOME/php/etc/php-fpm.conf" -c "$HOME/php/etc"',
                    lines[1])
                eq_('php-fpm-logs: tail -F $HOME/logs/php-fpm.log',
                    lines[2])
            # Test htdocs & config
            self.assert_exists(self.build_dir, 'htdocs')
            self.assert_exists(self.build_dir, '.bp-config')
            self.assert_exists(self.build_dir, '.bp-config', 'options.json')
            # Test NGINX
            self.assert_exists(self.build_dir)
            self.assert_exists(self.build_dir, 'nginx')
            self.assert_exists(self.build_dir, 'nginx', 'conf')
            self.assert_exists(self.build_dir, 'nginx', 'conf',
                               'fastcgi_params')
            self.assert_exists(self.build_dir, 'nginx', 'conf',
                               'http-logging.conf')
            self.assert_exists(self.build_dir, 'nginx', 'conf',
                               'http-defaults.conf')
            self.assert_exists(self.build_dir, 'nginx', 'conf',
                               'http-php.conf')
            self.assert_exists(self.build_dir, 'nginx', 'conf',
                               'mime.types')
            self.assert_exists(self.build_dir, 'nginx', 'conf',
                               'nginx-defaults.conf')
            self.assert_exists(self.build_dir, 'nginx', 'conf',
                               'nginx-workers.conf')
            self.assert_exists(self.build_dir, 'nginx', 'conf',
                               'nginx.conf')
            self.assert_exists(self.build_dir, 'nginx', 'conf',
                               'server-defaults.conf')
            self.assert_exists(self.build_dir, 'nginx', 'conf',
                               'server-locations.conf')
            self.assert_exists(self.build_dir, 'nginx', 'logs')
            self.assert_exists(self.build_dir, 'nginx', 'sbin')
            self.assert_exists(self.build_dir, 'nginx', 'sbin', 'nginx')
            with open(os.path.join(self.build_dir,
                                   'nginx',
                                   'conf',
                                   'http-php.conf')) as fin:
                data = fin.read()
                eq_(-1, data.find('#{PHP_FPM_LISTEN}'))
                eq_(-1, data.find('{TMPDIR}'))
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


class TestCompileCustomDirs(BaseTestCompile):
    def setUp(self):
        BaseTestCompile.initialize(self, 'app-6')

    def tearDown(self):
        BaseTestCompile.cleanup(self)

    def test_compile_httpd_custom_webdir(self):
        bp = BuildPack({
            'BUILD_DIR': self.build_dir,
            'CACHE_DIR': self.cache_dir
        }, '.')
        self.copy_build_pack(bp.bp_dir)
        # set web server
        self.set_web_server(os.path.join(bp.bp_dir,
                                         'defaults',
                                         'options.json'),
                            'httpd')
        try:
            output = ''
            output = bp._compile()
            outputLines = output.split('\n')
            eq_(21, len([l for l in outputLines
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
            # Check public and config
            self.assert_exists(self.build_dir, 'public')
            self.assert_exists(self.build_dir, 'public', 'index.php')
            self.assert_exists(self.build_dir, 'public', 'info.php')
            self.assert_exists(self.build_dir, 'public',
                               'technical-difficulties1.jpg')
            self.assert_exists(self.build_dir, 'vendor')
            self.assert_exists(self.build_dir, 'vendor', 'lib.php')
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
            self.assert_exists(self.build_dir, 'httpd', 'modules',
                               'mod_rewrite.so')
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


class TestCompileStandAlone(BaseTestCompile):

    def setUp(self):
        BaseTestCompile.initialize(self, 'app-5')

    def tearDown(self):
        BaseTestCompile.cleanup(self)

    def test_compile_stand_alone(self):
        bp = BuildPack({
            'BUILD_DIR': self.build_dir,
            'CACHE_DIR': self.cache_dir
        }, '.')
        self.copy_build_pack(bp.bp_dir)
        # set web server & php version
        optsFile = os.path.join(bp.bp_dir, 'defaults', 'options.json')
        self.set_web_server(optsFile, 'none')
        self.set_php_version(optsFile, '5.4.31')
        try:
            output = ''
            output = bp._compile()
            # Test Output
            outputLines = output.split('\n')
            eq_(6, len([l for l in outputLines if l.startswith('Downloaded')]))
            eq_(1, len([l for l in outputLines if l.startswith('No Web')]))
            eq_(1, len([l for l in outputLines
                        if l.startswith('Installing PHP')]))
            eq_(1, len([l for l in outputLines if l.find('php-cli') >= 0]))
            eq_(True, outputLines[-1].startswith('Finished:'))
            # Test scripts and config
            self.assert_exists(self.build_dir, 'start.sh')
            with open(os.path.join(self.build_dir, 'start.sh')) as start:
                lines = [line.strip() for line in start.readlines()]
                eq_(4, len(lines))
                eq_('export PYTHONPATH=$HOME/.bp/lib', lines[0])
                eq_('$HOME/.bp/bin/rewrite "$HOME/php/etc"', lines[1])
                eq_('$HOME/.bp/bin/rewrite "$HOME/.env"', lines[2])
                eq_('$HOME/.bp/bin/start', lines[3])
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
                eq_(1, len(lines))
                eq_('LD_LIBRARY_PATH=@LD_LIBRARY_PATH:@HOME/php/lib',
                    lines[0])
            with open(os.path.join(self.build_dir, '.procs')) as procs:
                lines = [line.strip() for line in procs.readlines()]
                eq_(1, len(lines))
                eq_('php-app: $HOME/php/bin/php -c "$HOME/php/etc" '
                    'app.php', lines[0])
            # Test PHP
            self.assert_exists(self.build_dir, 'php')
            self.assert_exists(self.build_dir, 'php', 'etc')
            self.assert_exists(self.build_dir, 'php', 'etc', 'php.ini')
            self.assert_exists(self.build_dir, 'php', 'bin')
            self.assert_exists(self.build_dir, 'php', 'bin', 'php')
            self.assert_exists(self.build_dir, 'php', 'bin', 'phar.phar')
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
