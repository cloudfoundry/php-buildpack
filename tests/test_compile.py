import compile
import shutil
import tempfile
import os.path
from nose.tools import eq_
from nose.tools import raises
from nose.tools import with_setup
from build_pack_utils import BuildPack


class TestCompile(object):
    def setUp(self):
        self.build_dir = tempfile.mkdtemp(prefix='build-')
        self.cache_dir = tempfile.mkdtemp(prefix='cache-')
        os.rmdir(self.build_dir) # delete otherwise copytree complains
        os.rmdir(self.cache_dir) # cache dir does not exist normally
        shutil.copytree('tests/data/app-1', self.build_dir)

    def tearDown(self):
        # TODO: make sure all temporary files are cleaned up
        #       Currently not cleaning up downloaded files.  Files are
        #       downloaded to TMPDIR, no record of what is downloaded.
        #       Probably need to override TMPDIR for the test and delete
        #       after the test runs.
        if os.path.exists(self.build_dir):
            shutil.rmtree(self.build_dir)
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)

    @with_setup(setup=setUp, teardown=tearDown)
    def test_setup(self):
        eq_(True, os.path.exists(self.build_dir))
        eq_(False, os.path.exists(self.cache_dir))
        eq_(True, os.path.exists(os.path.join(self.build_dir, 'htdocs')))

    def assert_exists(self, *args):
        eq_(True, os.path.exists(os.path.join(*args)),
            "Does not exists: %s" % os.path.join(*args))

    @with_setup(setup=setUp, teardown=tearDown)
    def test_setup(self):
        bp = BuildPack({
            'BUILD_DIR': self.build_dir,
            'CACHE_DIR': self.cache_dir
        }, '.')
        # simulate clone, makes debugging easier
        os.rmdir(bp.bp_dir)
        shutil.copytree('.', bp.bp_dir,
                        ignore=shutil.ignore_patterns("binaries",
                                                      "env",
                                                      "tests"))
        try:
            bp._compile()
            self.assert_exists(self.build_dir)
            self.assert_exists(self.build_dir, 'httpd')
            self.assert_exists(self.build_dir, 'httpd', 'conf')
            self.assert_exists(self.build_dir, 'httpd', 'conf', 'httpd.conf')
            self.assert_exists(self.build_dir, 'httpd', 'conf', 'extra')
            self.assert_exists(self.build_dir, 'httpd', 'conf',
                          'extra', 'httpd-modules.conf')
            self.assert_exists(self.build_dir, 'start.sh')
            self.assert_exists(self.build_dir, 'htdocs')
            self.assert_exists(self.build_dir, 'config')
            self.assert_exists(self.build_dir, 'config', 'options.json')
        except Exception, e:
            print str(e)
            if hasattr(e, 'output'):
                print e.output
            raise e
        finally:
            if os.path.exists(bp.bp_dir):
                shutil.rmtree(bp.bp_dir)
