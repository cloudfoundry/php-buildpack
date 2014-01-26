import os


def setup_start_script(ssb):
    (ssb.environment_variable()
            .export()
            .name('PHP_FPM_LISTEN')
            .value('{TMPDIR}php-fpm.socket')
        .command()
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


def rewrite_nginx_conf(conf_path, ctx):
    for file_name in os.listdir(conf_path):
        cfg_path = os.path.join(conf_path, file_name)
        lines = open(cfg_path).readlines()
        with open(cfg_path, 'wt') as out:
            for line in lines:
                out.write(line.format(**ctx))
