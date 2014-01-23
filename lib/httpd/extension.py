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
    (install
        .package('HTTPD')
        .config()
            .from_application('config/httpd')
            .or_from_build_pack('defaults/config/httpd/{HTTPD_VERSION}')
            .to('httpd/conf')
            .done()
        .modules('HTTPD')
            .filter_files_by_extension('.conf')
            .find_modules_with_regex('^LoadModule .* modules/(.*).so$')
            .from_application('httpd/conf')
            .done())
    return 0
