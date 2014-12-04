import shutil
import os.path
from nose.tools import eq_
from build_pack_utils import BuildPack
from common.integration import OptionsHelper
from common.integration import DirectoryHelper
from common.integration import FileAssertHelper
from common.integration import ErrorHelper
from common.integration import TextFileAssertHelper


class TestCompile(object):
    def setUp(self):
        self.dh = DirectoryHelper()
        (self.build_dir,
         self.cache_dir,
         self.temp_dir) = self.dh.create_bp_env('app-1')
        self.bp = BuildPack({
            'BUILD_DIR': self.build_dir,
            'CACHE_DIR': self.cache_dir,
            'TMPDIR': self.temp_dir
        }, '.')
        self.dh.copy_build_pack_to(self.bp.bp_dir)
        self.dh.register_to_delete(self.bp.bp_dir)
        self.opts = OptionsHelper(os.path.join(self.bp.bp_dir,
                                               'defaults',
                                               'options.json'))
        self.opts.set_download_url(
            'http://localhost:5000/binaries/{STACK}')

    def tearDown(self):
        self.dh.cleanup()

    def test_setup(self):
        fah = FileAssertHelper()
        (fah.expect()
            .path(self.build_dir)
            .path(self.build_dir, 'htdocs')
            .path(self.temp_dir)
            .exists())
        fah.expect().path(self.cache_dir).does_not_exist()

    def test_compile_httpd(self):
        fah = FileAssertHelper()
        tfah = TextFileAssertHelper()
        # set web server to httpd, since that's what we're expecting here
        self.opts.set_web_server('httpd')
        # run the compile step of the build pack
        output = ErrorHelper().compile(self.bp)
        # Test stdout, confirm what is downloaded & installed
        (tfah.expect()
            .on_string(output)
            .line_count_equals(21, lambda l: l.startswith('Downloaded'))
            .line_count_equals(2, lambda l: l.startswith('Installing'))
            .line(-1)
                .startswith('Finished:'))  # noqa
        # Test that the start script was created properly
        fah.expect().path(self.build_dir, 'start.sh').exists()
        (tfah.expect()
            .on_file(self.build_dir, 'start.sh')
            .line_count_equals(5)
            .line(0)
                .equals('export PYTHONPATH=$HOME/.bp/lib\n')  # noqa
            .any_line()
                .equals('$HOME/.bp/bin/rewrite "$HOME/httpd/conf"\n')
                .equals('$HOME/.bp/bin/rewrite "$HOME/php/etc"\n')
                .equals('$HOME/.bp/bin/rewrite "$HOME/.env"\n')
            .line(-1)
                .equals('$HOME/.bp/bin/start'))
        # Check scripts and bp are installed
        (fah.expect()
            .path(self.build_dir, '.bp', 'bin', 'rewrite')
            .root(self.build_dir, '.bp', 'lib', 'build_pack_utils')
                .directory_count_equals(22)  # noqa
                .path('utils.py')
                .path('process.py')
            .exists())
        # Check env file
        fah.expect().path(self.build_dir, '.env').exists()
        (tfah.expect()
            .on_file(self.build_dir, '.env')
            .line_count_equals(3)
            .any_line()
                .equals('PATH=@PATH:@HOME/php/bin\n')  # noqa
                .equals('HTTPD_SERVER_ADMIN=dan@mikusa.com\n')
                .equals('LD_LIBRARY_PATH=@LD_LIBRARY_PATH:@HOME/php/lib\n'))
        # Check procs files
        fah.expect().path(self.build_dir, '.procs').exists()
        (tfah.expect()
            .on_file(self.build_dir, '.procs')
            .line_count_equals(3)
            .any_line()
                .equals('httpd: $HOME/httpd/bin/apachectl -f '  # noqa
                        '"$HOME/httpd/conf/httpd.conf" -k start '
                        '-DFOREGROUND\n')
                .equals('php-fpm: $HOME/php/sbin/php-fpm -p '
                        '"$HOME/php/etc" -y "$HOME/php/etc/php-fpm.conf"'
                        ' -c "$HOME/php/etc"\n')
                .equals('php-fpm-logs: tail -F $HOME/logs/php-fpm.log\n'))
        # Check htdocs and config
        (fah.expect()
            .root(self.build_dir)
                .path('htdocs')  # noqa
                .path('.bp-config', 'options.json')
            .exists())
        # Test HTTPD
        (fah.expect()
            .root(self.build_dir, 'httpd', 'conf')
                .path('httpd.conf')  # noqa
                .root('extra')
                    .path('httpd-modules.conf')  # noqa
                    .path('httpd-remoteip.conf')
            .root(self.build_dir, 'httpd', 'modules', reset=True)
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
        # Test PHP
        (fah.expect()
            .root(self.build_dir, 'php')
                .path('etc', 'php-fpm.conf')  # noqa
                .path('etc', 'php.ini')
                .path('sbin', 'php-fpm')
                .path('bin')
            .root(self.build_dir, 'php', 'lib', 'php', 'extensions',
                  'no-debug-non-zts-20100525')
                .path('bz2.so')
                .path('zlib.so')
                .path('curl.so')
                .path('mcrypt.so')
            .exists())
