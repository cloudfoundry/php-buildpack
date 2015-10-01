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

import os
import os.path
import logging
    
_log = logging.getLogger('varnish')

DEFAULTS = {
    'VARNISH_HOST': 'raw.githubusercontent.com',
    'VARNISH_VERSION': '3.0.6',
    'VARNISH_PACKAGE': 'varnish-{VARNISH_VERSION}.tar.gz',
    'VARNISH_DOWNLOAD_URL': 'https://raw.githubusercontent.com/chregu/cf-varnish-buildpack/master/vendor/varnish-{VARNISH_VERSION}.tar.gz',
}


class VarnishInstaller(object):

    def __init__(self, ctx):
        self._log = _log
        self._ctx = ctx
        self._merge_defaults()


    def _merge_defaults(self):
        for key, val in DEFAULTS.iteritems():
            if key not in self._ctx:
                self._ctx[key] = val
                
    def should_install(self):
        return self._ctx['CACHE_SERVER'] == 'varnish'
    
    def install(self):
        _log.info("Installing Varnish METHOD")
        self._builder.install()._installer._install_binary_from_manifest(
                self._ctx['VARNISH_DOWNLOAD_URL'],
                os.path.join('app'),
                extract=True)

        

def preprocess_commands(ctx):
    return ((
        '$HOME/.bp/bin/rewrite',
        '"$HOME/varnish/etc/varnish"'),)


def service_commands(ctx):
    return {
            'varnish': (
                '$HOME/varnish/sbin/varnishd',
                '-n $TMPDIR/varnish/',
                '-F',
                '-f $HOME/varnish/etc/varnish/default.vcl',
                '-a 0.0.0.0:$VCAP_APP_PORT',
                '-t 120',
                '-w 50,1000,120',
                '-s malloc,128M',
                '-T 127.0.0.1:6082',
                '-p http_resp_hdr_len=32768'
                '2>&1'
                )
        }

def service_environment(ctx):
    env = {
            'LD_LIBRARY_PATH': '$LD_LIBRARY_PATH:$HOME/varnish/lib/varnish',
    }
    return env


def compile(install):
    varnish = VarnishInstaller(install.builder._ctx)
    if varnish.should_install():
        _log.info("Installing Varnish")
        (install
            .package('VARNISH')
            .config()
                .from_application('.bp-config/varnish')  # noqa
                .or_from_build_pack('defaults/config/varnish/{VARNISH_VERSION}')
                .to('varnish/etc/varnish')
                .rewrite()
                .done())
        _log.info("Varnish Installed.")
    return 0
