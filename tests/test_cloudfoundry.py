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
                'TMPDIR': tempfile.mkdtemp(),
                'BP_DIR': '',
                'TESTING_DOWNLOAD_URL': 'http://mock.com',
            })
            instance.install_binary('TESTING')
        except RuntimeError as e:
            exception = e

        eq_("Could not download dependency: http://mock.com", str(exception))
