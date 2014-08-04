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
"""Codizy-Client files install

Downloads, installs and configures the Codizy-client files for PHP
"""
import os
import os.path
import logging


_log = logging.getLogger('codizy-client')


DEFAULTS = {
    "CODIZY_CLIENT_VERSION": "1.1",
    "CODIZY_CLIENT_PACKAGE": "Codizy-codizy.tar.gz",
    "CODIZY_CLIENT_DOWNLOAD_URL": "https://www.codizy.com/download/marketplace-codizy/{CODIZY_PACKAGE}",
    "CODIZY_CLIENT_STRIP": False
}



class CodizyClientInstaller(object):
    def __init__(self, ctx):
        self._log = _log
        self._ctx = ctx
        self.app_name = None
        try:
            self._log.info("Initializing")
            self._merge_defaults()
        except Exception:
            self._log.exception("Error installing Codizy-client files! "
                                "Codizy-client files will not be available.")

    def _merge_defaults(self):
        for key, val in DEFAULTS.iteritems():
            if key not in self._ctx:
                self._ctx[key] = val

# Extension Methods
def preprocess_commands(ctx):
    return ()


def service_commands(ctx):
    return {}


def service_environment(ctx):
    return {}


def compile(install):
    codizyclient = CodizyClientInstaller(install.builder._ctx)
    _log.info("Installing Codizy-client file")
    install.package('CODIZY_CLIENT')
    _log.info("Codizy-client Installed.")
    return 0
