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
import json
import os
import shutil
from dingus import Dingus
from nose.tools import eq_
from build_pack_utils import utils
import tempfile


class TestGeoipConfig(object):

    def __init__(self):
        self.extension_module = utils.load_extension('extensions/geoip')

    def test_should_compile_yes(self):
        geoip = self.extension_module.GeoipConfig({
            'PHP_EXTENSIONS': ['geoip']
        })
        eq_(True, geoip._should_compile())

    def test_should_compile_no(self):
        geoip = self.extension_module.GeoipConfig({
            'PHP_EXTENSIONS': []
        })
        eq_(False, geoip._should_compile())

    def test_should_download_no(self):
        geoip = self.extension_module.GeoipConfig({
            self.extension_module.GeoipConfig.GEOIP_LOCATION_KEY:
                'value doesnt matter'
        })
        eq_(False, geoip._should_download())

    def test_should_download_yes(self):
        geoip = self.extension_module.GeoipConfig({})
        eq_(True, geoip._should_download())

    def test_geoip_key_default(self):
        geoip = self.extension_module.GeoipConfig({})
        eq_(geoip.DEFAULT_GEOIP_TRIGGER, geoip._geoip_key())

    def test_geoip_key_custom(self):
        geoip = self.extension_module.GeoipConfig({
            self.extension_module.GeoipConfig.CUSTOM_GEOIP_KEY_NAME:
                'custom_geoip_service'
        })
        eq_('custom_geoip_service', geoip._geoip_key())

    def test_extract_download_info_no_vcap_services(self):
        geoip = self.extension_module.GeoipConfig({})
        eq_(None, geoip._extract_download_info())

    def test_extract_download_info_no_geoip_service(self):
        ctx = json.load(open('tests/data/geoip/vcap_services_no_geoip.json'))
        geoip = self.extension_module.GeoipConfig(ctx)
        eq_(None, geoip._extract_download_info())

    def test_extract_download_info_geoip_service_present(self):
        ctx = json.load(open('tests/data/geoip/vcap_services_geoip.json'))
        geoip = self.extension_module.GeoipConfig(ctx)
        expected = ('TEST',
                    'asdfghjkl;',
                    'GeoLite-Legacy-IPv6-City GeoLite-Legacy-IPv6-Country')
        actual = geoip._extract_download_info()
        for exp, act in zip(expected, actual):
            eq_(exp, act)

    def test_extract_download_info_just_products(self):
        ctx = json.load(open(
            'tests/data/geoip/vcap_services_geoip_products.json'))
        geoip = self.extension_module.GeoipConfig(ctx)
        expected = (None,
                    None,
                    'GeoLite-Legacy-IPv6-City GeoLite-Legacy-IPv6-Country')
        actual = geoip._extract_download_info()
        for exp, act in zip(expected, actual):
            eq_(exp, act)

    def test_extract_download_info_just_user(self):
        ctx = json.load(open('tests/data/geoip/vcap_services_geoip_user.json'))
        geoip = self.extension_module.GeoipConfig(ctx)
        expected = ('TEST', None, None)
        actual = geoip._extract_download_info()
        for exp, act in zip(expected, actual):
            eq_(exp, act)

    def test_extract_download_info_just_license(self):
        ctx = json.load(open(
            'tests/data/geoip/vcap_services_geoip_license.json'))
        geoip = self.extension_module.GeoipConfig(ctx)
        expected = (None, 'asdfghjkl;', None)
        actual = geoip._extract_download_info()
        for exp, act in zip(expected, actual):
            eq_(exp, act)

    def test_extract_download_info_user_and_license(self):
        ctx = json.load(open(
            'tests/data/geoip/vcap_services_geoip_user_and_license.json'))
        geoip = self.extension_module.GeoipConfig(ctx)
        expected = ('TEST', 'asdfghjkl;', None)
        actual = geoip._extract_download_info()
        for exp, act in zip(expected, actual):
            eq_(exp, act)

    def test_build_download_cmd(self):
        ctx = json.load(open('tests/data/geoip/vcap_services_geoip.json'))
        ctx['BUILD_DIR'] = '/test/build_dir'
        ctx['BP_DIR'] = '/test/bp_dir'
        geoip = self.extension_module.GeoipConfig(ctx)
        cmd = geoip._build_download_cmd()
        eq_('/test/build_dir/php/geoipdb/bin/download_geoip_db.rb '
            '--output_dir="/test/build_dir/php/geoipdb/dbs" '
            '--user="TEST" '
            '--license="asdfghjkl;" '
            '--products='
            '"GeoLite-Legacy-IPv6-City GeoLite-Legacy-IPv6-Country"', cmd)

    def test_build_download_cmd_user_and_license(self):
        ctx = json.load(open(
            'tests/data/geoip/vcap_services_geoip_user_and_license.json'))
        ctx['BUILD_DIR'] = '/test/build_dir'
        ctx['BP_DIR'] = '/test/bp_dir'
        geoip = self.extension_module.GeoipConfig(ctx)
        cmd = geoip._build_download_cmd()
        eq_('/test/build_dir/php/geoipdb/bin/download_geoip_db.rb '
            '--output_dir="/test/build_dir/php/geoipdb/dbs" '
            '--user="TEST" '
            '--license="asdfghjkl;"', cmd)

    def test_build_download_cmd_products(self):
        ctx = json.load(open(
            'tests/data/geoip/vcap_services_geoip_products.json'))
        ctx['BUILD_DIR'] = '/test/build_dir'
        ctx['BP_DIR'] = '/test/bp_dir'
        geoip = self.extension_module.GeoipConfig(ctx)
        cmd = geoip._build_download_cmd()
        eq_('/test/build_dir/php/geoipdb/bin/download_geoip_db.rb '
            '--output_dir="/test/build_dir/php/geoipdb/dbs" '
            '--products='
            '"GeoLite-Legacy-IPv6-City GeoLite-Legacy-IPv6-Country"', cmd)

    def test_link_geoip_dat_geoip_dat_exists(self):
        ctx = {}
        ctx['BUILD_DIR'] = tempfile.mkdtemp()
        geoip_dir = os.path.join(ctx['BUILD_DIR'], 'php', 'geoipdb', 'dbs')
        os.makedirs(geoip_dir)

        with open(os.path.join(geoip_dir, "GeoIP.dat"), 'w') as f:
            f.write('xxx')

        with open(os.path.join(geoip_dir, "GeoLiteCountry.dat"), 'w') as f:
            f.write('yyy')

        geoip = self.extension_module.GeoipConfig(ctx)
        geoip._link_geoip_dat()

        contents = ''
        with open(os.path.join(geoip_dir, "GeoIP.dat"), 'r') as f:
            contents = f.read()

        eq_(contents, 'xxx')

        shutil.rmtree(ctx['BUILD_DIR'])

    def test_link_geoip_dat_geoip_dat_does_not_exist(self):
        ctx = {}
        ctx['BUILD_DIR'] = tempfile.mkdtemp()
        geoip_dir = os.path.join(ctx['BUILD_DIR'], 'php', 'geoipdb', 'dbs')
        os.makedirs(geoip_dir)

        with open(os.path.join(geoip_dir, "GeoLiteCountry.dat"), 'w') as f:
            f.write('yyy')

        geoip = self.extension_module.GeoipConfig(ctx)
        geoip._link_geoip_dat()

        contents = ''
        with open(os.path.join(geoip_dir, "GeoIP.dat"), 'r') as f:
            contents = f.read()

        eq_(contents, 'yyy')

        shutil.rmtree(ctx['BUILD_DIR'])

    def test_link_geoip_dat_geolitecountry_dat_does_not_exist(self):
        ctx = {}
        ctx['BUILD_DIR'] = tempfile.mkdtemp()
        geoip_dir = os.path.join(ctx['BUILD_DIR'], 'php', 'geoipdb', 'dbs')
        os.makedirs(geoip_dir)

        geoip = self.extension_module.GeoipConfig(ctx)
        geoip._link_geoip_dat()

        eq_(os.path.isfile(os.path.join(geoip_dir, "GeoIP.dat")), False)
        eq_(os.path.isfile(os.path.join(geoip_dir, "GeoLiteCountry.dat")), False)

        shutil.rmtree(ctx['BUILD_DIR'])
