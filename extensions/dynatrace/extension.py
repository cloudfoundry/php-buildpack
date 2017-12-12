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
"""
Downloads and configures Dynatrace OneAgent for Paas.
"""

from __future__ import print_function
import os
import logging
from subprocess import call
import urllib2
import json
import time

_log = logging.getLogger('dynatrace')

class DynatraceInstaller(object):
    def __init__(self, ctx):
        self._log = _log
        self._ctx = ctx
        self._detected = False
        self._run_installer = True
        self.app_name = None
        self.dynatrace_server = None
        try:
            self._log.info("Initializing")
            if ctx['PHP_VM'] == 'php':
                self._log.info("Loading service info")
                self._load_service_info()
        except Exception:
            self._log.exception("Error installing Dynatrace OneAgent! "
                                "Dynatrace OneAgent will not be available.")

    # set 'DYNATRACE_API_URL' if not available
    def _convert_api_url(self):
        if self._ctx['DYNATRACE_API_URL'] == None:
            self._ctx['DYNATRACE_API_URL'] = 'https://' + self._ctx['DYNATRACE_ENVIRONMENT_ID'] + '.live.dynatrace.com/api'

    # verify if 'dynatrace' service is available
    def _load_service_info(self):
        detected_services = []
        vcap_services = self._ctx.get('VCAP_SERVICES', {})
        for provider, services in vcap_services.iteritems():
            for service in services:
                if 'dynatrace' in service.get('name', ''):
                    creds = service.get('credentials', {})
                    if creds.get('environmentid', None) and creds.get('apitoken', None):
                        detected_services.append(creds)
                    else:
                        self._log.info("Dynatrace service detected. But without proper credentials!")

        if len(detected_services) == 1:
            self._log.info("Found one matching Dynatrace service")

            self._ctx['DYNATRACE_API_URL'] = detected_services[0].get('apiurl', None)
            self._ctx['DYNATRACE_ENVIRONMENT_ID'] = detected_services[0].get('environmentid', None)
            self._ctx['DYNATRACE_TOKEN'] = detected_services[0].get('apitoken', None)
            self._ctx['DYNATRACE_SKIPERRORS'] = detected_services[0].get('skiperrors', None)

            self._convert_api_url()
            self._detected = True

        elif len(detected_services) > 1:
            self._log.warning("More than one matching service found!")
            raise SystemExit(1)

    # returns paas-installer path
    def _get_paas_installer_path(self):
        return os.path.join(self._ctx['BUILD_DIR'], 'dynatrace', 'paasInstaller.sh')

    def should_install(self):
        return self._detected

    # create folder if not existing
    def create_folder(self, directory):
        if not os.path.exists(directory):
            os.makedirs(directory)

    def _retry_download(self, url, dest):
        tries = 3
        base_waittime = 3

        for attempt in range(tries):
            try:
                result = urllib2.urlopen(url)
                f = open(dest, 'w')
                f.write(result.read())
                f.close()
                return
            except IOError, exc:
                last_exception = exc
                waittime = base_waittime + 2**attempt
                _log.warn("Error during installer download, retrying in %s seconds" % (waittime))
                time.sleep(waittime)

        raise last_exception

    # downloading the paas agent from the 'DYNATRACE_API_URL'
    def download_paas_agent_installer(self):
        self.create_folder(os.path.join(self._ctx['BUILD_DIR'], 'dynatrace'))
        installer = self._get_paas_installer_path()
        url = self._ctx['DYNATRACE_API_URL'] + '/v1/deployment/installer/agent/unix/paas-sh/latest?Api-Token=' + self._ctx['DYNATRACE_TOKEN'] + '&bitness=64&include=php&include=nginx&include=apache'
        skiperrors = self._ctx['DYNATRACE_SKIPERRORS']

        try:
            self._retry_download(url, installer)
            os.chmod(installer, 0o777)
        except IOError, exc:
            if skiperrors == 'true':
                _log.warn('Error during installer download, skipping installation: %s' % (exc))
                self._run_installer = False
            else:
                _log.error('ERROR: Dynatrace agent download failed')
                raise


    def run_installer(self):
        return self._run_installer
    # executing the downloaded paas-installer
    def extract_paas_agent(self):
        installer = self._get_paas_installer_path()
        call([installer, self._ctx['BUILD_DIR']])

    # removing the paas-installer
    def cleanup_paas_installer(self):
        installer = self._get_paas_installer_path()
        os.remove(installer)

    # copying the exisiting dynatrace-env.sh file
    def adding_environment_variables(self):
        source      = os.path.join(self._ctx['BUILD_DIR'], 'dynatrace', 'oneagent', 'dynatrace-env.sh')
        dest        = os.path.join(self._ctx['BUILD_DIR'], '.profile.d', 'dynatrace-env.sh')
        dest_folder = os.path.join(self._ctx['BUILD_DIR'], '.profile.d')
        self.create_folder(dest_folder)
        os.rename(source, dest)

    # adding LD_PRELOAD to the exisiting dynatrace-env.sh file
    def adding_ld_preload_settings(self):
        vcap_app = self._ctx.get('VCAP_APPLICATION', {})
        app_name = vcap_app.get('name', None)
        envfile    = os.path.join(self._ctx['BUILD_DIR'], '.profile.d', 'dynatrace-env.sh')
        agent_path = None
        manifest_file = os.path.join(self._ctx['BUILD_DIR'], 'dynatrace', 'oneagent', 'manifest.json')

        if os.path.isfile(manifest_file):
            manifest = json.load(open(manifest_file))
            process_technology = manifest['technologies'].get('process')
            if process_technology:
                for entry in process_technology['linux-x86-64']:
                    if entry.get('binarytype') == 'primary':
                        _log.info("Using manifest.json")
                        agent_path = entry['path']

        if not agent_path:
            _log.warning("Agent path not found in manifest.json, using fallback")
            agent_path = os.path.join('agent', 'lib64', 'liboneagentproc.so')

        # prepending agent path with installer directory
        agent_path = os.path.join(self._ctx['HOME'], 'app', 'dynatrace', 'oneagent', agent_path)

        ld_preload = '\nexport LD_PRELOAD="' + agent_path + '"'
        host_name  = '\nexport DT_HOST_ID=' + app_name + '_${CF_INSTANCE_INDEX}'
        with open(envfile, "a") as file:
            file.write(ld_preload + host_name)

# Extension Methods
def compile(install):
    dynatrace = DynatraceInstaller(install.builder._ctx)
    if dynatrace.should_install():
        _log.info("Downloading Dynatrace PAAS-Agent Installer")
        dynatrace.download_paas_agent_installer()
        if dynatrace.run_installer():
            _log.info("Extracting Dynatrace PAAS-Agent")
            dynatrace.extract_paas_agent()
            _log.info("Removing Dynatrace PAAS-Agent Installer")
            dynatrace.cleanup_paas_installer()
            _log.info("Adding Dynatrace specific Environment Vars")
            dynatrace.adding_environment_variables()
            _log.info("Adding Dynatrace LD_PRELOAD settings")
            dynatrace.adding_ld_preload_settings()
    return 0
