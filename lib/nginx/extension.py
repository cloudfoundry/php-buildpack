def setup_start_script(ssb):
    (ssb.command()
        .run('$HOME/nginx/sbin/nginx')
        .with_argument('-c "$HOME/nginx/conf/nginx.conf"')
        .done())
       

def compile(install):
    (install
        .package('NGINX')
        .config()
            .from_application('config/nginx')
            .or_from_build_pack('defaults/config/nginx/{NGINX_VERSION}')
            .to('nginx/conf')
            .done())
    return 0
