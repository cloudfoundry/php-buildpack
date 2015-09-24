from __future__ import print_function

import signal
import subprocess
import sys
import logging
from datetime import datetime
from threading import Thread
from Queue import Queue, Empty


#
# This code comes from Honcho.  Didn't need the whole Honcho
#   setup, so I just swiped this part which is what the build
#   pack utils library needs.
#
#  https://github.com/nickstenning/honcho
#
# I've modified parts to fit better with this module.
#

# Copyright (c) 2012 Nick Stenning, http://whiteink.com/

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


def _enqueue_output(proc, queue):
    if not proc.quiet:
        for line in iter(proc.stdout.readline, b''):
            try:
                line = line.decode('utf-8')
            except UnicodeDecodeError as e:
                queue.put((proc, e))
                continue
            if not line.endswith('\n'):
                line += '\n'
            queue.put((proc, line))
        proc.stdout.close()


class Process(subprocess.Popen):
    def __init__(self, cmd, name=None, quiet=False, *args, **kwargs):
        self.name = name
        self.quiet = quiet
        self.reader = None
        self.printer = None
        self.dead = False

        if self.quiet:
            self.name = "{0} (quiet)".format(self.name)

        defaults = {
            'stdout': subprocess.PIPE,
            'stderr': subprocess.STDOUT,
            'shell': True,
            'bufsize': 1,
            'close_fds': True
        }
        defaults.update(kwargs)

        super(Process, self).__init__(cmd, *args, **defaults)


class ProcessManager(object):
    """
    Here's where the business happens. The ProcessManager multiplexes and
    pretty-prints the output from a number of Process objects, typically added
    using the add_process() method.

    Example:

        pm = ProcessManager()
        pm.add_process('name', 'ruby server.rb')
        pm.add_process('name', 'python worker.py')

        pm.loop()
    """
    def __init__(self):
        self.processes = []
        self.queue = Queue()
        self.returncode = None
        self._terminating = False
        self._log = logging.getLogger('process')

    def add_process(self, name, cmd, quiet=False):
        """
        Add a process to this manager instance:

        Arguments:

        name        - a human-readable identifier for the process
                      (e.g. 'worker'/'server')
        cmd         - the command-line used to run the process
                      (e.g. 'python run.py')
        """
        self._log.debug("Adding process [%s] with cmd [%s]", name, cmd)
        self.processes.append(Process(cmd, name=name, quiet=quiet))

    def loop(self):
        """
        Enter the main loop of the program. This will print the multiplexed
        output of all the processes in this ProcessManager to sys.stdout, and
        will block until all the processes have completed.

        If one process terminates, all the others will be terminated
        and loop() will return.

        Returns: the returncode of the first process to exit, or 130 if
        interrupted with Ctrl-C (SIGINT)
        """
        self._init_readers()
        self._init_printers()

        for proc in self.processes:
            self._log.info("Started [%s] with pid [%s]", proc.name, proc.pid)

        while True:
            try:
                proc, line = self.queue.get(timeout=0.1)
            except Empty:
                pass
            except KeyboardInterrupt:
                self._log.exception("SIGINT received")
                self.returncode = 130
                self.terminate()
            else:
                self._print_line(proc, line)

            for proc in self.processes:
                if not proc.dead and proc.poll() is not None:
                    self._log.info('process [%s] with pid [%s] terminated',
                                   proc.name, proc.pid)
                    proc.dead = True

                    # Set the returncode of the ProcessManager instance if not
                    # already set.
                    if self.returncode is None:
                        self.returncode = proc.returncode

                    self.terminate()

            if not self._process_count() > 0:
                break

        while True:
            try:
                proc, line = self.queue.get(timeout=0.1)
            except Empty:
                break
            else:
                self._print_line(proc, line)

        return self.returncode

    def terminate(self):
        """

        Terminate all the child processes of this ProcessManager, bringing the
        loop() to an end.

        """
        if self._terminating:
            return False

        self._terminating = True

        self._log.info("sending SIGTERM to all processes")
        for proc in self.processes:
            if proc.poll() is None:
                self._log.info("sending SIGTERM to pid [%d]", proc.pid)
                proc.terminate()

        def kill(signum, frame):
            # If anything is still alive, SIGKILL it
            for proc in self.processes:
                if proc.poll() is None:
                    self._log.info("sending SIGKILL to pid [%d]", proc.pid)
                    proc.kill()

        signal.signal(signal.SIGALRM, kill)  # @UndefinedVariable
        signal.alarm(5)  # @UndefinedVariable

    def _process_count(self):
        return [p.poll() for p in self.processes].count(None)

    def _init_readers(self):
        for proc in self.processes:
            self._log.debug("Starting [%s]", proc.name)
            t = Thread(target=_enqueue_output, args=(proc, self.queue))
            t.daemon = True  # thread dies with the program
            t.start()

    def _init_printers(self):
        width = max(len(p.name) for p in
                    filter(lambda x: not x.quiet, self.processes))
        for proc in self.processes:
            proc.printer = Printer(sys.stdout,
                                   name=proc.name,
                                   width=width)

    def _print_line(self, proc, line):
        if isinstance(line, UnicodeDecodeError):
            self._log.error(
                "UnicodeDecodeError while decoding line from process [%s]",
                proc.name)
        else:
            print(line, end='', file=proc.printer)


class Printer(object):
    def __init__(self, output=sys.stdout, name='unknown', width=0):
        self.output = output
        self.name = name
        self.width = width

        self._write_prefix = True

    def write(self, *args, **kwargs):
        new_args = []

        for arg in args:
            lines = arg.split('\n')
            lines = [self._prefix() + l if l else l for l in lines]
            new_args.append('\n'.join(lines).encode('utf-8'))

        self.output.write(*new_args, **kwargs)

    def _prefix(self):
        time = datetime.now().strftime('%H:%M:%S')
        name = self.name.ljust(self.width)
        prefix = '{time} {name} | '.format(time=time, name=name)
        return prefix
