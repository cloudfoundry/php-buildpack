import os
import sys
import shutil
import logging
import codecs
import inspect
import re
from string import Template
from runner import check_output


_log = logging.getLogger('utils')


def safe_makedirs(path):
    try:
        os.makedirs(path)
    except OSError, e:
        # Ignore if it exists
        if e.errno != 17:
            raise e


def load_env(path):
    _log.info("Loading environment from [%s]", path)
    env = {}
    with open(path, 'rt') as envFile:
        for line in envFile:
            name, val = line.strip().split('=', 1)
            env[name.strip()] = val.strip()
    _log.debug("Loaded environment [%s]", env)
    return env


def load_processes(path):
    _log.info("Loading processes from [%s]", path)
    procs = {}
    with open(path, 'rt') as procFile:
        for line in procFile:
            name, cmd = line.strip().split(':', 1)
            procs[name.strip()] = cmd.strip()
    _log.debug("Loaded processes [%s]", procs)
    return procs


def load_extension(path):
    _log.debug("Loading extension from [%s]", path)
    init = os.path.join(path, '__init__.py')
    if not os.path.exists(init):
        with open(init, 'w'):
            pass  # just create an empty file
    try:
        sys.path.append(os.path.dirname(path))
        extn = __import__('%s.extension' % os.path.basename(path),
                          fromlist=['extension'])
    finally:
        sys.path.remove(os.path.dirname(path))
    return extn


def process_extension(path, ctx, to_call, success, args=None, ignore=False):
    _log.debug('Processing extension from [%s] with method [%s]',
               path, to_call)
    if not args:
        args = [ctx]
    extn = load_extension(path)
    try:
        if hasattr(extn, to_call):
            success(getattr(extn, to_call)(*args))
    except Exception:
        if ignore:
            _log.exception("Error with extension [%s]" % path)
        else:
            raise


def process_extensions(ctx, to_call, success, args=None, ignore=False):
    for path in ctx['EXTENSIONS']:
        process_extension(path, ctx, to_call, success, args, ignore)


def rewrite_with_template(template, cfgPath, ctx):
    with codecs.open(cfgPath, encoding='utf-8') as fin:
        data = fin.read()
    with codecs.open(cfgPath, encoding='utf-8', mode='wt') as out:
        out.write(template(data).safe_substitute(ctx))


def rewrite_cfgs(toPath, ctx, delim='#'):
    class RewriteTemplate(Template):
        delimiter = delim
    if os.path.isdir(toPath):
        _log.info("Rewriting configuration under [%s]", toPath)
        for root, dirs, files in os.walk(toPath):
            for f in files:
                cfgPath = os.path.join(root, f)
                _log.debug("Rewriting [%s]", cfgPath)
                rewrite_with_template(RewriteTemplate, cfgPath, ctx)
    else:
        _log.info("Rewriting configuration file [%s]", toPath)
        rewrite_with_template(RewriteTemplate, toPath, ctx)


def find_git_url(bp_dir):
    if os.path.exists(os.path.join(bp_dir, '.git')):
        try:
            url = check_output(['git', '--git-dir=%s/.git' % bp_dir,
                                'config', '--get', 'remote.origin.url'])
            commit = check_output(['git', '--git-dir=%s/.git' % bp_dir,
                                   'rev-parse', '--short', 'HEAD'])
            if url and commit:
                return "%s#%s" % (url.strip(), commit.strip())
        except OSError:
            _log.debug("Git does not seem to be installed / available",
                       exc_info=True)


class FormattedDictWrapper(object):
    def __init__(self, obj):
        self.obj = obj

    def unwrap(self):
        return self.obj

    def __str__(self):
        return self.obj.__str__()

    def __repr__(self):
        return self.obj.__repr__()


def wrap(obj):
    return FormattedDictWrapper(obj)


