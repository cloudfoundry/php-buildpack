import shutil
import tempfile
import os.path
import re
from nose.tools import with_setup
from build_pack_utils import BuildPack


class TestDetect(object):
    def setUp(self):
        self.build_dir = tempfile.mkdtemp(prefix='build-')
        self.cache_dir = tempfile.mkdtemp(prefix='cache-')
        os.rmdir(self.build_dir)  # delete otherwise copytree complains
        os.rmdir(self.cache_dir)  # cache dir does not exist normally

    def tearDown(self):
        if os.path.exists(self.build_dir):
            shutil.rmtree(self.build_dir)
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)
        for name in os.listdir(os.environ['TMPDIR']):
            if name.startswith('httpd-') and name.endswith('.gz'):
                os.remove(os.path.join(os.environ['TMPDIR'], name))
            if name.startswith('php-') and name.endswith('.gz'):
                os.remove(os.path.join(os.environ['TMPDIR'], name))

    @with_setup(setup=setUp, teardown=tearDown)
    def test_detect_php_and_htdocs(self):
        shutil.copytree('tests/data/app-1', self.build_dir)
        bp = BuildPack({
            'BUILD_DIR': self.build_dir,
            'CACHE_DIR': self.cache_dir,
            'WEBDIR': 'htdocs'
        }, '.')
        # simulate clone, makes debugging easier
        os.rmdir(bp.bp_dir)
        shutil.copytree('.', bp.bp_dir,
                        ignore=shutil.ignore_patterns("binaries",
                                                      "env",
                                                      "tests"))
        try:
            output = bp._detect().strip()
            assert re.match('php*', output)
        except Exception, e:
            print str(e)
            if hasattr(e, 'output'):
                print e.output
            if output:
                print output
            raise
        finally:
            if os.path.exists(bp.bp_dir):
                shutil.rmtree(bp.bp_dir)

    @with_setup(setup=setUp, teardown=tearDown)
    def test_detect_php(self):
        shutil.copytree('tests/data/app-2', self.build_dir)
        bp = BuildPack({
            'BUILD_DIR': self.build_dir,
            'CACHE_DIR': self.cache_dir,
            'WEBDIR': 'htdocs'
        }, '.')
        # simulate clone, makes debugging easier
        os.rmdir(bp.bp_dir)
        shutil.copytree('.', bp.bp_dir,
                        ignore=shutil.ignore_patterns("binaries",
                                                      "env",
                                                      "tests"))
        try:
            output = bp._detect().strip()
            assert re.match('php*', output)
        except Exception, e:
            print str(e)
            if hasattr(e, 'output'):
                print e.output
            if output:
                print output
            raise
        finally:
            if os.path.exists(bp.bp_dir):
                shutil.rmtree(bp.bp_dir)

    @with_setup(setup=setUp, teardown=tearDown)
    def test_detect_static(self):
        shutil.copytree('tests/data/app-3', self.build_dir)
        bp = BuildPack({
            'BUILD_DIR': self.build_dir,
            'CACHE_DIR': self.cache_dir,
            'WEBDIR': 'htdocs'
        }, '.')
        # simulate clone, makes debugging easier
        os.rmdir(bp.bp_dir)
        shutil.copytree('.', bp.bp_dir,
                        ignore=shutil.ignore_patterns("binaries",
                                                      "env",
                                                      "tests"))
        try:
            output = bp._detect().strip()
            assert re.match('php*', output)
        except Exception, e:
            print str(e)
            if hasattr(e, 'output'):
                print e.output
            raise
        finally:
            if os.path.exists(bp.bp_dir):
                shutil.rmtree(bp.bp_dir)

    @with_setup(setup=setUp, teardown=tearDown)
    def test_detect_with_invalid_json(self):
        shutil.copytree('tests/data/app-invalid-json', self.build_dir)
        bp = BuildPack({
            'BUILD_DIR': self.build_dir,
            'CACHE_DIR': self.cache_dir,
            'WEBDIR': 'htdocs'
        }, '.')
        # simulate clone, makes debugging easier
        os.rmdir(bp.bp_dir)
        shutil.copytree('.', bp.bp_dir,
                        ignore=shutil.ignore_patterns("binaries",
                                                      "env",
                                                      "tests"))
        try:
            output = bp._detect().strip()
            assert re.match('php*', output)
        except Exception, e:
            print str(e)
            if hasattr(e, 'output'):
                print e.output
            if output:
                print output
        finally:
            if os.path.exists(bp.bp_dir):
                shutil.rmtree(bp.bp_dir)

    @with_setup(setup=setUp, teardown=tearDown)
    def test_detect_with_asp_net_app(self):
        shutil.copytree('tests/data/app-asp-net', self.build_dir)
        bp = BuildPack({
            'BUILD_DIR': self.build_dir,
            'CACHE_DIR': self.cache_dir,
            'WEBDIR': 'htdocs'
        }, '.')
        # simulate clone, makes debugging easier
        os.rmdir(bp.bp_dir)
        shutil.copytree('.', bp.bp_dir,
                        ignore=shutil.ignore_patterns("binaries",
                                                      "env",
                                                      "tests"))
        try:
            bp._detect().strip()
        except Exception, e:
            print e.output
            assert re.match('no', e.output)
        finally:
            if os.path.exists(bp.bp_dir):
                shutil.rmtree(bp.bp_dir)
