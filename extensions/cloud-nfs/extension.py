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

Prepares PHP buildpack to leverage NFS storage mount
"""
import os
import os.path
import logging


_log = logging.getLogger('cloud-nfs')

class CloudNFSInstaller(object):
    def __init__(self, ctx):
        _log.info("CloudNFSInstaller init")
        self._log = _log
        self._ctx = ctx
        self._detected = False

# Extension Methods
def preprocess_commands(ctx):
    _log.info("preprocess_commands method")
    return ()


def service_commands(ctx):
    _log.info("service_commands method")
    return {}


def service_environment(ctx):
    _log.info("service_environment method")
    return {}


def compile(install):
    _log.info("compile method")
    return 0
