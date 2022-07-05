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
Downloads and configures Dynatrace OneAgent.
"""

from __future__ import print_function

import json
import logging
import os
import re
import time
from subprocess import call

import urllib2

_log = logging.getLogger('dynatrace')


class DynatraceInstaller(object):
    def __init__(self, ctx):
        self._log = _log
        self._ctx = ctx
        self._detected = False
        self._run_installer = True
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
            self._ctx['DYNATRACE_NETWORK_ZONE'] = detected_services[0].get('networkzone', None)

            self._convert_api_url()
            self._detected = True

        elif len(detected_services) > 1:
            self._log.warning("More than one matching service found!")
            raise SystemExit(1)

    # returns oneagent installer path
    def _get_oneagent_installer_path(self):
        return os.path.join(self._ctx['BUILD_DIR'], 'dynatrace', 'paasInstaller.sh')

    def should_install(self):
        return self._detected

    # create folder if not existing
    def create_folder(self, directory):
        if not os.path.exists(directory):
            os.makedirs(directory)

    def get_buildpack_version(self):
        with open(os.path.join(self._ctx['BP_DIR'], "VERSION")) as version_file:
            return version_file.read()

    def _retry_download(self, url, dest):
        tries = 3
        base_waittime = 3

        for attempt in range(tries):
            try:
                request = urllib2.Request(url)
                request.add_header("user-agent", "cf-php-buildpack/" + self.get_buildpack_version())
                request.add_header("Authorization", "Api-Token {token}".format(token=self._ctx['DYNATRACE_TOKEN']))
                result = urllib2.urlopen(request)
                f = open(dest, 'w')
                f.write(result.read())
                f.close()
                return
            # TODO change to 'err' if this is correct
            except IOError as exc:
                last_exception = exc
                waittime = base_waittime + 2 ** attempt
                _log.warning("Error during installer download, retrying in %s seconds" % waittime)
                time.sleep(waittime)

        raise last_exception

    # downloading the oneagent from the 'DYNATRACE_API_URL'
    def download_oneagent_installer(self):
        self.create_folder(os.path.join(self._ctx['BUILD_DIR'], 'dynatrace'))
        installer = self._get_oneagent_installer_path()
        url = self._ctx['DYNATRACE_API_URL'] + '/v1/deployment/installer/agent/unix/paas-sh/latest?bitness=64&include=php&include=nginx&include=apache'
        if self._ctx['DYNATRACE_NETWORK_ZONE']:
            self._log.info("Setting DT_NETWORK_ZONE...")
            url = url + ("&networkZone=%s" % self._ctx['DYNATRACE_NETWORK_ZONE'])
        skiperrors = self._ctx['DYNATRACE_SKIPERRORS']

        try:
            self._retry_download(url, installer)
            os.chmod(installer, 0o777)
        except IOError as exc:
            if skiperrors == 'true':
                _log.warning('Error during installer download, skipping installation: %s' % exc)
                self._run_installer = False
            else:
                _log.error('ERROR: Dynatrace agent download failed')
                raise

    def run_installer(self):
        return self._run_installer

    # executing the downloaded oneagent installer
    def extract_oneagent(self):
        installer = self._get_oneagent_installer_path()
        call([installer, self._ctx['BUILD_DIR']])

    # removing the oneagent installer
    def cleanup_oneagent_installer(self):
        installer = self._get_oneagent_installer_path()
        os.remove(installer)

    # copying the exisiting dynatrace-env.sh file
    def adding_environment_variables(self):
        source = os.path.join(self._ctx['BUILD_DIR'], 'dynatrace', 'oneagent', 'dynatrace-env.sh')
        dest = os.path.join(self._ctx['BUILD_DIR'], '.profile.d', 'dynatrace-env.sh')
        dest_folder = os.path.join(self._ctx['BUILD_DIR'], '.profile.d')
        self.create_folder(dest_folder)
        os.rename(source, dest)

    # adding LD_PRELOAD to the exisiting dynatrace-env.sh file
    def adding_ld_preload_settings(self):
        envfile = os.path.join(self._ctx['BUILD_DIR'], '.profile.d', 'dynatrace-env.sh')
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

        extra_env = '\nexport LD_PRELOAD="{}"'.format(agent_path)
        extra_env += '\nexport DT_LOGSTREAM=${DT_LOGSTREAM:-stdout}'

        network_zone = self._ctx.get('DYNATRACE_NETWORK_ZONE')
        if network_zone:
            extra_env += '\nexport DT_NETWORK_ZONE="${{DT_NETWORK_ZONE:-{}}}"'.format(network_zone)

        with open(envfile, "a") as file:
            file.write(extra_env)

    # downloading the most recent OneAgent config from the configured tenants API,
    # and merging it with the static config the standalone installer package brought along
    def update_agent_config(self):

        skiperrors = self._ctx['DYNATRACE_SKIPERRORS']
        agent_config_url = self._ctx['DYNATRACE_API_URL'] + '/v1/deployment/installer/agent/processmoduleconfig'

        try:
            # fetch most recent OneAgent config from tenant API
            request = urllib2.Request(agent_config_url)
            request.add_header("user-agent", "cf-php-buildpack/" + self.get_buildpack_version())
            request.add_header("Authorization", "Api-Token {token}".format(token=self._ctx['DYNATRACE_TOKEN']))
            result = urllib2.urlopen(request)
        except IOError as err:
            if skiperrors == 'true':
                _log.warning('Error during agent config update, skipping it: %s' % err)
                return
            else:
                _log.warning('ERROR: Failed to download most recent OneAgent config from API: %s ' % err)
                raise
        _log.debug("Successfully fetched OneAgent config from API")

        # store fetched config in a nested dictionary for easy merging with
        # the data from ruxitagentproc.conf
        json_data = json.load(result)
        config_from_api = dict()
        for elem in json_data['properties']:
            # Storing these values in individual variables might be a bit
            # redundant, but it improves readability below.
            # Also explicitly adding the braces for the sections we get via the
            # the API, to have them formatted in the same ways as the ones from
            # the ruxitagentproc.conf file
            section = "[" + elem['section'] + "]"
            key = elem['key']
            value = elem['value']

            # checking if the required dict is already there.
            # if not: initialize it
            if section not in config_from_api:
                config_from_api[section] = dict()

            config_from_api[section][key] = value

        # read static config from standalone installer
        try:
            agent_config_path = os.path.join(
                self._ctx['BUILD_DIR'],
                'dynatrace',
                'oneagent',
                'agent',
                'conf',
                'ruxitagentproc.conf')
            agent_config_file = open(agent_config_path, 'r')
            agent_config_data = agent_config_file.readlines()
            agent_config_file.close()
        except IOError as err:
            _log.error("ERROR: Failed to read OneAgent config file: %s" % err)
            raise

        _log.debug("Successfully read OneAgent config from " + agent_config_path)

        # store static config in same kind of data structure (nested dictionary)
        # as we use for the config from we fetched from the API
        section_regex = re.compile('\[(.*)\]')
        config_section = ""
        config_from_agent = dict()
        _log.debug("Starting to parse OneAgent config...")
        for line in agent_config_data:
            line = line.rstrip()

            if section_regex.match(line):
                config_section = line
                continue

            if line.startswith('#'):
                # skipping over lines that are purely comments
                continue
            elif line == "":
                # skipping over empty lines
                continue

            # store data in dict

            # checking if the required dict is already there.
            # if not: initialize it
            if config_section not in config_from_agent:
                config_from_agent[config_section] = dict()

            config_line_key = line.split()[0]
            rest_of_the_line = line.split()[1:]
            # the join-construct is needed to convert the list, we get back from the slicing,
            # into a proper string again.
            # Otherwise, we'd need to do the conversion whe writing the data back to the
            # config file, which would be more cumbersome.
            config_line_value = ' '.join(rest_of_the_line)
            config_from_agent[config_section][config_line_key] = config_line_value
        _log.debug("Successfully parsed OneAgent config...")

        # Merging the two configs by just writing the contents we got from
        # the API over the data we got from the local config file.
        # This replaces existing values and adds new ones.
        _log.debug("Starting with OneAgent configuration merging")
        for section_name, section_content in config_from_api.items():
            for key in section_content:
                # checking if the required dict is already there.
                # if not: initialize it
                if section_name not in config_from_agent:
                    config_from_agent[section_name] = dict()
                config_from_agent[section_name][key] = config_from_api[section_name][key]
        _log.debug("Finished OneAgent configuration merging")

        # Write updated config back to ruxitagentproc.conf file
        try:
            overwrite_agent_config_file = open(agent_config_path, 'w')
            for section_name, section_content in config_from_agent.items():
                overwrite_agent_config_file.write(section_name + "\n")
                for key in section_content:
                    write_line = key + " " + section_content[key] + "\n"
                    overwrite_agent_config_file.write(write_line)
                # Trailing empty newline at the end of each section for better human readability
                overwrite_agent_config_file.write("\n")
            overwrite_agent_config_file.close()
        except IOError as err:
            _log.error("ERROR: Failed to write updated config to OneAgent config file: %s" % err)
            raise

        _log.debug("Finished writing updated OneAgent config back to " + agent_config_path)


# Extension Methods
def compile(install):
    dynatrace = DynatraceInstaller(install.builder._ctx)
    if dynatrace.should_install():
        _log.info("Downloading Dynatrace OneAgent Installer")
        dynatrace.download_oneagent_installer()
        if dynatrace.run_installer():
            _log.info("Extracting Dynatrace OneAgent")
            dynatrace.extract_oneagent()
            _log.info("Removing Dynatrace OneAgent Installer")
            dynatrace.cleanup_oneagent_installer()
            _log.info("Adding Dynatrace specific Environment Vars")
            dynatrace.adding_environment_variables()
            _log.info("Adding Dynatrace LD_PRELOAD settings")
            dynatrace.adding_ld_preload_settings()
            _log.info("Fetching updated OneAgent configuration from tenant...")
            dynatrace.update_agent_config()
    return 0
