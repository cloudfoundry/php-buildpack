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
import os
import os.path

_log = logging.getLogger('varnish')

DEFAULTS = {
    'VARNISH_VERSION': '3.0.2',
    'VARNISH_PACKAGE': 'varnish-{VARNISH_VERSION}.tar.gz',
    'VARNISH_DOWNLOAD_URL': '{DOWNLOAD_URL}/varnish/' '{VARNISH_VERSION}/{VARNISH_PACKAGE}',
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
        # Check if there is a default.vcl file in the .bp-config/varnish directory
        bpConfig = os.path.join(self._ctx['BUILD_DIR'], '.bp-config/varnish')
        if os.path.exists(os.path.join(bpConfig, 'default.vcl')):
            log("default.vcl file detected... enabling Varnish Cache")
            return True
        else:
            log("default.vcl file not detected...")
            return False        

def preprocess_commands(ctx):
    log("preprocess_commands method")
    return ( )


def service_commands(ctx):
    log("service_commands method")
    varnish = VarnishInstaller(ctx)
    if varnish.should_install():
        service_tup = (
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
            '-s malloc,$VARNISH_MEMORY_LIMIT',
            '-F'
        )
        log("service command for varnish: " + str(service_tup))
        return {
                'varnishd': ( service_tup )
                }
    else:
        return { }

def service_environment(ctx):
    log("service_environment method")
    env_dict = {}
    
    varnish = VarnishInstaller(ctx)
    if varnish.should_install():
        env_dict['LD_LIBRARY_PATH'] = '@LD_LIBRARY_PATH:@HOME/varnish/lib:@HOME/php/lib'
        varnish_mem = ctx.get('VARNISH_MEMORY_LIMIT', None)
        if varnish_mem is None:
            log("VARNISH_MEMORY_LIMIT variable not detected.  Using application MEMORY_LIMIT")
            varnish_mem = ctx.get('MEMORY_LIMIT', None)
            env_dict['VARNISH_MEMORY_LIMIT'] = varnish_mem
        else:
            log("VARNISH_MEMORY_LIMIT variable detected")
    log("service environment for varnish: " + str(env_dict))
    return env_dict

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