class FormattedDict(dict):
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)

    def format(self, val):
        if hasattr(val, 'format'):
            val = val.format(**self)
            newVal = val.format(**self)
            while val != newVal:
                val = newVal
                newVal = newVal.format(**self)
            return val
        return val.unwrap() if hasattr(val, 'unwrap') else val

    def __getitem__(self, key):
        return self.format(dict.__getitem__(self, key))

    def get(self, *args, **kwargs):
        if kwargs.get('format', True):
            return self.format(dict.get(self, *args))
        else:
            tmp = dict.get(self, *args)
            return tmp.unwrap() if hasattr(tmp, 'unwrap') else tmp

    def __setitem__(self, key, val):
        if _log.isEnabledFor(logging.DEBUG):
            frame = inspect.currentframe()
            caller = inspect.getouterframes(frame, 2)
            info = caller[1]
            _log.debug('line #%s in %s, "%s" is setting [%s] = [%s]',
                       info[2], info[1], info[3], key, val)
        dict.__setitem__(self, key, val)


class ConfigFileEditor(object):
    def __init__(self, cfgPath):
        with open(cfgPath, 'rt') as cfg:
            self._lines = cfg.readlines()

    def find_lines_matching(self, regex):
        if hasattr(regex, 'strip'):
            regex = re.compile(regex)
        if not hasattr(regex, 'match'):
            raise ValueError("must be str or RegexObject")
        return [line.strip() for line in self._lines if regex.match(line)]

    def update_lines(self, regex, repl):
        if hasattr(regex, 'strip'):
            regex = re.compile(regex)
        if not hasattr(regex, 'match'):
            raise ValueError("must be str or RegexObject")
        self._lines = [regex.sub(repl, line) for line in self._lines]

    def append_lines(self, lines):
        self._lines.extend(lines)

    def insert_after(self, regex, lines):
        if hasattr(regex, 'strip'):
            regex = re.compile(regex)
        if not hasattr(regex, 'match'):
            raise ValueError("must be str or RegexObject")
        for i, line in enumerate(self._lines):
            if regex.match(line):
                for j, item in enumerate(["%s\n" % l for l in lines]):
                    self._lines.insert((i + j + 1), item)
                break

    def save(self, cfgPath):
        with open(cfgPath, 'wt') as cfg:
            cfg.writelines(self._lines)


def unique(seq):
    """Return only the unique items in the given list, but preserve order"""
    # http://stackoverflow.com/a/480227
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


# This is copytree from PyPy 2.7 source code.
#   https://bitbucket.org/pypy/pypy/src/9d88b4875d6e/lib-python/2.7/shutil.py
# Modifying this so that it doesn't care about an initial directory existing

# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


def copytree(src, dst, symlinks=False, ignore=None):
    """Recursively copy a directory tree using copy2().

    If exception(s) occur, an Error is raised with a list of reasons.

    If the optional symlinks flag is true, symbolic links in the
    source tree result in symbolic links in the destination tree; if
    it is false, the contents of the files pointed to by symbolic
    links are copied.

    The optional ignore argument is a callable. If given, it
    is called with the `src` parameter, which is the directory
    being visited by copytree(), and `names` which is the list of
    `src` contents, as returned by os.listdir():

        callable(src, names) -> ignored_names

    Since copytree() is called recursively, the callable will be
    called once for each directory that is copied. It returns a
    list of names relative to the `src` directory that should
    not be copied.

    XXX Consider this example code rather than the ultimate tool.

    """
    names = os.listdir(src)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()
    try:
        os.makedirs(dst)
    except OSError, e:
        if e.errno != 17:  # File exists
            raise e
    errors = []
    for name in names:
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                copytree(srcname, dstname, symlinks, ignore)
            else:
                # Will raise a SpecialFileError for unsupported file types
                shutil.copy2(srcname, dstname)
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except shutil.Error, err:
            errors.extend(err.args[0])
        except EnvironmentError, why:
            errors.append((srcname, dstname, str(why)))
    try:
        shutil.copystat(src, dst)
    except OSError, why:
        if WindowsError is not None and isinstance(why, WindowsError):
            # Copying file access times may fail on Windows
            pass
        else:
            errors.extend((src, dst, str(why)))
    if errors:
        raise shutil.Error, errors
