from common.integration import FileAssertHelper
from common.integration import TextFileAssertHelper


class DownloadAssertHelper(object):
    """Helper to assert download counts"""

    def __init__(self, download, install):
        self.download = download
        self.install = install

    def assert_downloads_from_output(self, output):
        assert output is not None, "Output is None"
        tfah = TextFileAssertHelper()
        (tfah.expect()
            .on_string(output)
            .line_count_equals(self.download,
                               lambda l: l.startswith('Downloaded'))
            .line_count_equals(self.install,
                               lambda l: l.startswith('Installing'))
            .line(-1).startswith('Finished:'))


class BuildPackAssertHelper(object):
    """Helper to assert build pack is working"""

    def assert_start_script_is_correct(self, build_dir):
        fah = FileAssertHelper()
        fah.expect().path(build_dir, '.profile.d/rewrite.sh').exists()
        tfah = TextFileAssertHelper()
        (tfah.expect()
            .on_file(build_dir, '.profile.d/rewrite.sh')
            .line(0)
                .contains('export PYTHONPATH=$HOME/.bp/lib'))  # noqa

    def assert_scripts_are_installed(self, build_dir):
        fah = FileAssertHelper()
        (fah.expect()
            .path(build_dir, '.bp', 'bin', 'rewrite')
            .root(build_dir, '.bp', 'lib', 'build_pack_utils')
                .directory_count_equals(20)  # noqa
                .path('utils.py')
                .path('process.py')
            .exists())

    def assert_config_options(self, build_dir):
        fah = FileAssertHelper()
        (fah.expect()
            .path(build_dir, '.bp-config', 'options.json')
            .exists())


class PhpAssertHelper(object):
    """Helper to assert PHP is installed & configured correctly"""

    def assert_start_script_is_correct(self, build_dir):
        fah = FileAssertHelper()
        fah.expect().path(build_dir, '.profile.d/rewrite.sh').exists()
        tfah = TextFileAssertHelper()
        (tfah.expect()
            .on_file(build_dir, '.profile.d/rewrite.sh')
            .any_line()
            .contains('$HOME/.bp/bin/rewrite "$HOME/php/etc"'))

    def assert_contents_of_procs_file(self, build_dir):
        fah = FileAssertHelper()
        fah.expect().path(build_dir, '.procs').exists()
        tfah = TextFileAssertHelper()
        (tfah.expect()
            .on_file(build_dir, '.procs')
            .any_line()
                .equals('php-fpm: $HOME/php/sbin/php-fpm -p '  # noqa
                        '"$HOME/php/etc" -y "$HOME/php/etc/php-fpm.conf"'
                        ' -c "$HOME/php/etc"\n'))

    def assert_contents_of_env_file(self, build_dir):
        fah = FileAssertHelper()
        fah.expect().path(build_dir, '.profile.d', 'bp_env_vars.sh').exists()
        tfah = TextFileAssertHelper()
        (tfah.expect()
            .on_file(build_dir, '.profile.d', 'bp_env_vars.sh')
            .any_line()
                .equals('export '
                        'PATH=$PATH:$HOME/php/bin:$HOME/php/sbin\n')  # noqa
                .equals('export '
                        'LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$HOME/php/lib\n')
                .equals('export PHPRC=$HOME/php/etc\n'))

    def assert_files_installed(self, build_dir):
        fah = FileAssertHelper()
        (fah.expect()
            .root(build_dir, 'php')
                .path('etc', 'php-fpm.conf')  # noqa
                .path('etc', 'php.ini')
                .path('sbin', 'php-fpm')
                .path('bin')
            .root(build_dir, 'php', 'lib', 'php', 'extensions',
                  'no-debug-non-zts-20121212')  # this timestamp is PHP5.5 specific
                .path('bz2.so')
                .path('zlib.so')
                .path('curl.so')
                .path('mcrypt.so')
            .exists())


class HttpdAssertHelper(object):
    """Helper to assert HTTPD is installed and configured correctly"""

    def assert_start_script_is_correct(self, build_dir):
        fah = FileAssertHelper()
        fah.expect().path(build_dir, '.profile.d/rewrite.sh').exists()
        tfah = TextFileAssertHelper()
        (tfah.expect()
            .on_file(build_dir, '.profile.d/rewrite.sh')
            .any_line()
            .contains('$HOME/.bp/bin/rewrite "$HOME/httpd/conf"'))

    def assert_contents_of_procs_file(self, build_dir):
        fah = FileAssertHelper()
        fah.expect().path(build_dir, '.procs').exists()
        tfah = TextFileAssertHelper()
        (tfah.expect()
            .on_file(build_dir, '.procs')
            .any_line()
                .equals('httpd: $HOME/httpd/bin/apachectl -f '  # noqa
                        '"$HOME/httpd/conf/httpd.conf" -k start '
                        '-DFOREGROUND\n'))

    def assert_contents_of_env_file(self, build_dir):
        fah = FileAssertHelper()
        fah.expect().path(build_dir, '.profile.d', 'bp_env_vars.sh').exists()
        tfah = TextFileAssertHelper()
        (tfah.expect()
            .on_file(build_dir, '.profile.d', 'bp_env_vars.sh')
            .any_line()
            .equals('export HTTPD_SERVER_ADMIN=dan@mikusa.com\n'))

    def assert_web_dir_exists(self, build_dir, web_dir):
        fah = FileAssertHelper()
        (fah.expect()
            .path(build_dir, web_dir)
            .exists())

    def assert_files_installed(self, build_dir):
        fah = FileAssertHelper()
        (fah.expect()
            .root(build_dir, 'httpd', 'conf')
                .path('httpd.conf')  # noqa
                .root('extra')
                    .path('httpd-modules.conf')  # noqa
                    .path('httpd-remoteip.conf')
            .root(build_dir, 'httpd', 'modules', reset=True)
                .path('mod_authz_core.so')
                .path('mod_authz_host.so')
                .path('mod_dir.so')
                .path('mod_env.so')
                .path('mod_log_config.so')
                .path('mod_mime.so')
                .path('mod_mpm_event.so')
                .path('mod_proxy.so')
                .path('mod_proxy_fcgi.so')
                .path('mod_reqtimeout.so')
                .path('mod_unixd.so')
                .path('mod_remoteip.so')
                .path('mod_rewrite.so')
            .exists())


