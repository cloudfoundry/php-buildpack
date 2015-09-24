import os
import os.path
import sys
import tempfile
import subprocess
import logging


# This and check_output are shims to support features of Python 2.7
#   on Python 2.6.
#
# This code was borrowed from PyPy 2.7.
#   bitbucket.org/pypy/pypy/src/9d88b4875d6e/lib-python/2.7/subprocess.py
#
# This can be removed when the CloudFoundry environment is upgraded
#   to Python 2.7 or higher.
#
class CalledProcessError(Exception):
    """This exception is raised when a process run by check_call() or
    check_output() returns a non-zero exit status.
    The exit status will be stored in the returncode attribute;
    check_output() will also store the output in the output attribute.
    """
    def __init__(self, returncode, cmd, output=None):
        self.returncode = returncode
        self.cmd = cmd
        self.output = output

    def __str__(self):
        return "Command '%s' returned non-zero exit status %d" % (
            self.cmd, self.returncode)


def check_output(*popenargs, **kwargs):
    r"""Run command with arguments and return its output as a byte string.

    If the exit code was non-zero it raises a CalledProcessError.  The
    CalledProcessError object will have the return code in the returncode
    attribute and output in the output attribute.

    The arguments are the same as for the Popen constructor.  Example:

    >>> check_output(["ls", "-l", "/dev/null"])
    'crw-rw-rw- 1 root root 1, 3 Oct 18  2007 /dev/null\n'

    The stdout argument is not allowed as it is used internally.
    To capture standard error in the result, use stderr=STDOUT.

    >>> check_output(["/bin/sh", "-c",
    ...               "ls -l non_existent_file ; exit 0"],
    ...              stderr=subprocess.STDOUT)
    'ls: non_existent_file: No such file or directory\n'
    """
    if 'stdout' in kwargs:
        raise ValueError('stdout argument not allowed, it will be overridden.')
    process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
    output, unused_err = process.communicate()
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        raise CalledProcessError(retcode, cmd, output=output)
    return output


def stream_output(*popenargs, **kwargs):
    r"""Run command with arguments and stream its output.

    If the exit code was non-zero it raises a CalledProcessError.  The
    CalledProcessError object will have the return code in the returncode
    attribute.

    The first argument should be the file like object where the output
    should be written.  The remainder of the arguments are the same as
    for the Popen constructor.

    Example:

    >>> fp = open('cmd-output.txt', 'wb')
    >>> stream_output(fp, ["ls", "-l", "/dev/null"])
    'crw-rw-rw- 1 root root 1, 3 Oct 18  2007 /dev/null\n'

    The stdout argument is not allowed as it is used internally.
    To capture standard error in the result, use stderr=STDOUT.

    >>> fp = open('cmd-output.txt', 'wb')
    >>> stream_output(fp, ["/bin/sh", "-c",
    ...               "ls -l non_existent_file ; exit 0"],
    ...               stderr=subprocess.STDOUT)
    'ls: non_existent_file: No such file or directory\n'
    """
    if 'stdout' in kwargs:
        raise ValueError('stdout argument not allowed, it will be overridden.')
    if hasattr(popenargs[0], 'fileno'):
        process = subprocess.Popen(stdout=popenargs[0],
                                   *popenargs[1:], **kwargs)
        retcode = process.wait()
    else:
        process = subprocess.Popen(stdout=subprocess.PIPE,
                                   *popenargs[1:], **kwargs)
        for c in iter(lambda: process.stdout.read(1024), ''):
            popenargs[0].write(c)
        retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        raise CalledProcessError(retcode, cmd)


class BuildPack(object):
    def __init__(self, ctx, url, branch=None, stream=sys.stdout):
        self._ctx = ctx
        self._url = url
        self._branch = branch
        self._stream = stream
        self.bp_dir = tempfile.mkdtemp(prefix='buildpack')
        self._log = logging.getLogger('runner')

    def run(self):
        if self._url:
            self._clone()
            self.framework = self._detect()
            self._compile()
            self.start_yml = self._release()

    def _clone(self):
        self._log.debug("Cloning [%s] to [%s]", self._url, self.bp_dir)
        stream_output(self._stream,
                      " ".join(['git', 'clone', self._url, self.bp_dir]),
                      stderr=subprocess.STDOUT,
                      shell=True)
        if self._branch:
            self._log.debug("Branching to [%s]", self._branch)
            stream_output(self._stream,
                          " ".join(['git', 'checkout', self._branch]),
                          stderr=subprocess.STDOUT,
                          shell=True)

    def _detect(self):
        self._log.debug("Running detect script")
        cmd = [os.path.join(self.bp_dir, 'bin', 'detect'),
               self._ctx['BUILD_DIR']]
        return check_output(" ".join(cmd),
                            stderr=subprocess.STDOUT,
                            shell=True).strip()

    def _compile(self):
        self._log.debug("Running compile script with build dir [%s] "
                        "and cache dir [%s]",
                        self._ctx['BUILD_DIR'],
                        self._ctx['CACHE_DIR'])
        cmd = [os.path.join(self.bp_dir, 'bin', 'compile'),
               self._ctx['BUILD_DIR'],
               self._ctx['CACHE_DIR']]
        stream_output(self._stream,
                      " ".join(cmd),
                      stderr=subprocess.STDOUT,
                      shell=True)

    def _release(self):
        self._log.debug("Running release script")
        cmd = [os.path.join(self.bp_dir, 'bin', 'release'),
               self._ctx['BUILD_DIR']]
        return check_output(" ".join(cmd),
                            stderr=subprocess.STDOUT,
                            shell=True).strip()
