def preprocess_commands(ctx):
    return ((
        '$HOME/.bp/bin/rewrite',
        '"$HOME/httpd/conf"'),)


def service_commands(ctx):
    return {
        'httpd': (
            '$HOME/httpd/bin/apachectl',
            '-f "$HOME/httpd/conf/httpd.conf"',
            '-k start',
            '-DFOREGROUND')
    }


def service_environment(ctx):
    return {
        'HTTPD_SERVER_ADMIN': ctx['ADMIN_EMAIL']
    }


def compile(install):
    install.builder._ctx['PHP_FPM_LISTEN'] = '127.0.0.1:9000'
    (install
        .package('HTTPD')
        .config()
            .from_application('config/httpd')
            .or_from_build_pack('defaults/config/httpd/{HTTPD_VERSION}')
            .to('httpd/conf')
            .rewrite()
            .done()
        .modules('HTTPD')
            .filter_files_by_extension('.conf')
            .find_modules_with_regex('^LoadModule .* modules/(.*).so$')
            .from_application('httpd/conf')
            .done())
    return 0
