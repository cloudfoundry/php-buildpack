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
from extension_helpers import ExtensionHelper


class HHVMExtension(ExtensionHelper):
    def _should_compile(self):
        return True

    def _preprocess_commands(self):
        return (('$HOME/.bp/bin/rewrite', '"$HOME/hhvm/etc"'),
                ('hhvm() {', '$HOME/hhvm/usr/bin/hhvm',
                 '-c "$HOME/hhvm/etc/php.ini" "$@";', '}'))

    def _service_commands(self):
        if is_web_app(self._ctx):
            return {
                'hhvm': (
                    '$HOME/hhvm/usr/bin/hhvm',
                    '--mode server',
                    '-c $HOME/hhvm/etc/server.ini',
                    '-c $HOME/hhvm/etc/php.ini')
            }
        else:
            app = find_stand_alone_app_to_run(self._ctx)
            return {
                'hhvm-app': (
                    '$HOME/hhvm/usr/bin/hhvm',
                    '-c $HOME/hhvm/etc/php.ini',
                    app)
            }

    def _service_environment(self):
        return {
            'LD_LIBRARY_PATH': '$LD_LIBRARY_PATH:$HOME/hhvm/usr/lib/hhvm',
            'PATH': "$PATH:$HOME/hhvm/usr/bin"
        }

    def _compile(self, install):
        print 'Installing HHVM'
        print 'HHVM %s' % (self._ctx['HHVM_VERSION'])
        # install HHVM & config
        (install
            .package('HHVM')
            .config()
                .from_application('.bp-config/hhvm')  # noqa
                .or_from_build_pack('defaults/config/hhvm/{HHVM_VERSION}')
                .to('hhvm/etc')
                .rewrite()
                .done())
        return 0


# Extension Methods
def configure(ctx):
    hhvm = HHVMExtension(ctx)
    return hhvm.configure()


def preprocess_commands(ctx):
    hhvm = HHVMExtension(ctx)
    return hhvm.preprocess_commands()


def service_commands(ctx):
    hhvm = HHVMExtension(ctx)
    return hhvm.service_commands()


def service_environment(ctx):
    hhvm = HHVMExtension(ctx)
    return hhvm.service_environment()


def compile(install):
    hhvm = HHVMExtension(install.builder._ctx)
    return hhvm.compile(install)
