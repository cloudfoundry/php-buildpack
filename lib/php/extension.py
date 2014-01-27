def setup_start_script(ssb):
    (ssb
        .environment_variable()
            .export()
            .name('LD_LIBRARY_PATH')
            .value('$LD_LIBRARY_PATH:$HOME/php/lib')
        .command()
            .run('$HOME/php/sbin/php-fpm')
            .with_argument('-p "$HOME/php/etc"')
            .with_argument('-y "$HOME/php/etc/php-fpm.conf"')
            .done()
        .command()
            .run('tail')
            .with_argument('-F $HOME/../logs/php-fpm.log')
            .background()
            .done())


def compile(install):
    (install
        .package('PHP')
        .config()
            .from_application('config/php')
            .or_from_build_pack('defaults/config/php/{PHP_VERSION}')
            .to('php/etc')
            .rewrite()
            .done()
        .modules('PHP')
            .find_modules_with_regex('^extension=(.*).so$')
            .include_module('fpm')
            .from_application('php/etc/php.ini')
            .done())
    return 0
