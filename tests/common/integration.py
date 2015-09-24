import json
import tempfile
import shutil
import os
import itertools
from StringIO import StringIO


class OptionsHelper(object):
    """Helper setting options in an options.json file"""

    def __init__(self, optsFile):
        self._opts_file = optsFile
        self._opts = json.load(open(optsFile))

    def _set_key(self, key, val):
        """Set a key value pair in the options file, writes change to file."""
        self._opts[key] = val
        json.dump(self._opts, open(self._opts_file, 'wt'))

    def __getattr__(self, name):
        """Overrides any method `set_...` methods to call `_set_key`"""
        if name.startswith('set_'):
            return lambda val: self._set_key(name[4:].upper(), val)
        if name.startswith('get_'):
            return lambda: self._opts[name[4:].upper()]
        return AttributeError("%s instance has no attribute '%s'" %
                              self.__class__.__name__, name)


class DirectoryHelper(object):
    """Helper for creating build pack test directories"""

    def __init__(self):
        self._temp_dirs = []  # temp dirs to delete
        self._temp_files = []  # temp files to delete

    def create_build_dir_from(self, app):
        """Create a temporary build directory, with app contents"""
        build_dir = tempfile.mkdtemp(prefix='build-')
        os.rmdir(build_dir)  # delete otherwise copytree complains
        shutil.copytree(app, build_dir)
        self._temp_dirs.append(build_dir)
        return build_dir

    def create_cache_dir(self):
        """Create a temporary cache directory"""
        cache_dir = tempfile.mkdtemp(prefix='cache-')
        os.rmdir(cache_dir)  # should not exist by default
        self._temp_dirs.append(cache_dir)
        return cache_dir

    def create_temp_dir(self):
        """Create a temporary directory"""
        temp_dir = tempfile.mkdtemp(prefix='temp-')
        self._temp_dirs.append(temp_dir)
        return temp_dir

    def register_to_delete(self, path):
        p = ((len(path) > 1) and os.path.join(path) or path)
        if os.path.exists(p) and os.path.isfile(p):
            self._temp_files.append(p)
        elif os.path.exists(p) and os.path.isdir(p):
            self._temp_dirs.append(p)
        else:
            raise ValueError("File doesn't exist or not the right type")

    def create_bp_env(self, app):
        return (
            self.create_build_dir_from(os.path.join('tests', 'data', app)),
            self.create_cache_dir(),
            self.create_temp_dir())

    def copy_build_pack_to(self, bp_dir):
        # simulate clone, makes debugging easier
        os.rmdir(bp_dir)
        shutil.copytree('.', bp_dir,
                        ignore=shutil.ignore_patterns("binaries",
                                                      "env",
                                                      "tests"))
        binPath = os.path.join(bp_dir, 'binaries', 'lucid')
        os.makedirs(binPath)

    def cleanup(self):
        """Removes all of the temp files and directories that were created"""
        for f in self._temp_files:
            if os.path.exists(f):
                if os.path.isfile(f):
                    os.remove(f)
                else:
                    print 'Could not remove [%s], not a file' % f
        for d in self._temp_dirs:
            if os.path.exists(d):
                if os.path.isdir(d):
                    shutil.rmtree(d)
                else:
                    print 'Could not remove [%s], not a directory' % d


class FileAssertHelper(object):
    """Helper for asserting on files and directories"""
    def expect(self):
        self._paths = []
        self._root = []
        return self

    def root(self, *args, **kwargs):
        if not kwargs.get('reset', False):
            self._root.extend(args)
        else:
            self._root = args
        return self

    def path(self, *args):
        self._paths.append(os.path.join(*(tuple(self._root) + tuple(args))))
        return self

    def exists(self):
        for path in self._paths:
            assert os.path.exists(path), "Does not exist: %s" % path
        return self

    def does_not_exist(self):
        for path in self._paths:
            assert not os.path.exists(path), "Does exist: %s" % path
        return self

    def directory_count_equals(self, cnt):
        root = os.path.join(*self._root)
        assert \
            len(os.listdir(root)) == cnt, \
            "Directory [%s] does not contain [%d] files" % (root, cnt)
        return self


class TextFileAssertHelper(object):
    """Helper for asserting on the textual contents of a file"""

    def _check(self, test, expected):
        if len(self._selection) == 1:
            line = self._selection[0]
            assert test(line), \
                "Found [%s] but expected [%s]" % (line, expected)
        elif len(self._selection) > 1:
            assert self._method([test(line) for line in self._selection]), \
                ("[%s] not found on any line\n"
                 "Choices were:\n\n\t%s" %
                 (expected, "\t".join(self._selection)))

    def expect(self):
        self._path = None
        self._contents = []
        self._selection = self._contents
        self._method = all
        return self

    def on_file(self, *path):
        self._path = os.path.join(*path)
        with open(self._path, 'rt') as fp:
            self._contents = fp.readlines()
        return self

    def on_string(self, data):
        self._path = '<str>'
        if hasattr(data, 'split'):
            self._contents = data.split('\n')
        else:
            self._contents = data
        return self

    def any_line(self):
        self._selection = self._contents
        self._method = any
        return self

    def line(self, num):
        self._method = all
        self._selection = [self._contents[num]]
        return self

    def equals(self, val):
        self._check(lambda l: l == val, val)
        return self

    def contains(self, val):
        self._check(lambda l: l.find(val) != -1, val)
        return self

    def does_not_contain(self, val):
        self._check(lambda l: l.find(val) == -1, val)
        return self

    def startswith(self, val):
        self._check(lambda l: l.startswith(val), val)
        return self

    def line_count_equals(self, num, test=None):
        found = len([item for item in itertools.ifilter(test, self._contents)])
        assert num == found, \
            "Found [%d] lines, not [%d] in [%s]\n\nContents:\n%s" % \
            (found, num, self._path, "\n".join(self._contents))
        return self


class ErrorHelper(object):
    """Helper for catching, logging and debugging errors"""

    def compile(self, bp):
        buf = StringIO()
        try:
            bp._stream = buf
            bp._compile()
            return buf.getvalue().strip()
        except Exception, e:
            print "Command Output:"
            print buf.getvalue().strip()
            if hasattr(e, 'output'):
                print e.output
            raise
