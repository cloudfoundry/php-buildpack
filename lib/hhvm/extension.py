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
from compile_helpers import is_web_app
from compile_helpers import find_stand_alone_app_to_run


def preprocess_commands(ctx):
    return (('$HOME/.bp/bin/rewrite', '"$HOME/.env"'),
            ('$HOME/.bp/bin/rewrite', '"$HOME/hhvm/etc"'))


def service_commands(ctx):
    if is_web_app(ctx):
        return {
            'hhvm': (
                '$HOME/hhvm/hhvm',
                '--mode server',
                '-c $HOME/hhvm/etc/config.hdf')
        }
    else:
        app = find_stand_alone_app_to_run(ctx)
        return {
            'hhvm-app': (
                '$HOME/hhvm/hhvm',
                app)
        }


def service_environment(ctx):
    return {
        'LD_LIBRARY_PATH': '@LD_LIBRARY_PATH:@HOME/hhvm'
    }


def compile(install):
    print 'Installing HHVM'
    ctx = install.builder._ctx
    # pick how to connect, tcp or unix socket
    if ctx['WEB_SERVER'] == 'httpd':
        ctx['HHVM_LISTEN_TYPE'] = 'Port'
        ctx['PHP_FPM_LISTEN'] = ctx['PHP_FPM_LISTEN'].split(':')[-1]
    elif ctx['WEB_SERVER'] == 'nginx':
        ctx['HHVM_LISTEN_TYPE'] = 'FileSocket'
    # install HHVM & config
    (install
        .package('HHVM')
        .config()
            .from_application('.bp-config/hhvm')
            .or_from_build_pack('defaults/config/hhvm/{HHVM_VERSION}')
            .to('hhvm/etc')
            .rewrite()
            .done())
    return 0
