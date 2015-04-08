from nose.tools import eq_
from build_pack_utils import cloudfoundry
import tempfile

class TestCloudFoundryInstaller(object):

    def test_missing_dependency_from_manifest_raises_error(self):
        exception = None

        try:
            instance = cloudfoundry.CloudFoundryInstaller({
                'CACHE_DIR': tempfile.mkdtemp(),
                'BUILD_DIR': 'tests/data/composer',
                'BP_DIR': '',
                'TESTING_DOWNLOAD_URL': ''
            })
            instance.install_binary('TESTING')
        except RuntimeError as e:
            exception = e

        eq_("Could not get translated url, exited with: DEPENDENCY_MISSING_IN_MANIFEST:", str(exception))
