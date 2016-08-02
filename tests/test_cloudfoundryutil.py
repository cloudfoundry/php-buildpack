from nose.tools import eq_
from build_pack_utils.cloudfoundry import CloudFoundryUtil
from build_pack_utils import utils
import tempfile
import shutil
import os

def buildpack_directory():
    directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    return os.path.abspath(directory)

def create_manifest_file(manifest_filename, contents):
    file = open(manifest_filename,'w+')
    file.write(contents)
    file.close()


class TestCloudFoundryUtil(object):
    def setUp(self):
        self.buildpack_dir = buildpack_directory()
        self.manifest_dir  = tempfile.mkdtemp()
        self.manifest_file = os.path.join(tempfile.mkdtemp(), 'manifest.yml')

    def tearDown(self):
        shutil.rmtree(self.manifest_dir)


    def test_default_versions_are_updated(self):
        input_dict = utils.FormattedDict()
        input_dict['BP_DIR'] = buildpack_directory()
        create_manifest_file(self.manifest_file, GOOD_MANIFEST)

        output_dict = CloudFoundryUtil.update_default_version('php', self.manifest_file, input_dict)

        # keys exist
        eq_('PHP_VERSION' in output_dict, True)
        eq_('PHP_DOWNLOAD_URL' in output_dict, True)
        eq_('PHP_MODULES_PATTERN' in output_dict, True)

        # have correct value
        eq_(output_dict['PHP_VERSION'], '9.9.99')

        # output_dict['PHP_VERSION'] + output_dict['MODULE_NAME'] are interpolated into the strings returned
        # from the dict, so:
        output_dict['MODULE_NAME'] = 'test_default_versions'
        eq_(output_dict['PHP_MODULES_PATTERN'], '/php/9.9.99/php-test_default_versions-9.9.99.tar.gz')
        eq_(output_dict['PHP_DOWNLOAD_URL'], '/php/9.9.99/php-9.9.99.tar.gz')

    def test_default_version_is_not_in_manifest(self):
        exception = None

        input_dict = utils.FormattedDict()
        input_dict['BP_DIR'] = buildpack_directory()
        create_manifest_file(self.manifest_file, BAD_MANIFEST)

        try:
            CloudFoundryUtil.update_default_version('php', self.manifest_file, input_dict)
        except RuntimeError as e:
            exception = e

        eq_("Error detecting PHP default version", str(exception))

BAD_MANIFEST = '''\
---
language: php

default_versions:
- name: php
  version: 9.9.777

dependencies:
- name: php
  version: 5.5.37
  uri: https://buildpacks.cloudfoundry.org/concourse-binaries/php/php-5.5.37-linux-x64-1469764899.tgz
  md5: 783f12b1d394815819631aa92e88c196
- name: php
  version: 5.6.23
  uri: https://buildpacks.cloudfoundry.org/concourse-binaries/php/php-5.6.23-linux-x64-1469767807.tgz
  md5: 9ffbd67e557f4569de8d876664a6bd33
- name: php
  version: 5.6.24
  uri: https://buildpacks.cloudfoundry.org/concourse-binaries/php/php-5.6.24-linux-x64-1469768750.tgz
  md5: 35b5e1ccce1f2ca7e55c81b11f278a3f
- name: php
  version: 7.0.8
  uri: https://buildpacks.cloudfoundry.org/concourse-binaries/php7/php7-7.0.8-linux-x64-1469764417.tgz
  md5: a479fec08ac8400ca9d775a88ddb2962
- name: php
  version: 7.0.9
  uri: https://buildpacks.cloudfoundry.org/concourse-binaries/php7/php7-7.0.9-linux-x64-1469765150.tgz
  cf_stacks:
  - cflinuxfs2
  md5: 19e8318e1cee3fa9fd8fdcc358f01076
'''

GOOD_MANIFEST = '''\
---
language: php

default_versions:
- name: php
  version: 9.9.99

dependencies:
- name: php
  version: 5.5.37
  uri: https://buildpacks.cloudfoundry.org/concourse-binaries/php/php-5.5.37-linux-x64-1469764899.tgz
  md5: 783f12b1d394815819631aa92e88c196
- name: php
  version: 9.9.99
  uri: https://buildpacks.cloudfoundry.org/concourse-binaries/php/php-9.9.99-linux-x64-1469766236.tgz
  md5: f31b1e164e29b0782eae9bd3bb6a288a
- name: php
  version: 5.6.23
  uri: https://buildpacks.cloudfoundry.org/concourse-binaries/php/php-5.6.23-linux-x64-1469767807.tgz
  md5: 9ffbd67e557f4569de8d876664a6bd33
- name: php
  version: 5.6.24
  uri: https://buildpacks.cloudfoundry.org/concourse-binaries/php/php-5.6.24-linux-x64-1469768750.tgz
  md5: 35b5e1ccce1f2ca7e55c81b11f278a3f
- name: php
  version: 7.0.8
  uri: https://buildpacks.cloudfoundry.org/concourse-binaries/php7/php7-7.0.8-linux-x64-1469764417.tgz
  md5: a479fec08ac8400ca9d775a88ddb2962
- name: php
  version: 7.0.9
  uri: https://buildpacks.cloudfoundry.org/concourse-binaries/php7/php7-7.0.9-linux-x64-1469765150.tgz
  cf_stacks:
  - cflinuxfs2
  md5: 19e8318e1cee3fa9fd8fdcc358f01076
'''