class NginxAssertHelper(object):
    """Helper to assert Nginx is installed and configured correctly"""

    def assert_start_script_is_correct(self, build_dir):
        fah = FileAssertHelper()
        fah.expect().path(build_dir, '.profile.d/rewrite.sh').exists()
        tfah = TextFileAssertHelper()
        (tfah.expect()
            .on_file(build_dir, '.profile.d/rewrite.sh')
            .any_line()
            .contains('$HOME/.bp/bin/rewrite "$HOME/nginx/conf"'))

    def assert_contents_of_procs_file(self, build_dir):
        fah = FileAssertHelper()
        fah.expect().path(build_dir, '.procs').exists()
        tfah = TextFileAssertHelper()
        (tfah.expect()
            .on_file(build_dir, '.procs')
            .any_line()
                .equals('nginx: $HOME/nginx/sbin/nginx -c '  # noqa
                        '"$HOME/nginx/conf/nginx.conf"\n'))

    def assert_web_dir_exists(self, build_dir, web_dir):
        fah = FileAssertHelper()
        (fah.expect()
            .path(build_dir, web_dir)
            .exists())

    def assert_files_installed(self, build_dir):
        fah = FileAssertHelper()
        (fah.expect()
            .root(build_dir, 'nginx')
                .path('logs')  # noqa
                .path('sbin', 'nginx')
            .root(build_dir, 'nginx', 'conf')
                .directory_count_equals(10)
                .path('fastcgi_params')
                .path('http-logging.conf')
                .path('http-defaults.conf')
                .path('http-php.conf')
            .exists())
        tfah = TextFileAssertHelper()
        (tfah.expect()
            .on_file(build_dir, 'nginx', 'conf', 'http-php.conf')
            .any_line()
                .does_not_contain('#{PHP_FPM_LISTEN}')  # noqa
                .does_not_contain('{TMPDIR}'))


class NoWebServerAssertHelper(object):
    """Helper to assert when we're not using a web server"""

    def assert_no_web_server_is_installed(self, build_dir):
        fah = FileAssertHelper()
        (fah.expect()
            .path(build_dir, 'httpd')
            .path(build_dir, 'nginx')
            .does_not_exist())

    def assert_downloads_from_output(self, output):
        tfah = TextFileAssertHelper()
        (tfah.expect()
            .on_string(output)
            .line_count_equals(1, lambda l: l.startswith('Downloaded'))
            .line_count_equals(1, lambda l: l.startswith('No Web'))
            .line_count_equals(1, lambda l: l.startswith('Installing PHP'))
            .line_count_equals(0, lambda l: l.find('php-cli') >= 0)
            .line(-1).startswith('Finished:'))

    def assert_contents_of_procs_file(self, build_dir):
        fah = FileAssertHelper()
        fah.expect().path(build_dir, '.procs').exists()
        tfah = TextFileAssertHelper()
        (tfah.expect()
            .on_file(build_dir, '.procs')
            .line(0)
            .equals('php-app: $HOME/php/bin/php -c "$HOME/php/etc" app.php\n'))

    def assert_files_installed(self, build_dir):
        fah = FileAssertHelper()
        (fah.expect()
            .root(build_dir, 'php')
                .path('etc', 'php.ini')  # noqa
                .path('bin', 'php')
                .path('bin', 'phar.phar')
            .root(build_dir, 'php', 'lib', 'php', 'extensions',
                  'no-debug-non-zts-20121212') # this timestamp is PHP5.5.x specific
                .path('bz2.so')
                .path('zlib.so')
                .path('curl.so')
                .path('mcrypt.so')
            .exists())

    def assert_no_web_dir(self, build_dir, webdir):
        fah = FileAssertHelper()
        (fah.expect()
            .path(build_dir, webdir)
            .does_not_exist())


class NewRelicAssertHelper(object):
    """Helper to assert NewRelic is installed and configured correctly"""

    def assert_files_installed(self, build_dir):
        fah = FileAssertHelper()
        (fah.expect()
            .root(build_dir, 'newrelic')  # noqa
                .path('daemon', 'newrelic-daemon.x64')
                .path('agent', 'x64', 'newrelic-20121212.so')
            .exists())
        tfah = TextFileAssertHelper()
        (tfah.expect()
            .on_file(build_dir, 'php', 'etc', 'php.ini')
            .any_line()
            .equals(
                'extension=@{HOME}/newrelic/agent/x64/newrelic-20121212.so\n')
            .equals('[newrelic]\n')
            .equals('newrelic.license=JUNK_LICENSE\n')
            .equals('newrelic.appname=app-name-1\n'))

    def is_not_installed(self, build_dir):
        fah = FileAssertHelper()
        (fah.expect()
            .path(build_dir, 'newrelic')
            .does_not_exist())

