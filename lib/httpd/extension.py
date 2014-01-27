def setup_start_script(ssb):
    (ssb.environment_variable()
            .export()
            .name('HTTPD_SERVER_ADMIN')
            .value('ADMIN_EMAIL')
        .command()
            .run('$HOME/httpd/bin/apachectl')
            .with_argument('-f "$HOME/httpd/conf/httpd.conf"')
            .with_argument('-k start')
            .with_argument('-DFOREGROUND')
            .done())


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
