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
"""Geoip Config Extension

Configures geoip & optionally downloads geoip databases
"""
import os
import sys
import shutil
from extension_helpers import PHPExtensionHelper
from build_pack_utils import stream_output
from build_pack_utils import utils


class GeoipConfig(PHPExtensionHelper):
    GEOIP_LOCATION_KEY = 'GEOIP_LOCATION'
    DEFAULT_GEOIP_TRIGGER = 'geoip-service'
    CUSTOM_GEOIP_KEY_NAME = 'GEOIP_SERVICE_NAME'

    def __init__(self, ctx):
        PHPExtensionHelper.__init__(self, ctx)

    def _geoip_key(self):
        key_name = self.DEFAULT_GEOIP_TRIGGER
        if self.CUSTOM_GEOIP_KEY_NAME in self._ctx:
            key_name = self._ctx[self.CUSTOM_GEOIP_KEY_NAME]
        return key_name

    def _should_compile(self):
        return 'geoip' in self._ctx.get('PHP_EXTENSIONS', [])

    def _should_download(self):
        return self.GEOIP_LOCATION_KEY not in self._ctx.keys()

    def _extract_download_info(self):
        vcap_services = self._ctx.get('VCAP_SERVICES', {})
        for provider, services in vcap_services.iteritems():
            for service in services:
                service_name = service.get('name', '')
                if service_name == self._geoip_key():
                    creds = service.get('credentials', {})
                    return (creds.get('username', None),
                            creds.get('license', None),
                            creds.get('products', None))
        return None

    def _build_download_cmd(self):
        geoipdbs = os.path.join(
            self._ctx['BUILD_DIR'], 'php', 'geoipdb', 'dbs')
        download_script = os.path.join(
            self._ctx['BUILD_DIR'],
            'php',
            'geoipdb',
            'bin',
            'download_geoip_db.rb')
        cmd = [download_script, '--output_dir="%s"' % geoipdbs]
        info = self._extract_download_info()
        if info:
            (user, license, products) = info
            if user:
                cmd.append('--user="%s"' % user)
            if license:
                cmd.append('--license="%s"' % license)
            if products and len(products) > 0:
                cmd.append('--products="%s"' % products)
        return ' '.join(cmd)

    def _link_geoip_dat(self):
        current_dir = os.getcwd()
        geoip_dir = os.path.join(
            self._ctx['BUILD_DIR'], 'php', 'geoipdb', 'dbs')

        os.chdir(geoip_dir)
        if os.path.isfile("GeoLiteCountry.dat") and not os.path.isfile("GeoIP.dat"):
            os.symlink("GeoLiteCountry.dat", "GeoIP.dat")
        os.chdir(current_dir)

    def _compile(self, install):
        # modify php.ini to add `geoip.custom_directory`
        self.load_config()
        self._php_ini.append_lines(
            'geoip.custom_directory=@{HOME}/php/geoipdb/dbs')
        self._php_ini.save(self._php_ini_path)
        # download geoip dbs
        geoipdbs = os.path.join(
            self._ctx['BUILD_DIR'], 'php', 'geoipdb', 'dbs')
        utils.safe_makedirs(geoipdbs)
        if self._should_download():
            print 'Downloading Geoip Databases.'
            stream_output(sys.stdout,
                          self._build_download_cmd(),
                          shell=True)
            self._link_geoip_dat()
        else:
            print 'Copying Geoip Databases from App.'
            app_geoipdbs = self._ctx.get(self.GEOIP_LOCATION_KEY, None)
            if app_geoipdbs:
                app_geoipdbs_path = os.path.join(self._ctx['BUILD_DIR'],
                                                 app_geoipdbs)
                if not os.path.exists(app_geoipdbs_path):
                    app_geoipdbs_path = os.path.join(self._ctx['BUILD_DIR'],
                                                     'htdocs',
                                                     app_geoipdbs)
                shutil.rmtree(geoipdbs)
                shutil.move(app_geoipdbs_path, geoipdbs)


GeoipConfig.register(__name__)
