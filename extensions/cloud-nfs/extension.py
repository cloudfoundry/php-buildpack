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

_log = logging.getLogger('cloud-nfs')

class CloudNFSInstaller(object):
    def __init__(self, ctx):
        log("CloudNFSInstaller inititializing")
        self._log = _log
        self._ctx = ctx
        self._detected = False
        self._load_service_info()
        
    def _load_service_info(self):
        services = self._ctx.get('VCAP_SERVICES', {})
        services = services.get('cloud-nfs', [])
        if len(services) == 0:
            log("cloud-nfs services not detected")
        if len(services) > 0:
            log("cloud-nfs services found...")
            for i in services:
                service = services[i]
                creds = service.get('credentials', {})
                log("service " + i + " credentials: " + creds)
                #self.license_key = creds.get('licenseKey', None)
                #self.app_name = service.get('name', None)
                #if self.license_key and self.app_name:
                #    self._log.debug("NewRelic service detected.")
                #    self._detected = True
            self._detected = True
        
    def should_configure(self):
        return self._detected
    
    def build_mount_commands(self):
        log("preparing mount commands...")
        return()

def log(msg):
    print 'cloud-nfs:: ' + msg

# Extension Methods
def preprocess_commands(ctx):
    log("preprocess_commands method")
    
    nfs = CloudNFSInstaller(ctx)
    if nfs.should_configure():
        log("Preparing service commands to create mounts")
        return nfs.build_mount_commands()
    
    return ()

def service_commands(ctx):
    return {}


def service_environment(ctx):
    return {}


def compile(install):
    return 0
