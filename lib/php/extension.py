def preprocess_commands(ctx):
    return ((
        '$HOME/rewrite',
        '"$HOME/php/etc"'),)


def service_commands(ctx):
    return {
        'php-fpm': (
            '$HOME/php/sbin/php-fpm',
            '-p "$HOME/php/etc"',
            '-y "$HOME/php/etc/php-fpm.conf"'),
        'php-fpm-logs': (
            'tail',
            '-F $HOME/../logs/php-fpm.log')
    }


def service_environment(ctx):
    return {
        'LD_LIBRARY_PATH': '$LD_LIBRARY_PATH:$HOME/php/lib'
    }


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
