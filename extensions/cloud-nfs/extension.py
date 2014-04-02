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
"""Cloud-NFS Extension

Prepares PHP buildpack to leverage NFS storage mount via user-provided-service(s)
"""
import os
import os.path
import logging
import subprocess
import sys
from subprocess import STDOUT, check_call

_log = logging.getLogger('cloud-nfs')

class CloudNFSInstaller(object):
    def __init__(self, ctx):
        log("CloudNFSInstaller initializing")
        self._log = _log
        self._ctx = ctx
        self._detected = False
        self._nfs_services = {}
        self._load_service_info()
        
    def _load_service_info(self):
        services = self._ctx.get('VCAP_SERVICES', {})
        services = services.get('user-provided', [])
        
        for item in services:
            name = item.get('name', {})
            if name.find('cloud-nfs') >= 0:
                self._nfs_services[name] = item
                log("Found cloud-nfs service [" + name + "]")
                self._detected = True
                
        if len(self._nfs_services) == 0:
            log("cloud-nfs services not detected")
            
        
    def should_configure(self):
        return self._detected
    
    def build_mount_commands(self):
        log("preparing mount commands...")
        #TODO - parse service information
#   157  sudo mount 10.0.0.59:/var/nfs /var/nfs
#   159  sudo mount 10.0.0.59:/var/nfs /var/nfs
#   160  sudo mount -t nfs4 10.0.0.59:/var/nfs /var/nfs
#   163  sudo mount -t nfs4 10.0.0.59:/var/nfs /var/nfs
           # return (('$HOME/.bp/bin/rewrite', '"$HOME/.env"'),
            #('$HOME/.bp/bin/rewrite', '"$HOME/hhvm/etc"'))
        return (('"mount"', '"10.0.0.59:/var/nfs"', '"/var/nfs'""))

def log(msg):
    print 'cloud-nfs:: ' + msg

# Extension Methods
def preprocess_commands(ctx):
    log("preprocess_commands method")
    
    nfs = ctx['nfs']
    if nfs.should_configure():
        log("Preparing service commands to create mounts")
        return nfs.build_mount_commands()
    
    return ()

def service_commands(ctx):
    return {}


def service_environment(ctx):
    return {}


def compile(install):
    log("compile step")
    nfs = CloudNFSInstaller(install.builder._ctx)
    install.builder._ctx['nfs'] = nfs
    if nfs.should_configure():
        log('Installing NFS libs')
        proc = subprocess.Popen('apt-get install -y nfs-common rpcbin', shell=True, stdin=None, stdout=subprocess.PIPE, stderr=STDOUT, executable="/bin/bash")
        # Poll process for new output until finished
        while True:
            nextline = proc.stdout.readline()
            if nextline == '' and proc.poll() != None:
                break
            sys.stdout.write(nextline)
            sys.stdout.flush()

        proc.wait()
        exit_code = proc.returncode
        if exit_code != 0:
            log("NFS Lib install failed :: exit code: " + str(exit_code))
            #return exit_code
    return 0
