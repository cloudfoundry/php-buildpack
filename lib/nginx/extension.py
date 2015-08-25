# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


def preprocess_commands(ctx):
    return ((
        '$HOME/.bp/bin/rewrite',
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
    print 'Installing Nginx'
    install.builder._ctx['PHP_FPM_LISTEN'] = '{TMPDIR}/php-fpm.socket'
    (install
        .package('NGINX')
        .config()
            .from_application('.bp-config/nginx')  # noqa
            .or_from_build_pack('defaults/config/nginx')
            .to('nginx/conf')
            .rewrite()
            .done())
    return 0
