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
"""Varnish Extension

Downloads, installs and configures Varnish reverse proxy web accelerator
"""
import logging

_log = logging.getLogger('varnish')

DEFAULTS = {
    'VARNISH_VERSION': '3.0.2',
    'VARNISH_PACKAGE': 'varnish-{VARNISH_VERSION}.tar.gz',
    'VARNISH_DOWNLOAD_URL': '{DOWNLOAD_URL}/varnish/' 'archive/{VARNISH_VERSION}/{VARNISH_PACKAGE}',
    'VARNISH_HASH_DOWNLOAD_URL': '{DOWNLOAD_URL}/varnish/{VARNISH_VERSION}/' '{VARNISH_PACKAGE}.{CACHE_HASH_ALGORITHM}'
}

def log(msg):
    #_log.info('varnish:: ' + msg)
    print 'vanish::' + msg
    
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
        return True

def preprocess_commands(ctx):
    log("preprocess_commands method")
    return ( )


def service_commands(ctx):
    log("service_commands method")
    tup = (
            '/sbin/start-stop-daemon',
            '--start',
            '--verbose',
            '--pidfile',
            '"$HOME/varnish/varnishd.pid"',
            '--startas',
            '"$HOME/varnish/bin/varnishd"',
            '--',
            '-P "$HOME/varnish/varnishd.pid"',
            '-n "$HOME/varnish"',
            '-a *:$VCAP_APP_PORT',
            '-T 127.0.0.1:6082',
            '-f "$HOME/varnish/conf/default.vcl"',
            '-s malloc,$MEMORY_LIMIT',
            '-F'
           )
    log("service command for varnish: " + str(tup))
    return {
        'varnishd': ( tup )
    }

def service_environment(ctx):
    log("service_environment method")
    return {
        'LD_LIBRARY_PATH': '@LD_LIBRARY_PATH:@HOME/varnish/lib'
    }

def compile(install): 
    varnish = VarnishInstaller(install.builder._ctx)
    if varnish.should_install():
        log("Installing Varnish...")
        (install
        .package('VARNISH')
        .config()
            .from_application('.bp-config/varnish')
            .to('varnish/conf')
            .rewrite()
            .done())
        log("Varnish Installed.")
    return 0
