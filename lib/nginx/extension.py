def preprocess_commands(ctx):
    return ((
        '$HOME/rewrite',
        '"$HOME/nginx/conf"'),)


def service_commands(ctx):
    return {
        'nginx': (
            '$HOME/nginx/sbin/nginx',
            '-c "$HOME/nginx/conf/nginx.conf"')
    }


def service_environment(ctx):
    return {}
       

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
