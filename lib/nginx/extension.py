
def setup_start_script(ssb):
    (ssb.command()
            .run('$HOME/rewrite')
            .with_argument('"$HOME/nginx/conf"')
            .done()
        .command()
            .run('$HOME/nginx/sbin/nginx')
            .with_argument('-c "$HOME/nginx/conf/nginx.conf"')
            .done())
       

def compile(install):
    install.builder._ctx['PHP_FPM_LISTEN'] = '{TMPDIR}/php-fpm.socket'
    (install
        .package('NGINX')
        .config()
            .from_application('config/nginx')
            .or_from_build_pack('defaults/config/nginx/{NGINX_VERSION}')
            .to('nginx/conf')
            .rewrite()
            .done())
    return 0
