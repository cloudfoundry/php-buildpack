import os
import sys
import shutil
import re
from subprocess import Popen
from subprocess import PIPE
from cloudfoundry import CloudFoundryUtil
from cloudfoundry import CloudFoundryInstaller
from detecter import TextFileSearch
from detecter import RegexFileSearch
from detecter import StartsWithFileSearch
from detecter import EndsWithFileSearch
from detecter import ContainsFileSearch


class Configurer(object):
    def __init__(self, builder):
        self.builder = builder

    def default_config(self):
        self._merge(
            CloudFoundryUtil.load_json_config_file_from(
                self.builder._ctx['BP_DIR'],
                'defaults/options.json'))
        return self

    def user_config(self, path=None):
        if path is None:
            path = os.path.join('config', 'options.json')
        self._merge(
            CloudFoundryUtil.load_json_config_file_from(
                self.builder._ctx['BUILD_DIR'], path))
        return self

    def done(self):
        return self.builder

    def _merge(self, ctx):
        self.builder._ctx.update(ctx)


class Detecter(object):
    def __init__(self, builder):
        self._builder = builder
        self._detecter = None
        self._recursive = False
        self._fullPath = False
        self._output = 'Found'
        self._root = builder._ctx['BUILD_DIR']

    def _config(self, detecter):
        detecter.recursive = self._recursive
        detecter.fullPath = self._fullPath
        return detecter

    def with_regex(self, regex):
        self._detecter = self._config(RegexFileSearch(regex))
        return self

    def by_name(self, name):
        self._detecter = self._config(TextFileSearch(name))
        return self

    def starts_with(self, text):
        self._detecter = self._config(StartsWithFileSearch(text))
        return self

    def ends_with(self, text):
        self._detecter = self._config(EndsWithFileSearch(text))
        return self

    def contains(self, text):
        self._detecter = self._config(ContainsFileSearch(text))
        return self

    def recursive(self):
        self._recursive = True
        if self._detecter:
            self._detecter.recursive = True
        return self

    def using_full_path(self):
        self._fullPath = True
        if self._detecter:
            self._detecter.fullPath = True
        return self

    def if_found_output(self, text):
        self._output = text
        return self

    def under(self, root):
        self._root = root
        self.recursive()
        return self

    def at(self, root):
        self._root = root
        return self

    def done(self):
        # calls to sys.exit are expected here and needed to
        #  conform to the requirements of CF's detect script
        #  which must set exit codes
        if self._detecter:
            if self._detecter.search(self._root):
                print self._output
                sys.exit(0)
        print 'no'
        sys.exit(1)


class Installer(object):
    def __init__(self, builder):
        self.builder = builder
        self._installer = CloudFoundryInstaller(self.builder._ctx)

    def package(self, key):
        self.builder._ctx['%s_INSTALL_PATH' % key] = \
            self._installer.install_binary(key)
        return self

    def packages(self, *keys):
        for key in keys:
            self.package(key)
        return self

    def config(self):
        return ConfigInstaller(self)

    def done(self):
        return self.builder


class ConfigInstaller(object):
    def __init__(self, installer):
        self._installer = installer
        self._cfInst = installer._installer
        self._ctx = installer.builder._ctx
        self._app_path = None
        self._bp_path = None
        self._to_path = None
        self._all_files = False

    def from_build_pack(self, fromFile):
        self._bp_path = fromFile
        return self

    def or_from_build_pack(self, fromFile):
        self._bp_path = fromFile
        return self

    def from_application(self, fromFile):
        self._app_path = fromFile
        return self

    def to(self, toPath):
        self._to_path = toPath
        return self

    def all_files(self):
        self._all_files = True
        return self

    def done(self):
        if (self._bp_path or self._app_path) and self._to_path:
            if not self._all_files:
                if self._bp_path:
                    self._cfInst.install_from_build_pack(self._bp_path,
                                                         self._to_path)
                if self._app_path:
                    self._cfInst.install_from_application(self._app_path,
                                                          self._to_path)
            else:
                if self._bp_path:
                    root = os.path.join(self._ctx['BP_DIR'], self._bp_path)
                    for item in os.listdir(root):
                        fromFile = os.path.join(self._bp_path, item)
                        toFile = os.path.join(self._to_path, item)
                        self._cfInst.install_from_build_pack(fromFile, toFile)
                if self._app_path:
                    root = os.path.join(self._ctx['BUILD_DIR'], self._app_path)
                    if os.path.exists(root) and os.path.isdir(root):
                        for item in os.listdir(root):
                            fromFile = os.path.join(self._app_path, item)
                            toFile = os.path.join(self._to_path, item)
                            self._cfInst.install_from_application(fromFile,
                                                                  toFile)
        return self._installer


class Runner(object):
    def __init__(self, builder):
        self._builder = builder
        self._path = os.getcwd()
        self._shell = False
        self._cmd = []
        self._on_finish = None
        self._on_success = None
        self._on_fail = None
        self._env = os.environ.copy()

    def done(self):
        if os.path.exists(self._path):
            cwd = os.getcwd()
            try:
                os.chdir(self._path)
                proc = Popen(self._cmd, stdout=PIPE, env=self._env,
                             stderr=PIPE, shell=self._shell)
                stdout, stderr = proc.communicate()
                retcode = proc.poll()
                if self._on_finish:
                    self._on_finish(self._cmd, retcode, stdout, stderr)
                else:
                    if retcode == 0 and self._on_success:
                        self._on_success(self._cmd, retcode, stdout)
                    elif retcode != 0 and self._on_fail:
                        self._on_fail(self._cmd, retcode, stderr)
                    elif retcode != 0:
                        print 'Command [%s] failed with [%d], add an ' \
                            '"on_fail" or "on_finish" method to debug ' \
                            'further' % (self._cmd, retcode)
            finally:
                os.chdir(cwd)
        return self._builder

    def environment_variable(self):
        return RunnerEnvironmentVariableBuilder(self)

    def command(self, command):
        if hasattr(command, '__call__'):
            self._cmd = command(self._builder._ctx)
        elif hasattr(command, 'split'):
            self._cmd = command.split(' ')
        else:
            self._cmd = command
        if self._shell:
            self._cmd = ' '.join(self._cmd)
        return self

    def out_of(self, path):
        if hasattr(path, '__call__'):
            self._path = path(self._builder._ctx)
        elif path in self._builder._ctx.keys():
            self._path = self._builder._ctx[path]
        else:
            self._path = path
        return self

    def with_shell(self):
        self._shell = True
        if not hasattr(self._cmd, 'strip'):
            self._cmd = ' '.join(self._cmd)
        return self

    def on_success(self, on_success):
        if hasattr(on_success, '__call__'):
            self._on_success = on_success
        return self

    def on_fail(self, on_fail):
        if hasattr(on_fail, '__call__'):
            self._on_fail = on_fail
        return self

    def on_finish(self, on_finish):
        if hasattr(on_finish, '__call__'):
            self._on_finish = on_finish
        return self


class RunnerEnvironmentVariableBuilder(object):
    def __init__(self, runner):
        self._runner = runner
        self._name = None

    def name(self, name):
        self._name = name
        return self

    def value(self, value):
        if not self._name:
            raise ValueError('You must specify a name')
        if hasattr(value, '__call__'):
            value = value()
        elif value in self._runner._builder._ctx.keys():
            value = self._runner._builder._ctx[value]
        self._runner._env[self._name] = value
        return self._runner


class Executor(object):
    def __init__(self, builder):
        self.builder = builder

    def method(self, execute):
        if hasattr(execute, '__call__'):
            execute(self.builder._ctx)
        return self.builder


class FileUtil(object):
    def __init__(self, builder, move=False):
        self._builder = builder
        self._move = move
        self._filters = []
        self._from_path = None
        self._into_path = None

    def everything(self):
        self._filters.append((lambda path: True))
        return self

    def all_files(self):
        self._filters.append(
            lambda path: os.path.isfile(path))
        return self

    def hidden(self):
        self._filters.append(
            lambda path: path.startswith('.'))
        return self

    def not_hidden(self):
        self._filters.append(
            lambda path: not path.startswith('.'))
        return self

    def all_folders(self):
        self._filters.append(
            lambda path: os.path.isdir(path))
        return self

    def where_name_matches(self, pattern):
        if hasattr(pattern, 'strip'):
            pattern = re.compile(pattern)
        self._filters.append(
            lambda path: (pattern.match(path) is not None))
        return self

    def under(self, path):
        if path in self._builder._ctx.keys():
            self._from_path = self._builder._ctx[path]
        elif not path.startswith('/'):
            self._from_path = os.path.join(os.getcwd(), path)
        else:
            self._from_path = path
        return self

    def into(self, path):
        if path in self._builder._ctx.keys():
            self._into_path = self._builder._ctx[path]
        elif not path.startswith('/'):
            self._into_path = os.path.join(self._from_path, path)
        else:
            self._into_path = path
        return self

    def _copy_or_move(self, src, dest):
        if os.path.isfile(src):
            dest_base = os.path.dirname(dest)
            if not os.path.exists(dest_base):
                os.makedirs(os.path.dirname(dest))
        if not self._move:
            if os.path.isfile(src):
                shutil.copy(src, dest)
            else:
                shutil.copytree(src, dest)
        else:
            shutil.move(src, dest)

    def done(self):
        if self._from_path and self._into_path:
            if self._from_path == self._into_path:
                raise ValueError("Source and destination paths "
                                 "are the same [%s]" % self._from_path)
            if not os.path.exists(self._from_path):
                raise ValueError("Source path [%s] does not exist"
                                 % self._from_path)
            if os.path.exists(self._into_path):
                raise ValueError("Destination path [%s] already exists"
                                 % self._into_path)
            for item in os.listdir(self._from_path):
                if all([f(item) for f in self._filters]):
                    self._copy_or_move(
                        os.path.join(self._from_path, item),
                        os.path.join(self._into_path, item))
        return self._builder


class StartScriptBuilder(object):
    def __init__(self, builder):
        self.builder = builder
        self.content = []

    def manual(self, cmd):
        self.content.append(cmd)

    def environment_variable(self):
        return EnvironmentVariableBuilder(self)

    def command(self):
        return ScriptCommandBuilder(self.builder, self)

    def write(self):
        scriptName = self.builder._ctx.get('START_SCRIPT_NAME',
                                           'start.sh')
        startScriptPath = os.path.join(
            self.builder._ctx['BUILD_DIR'], scriptName)
        with open(startScriptPath, 'wt') as out:
            out.write('\n'.join(self.content))
        os.chmod(startScriptPath, 0755)
        return self.builder


class ScriptCommandBuilder(object):
    def __init__(self, builder, scriptBuilder):
        self._builder = builder
        self._scriptBuilder = scriptBuilder
        self._command = None
        self._args = []
        self._background = False
        self._stdout = None
        self._stderr = None
        self._both = None
        self._content = []

    def manual(self, cmd):
        self._content.append(cmd)
        return self

    def run(self, command):
        self._command = command
        return self

    def with_argument(self, argument):
        if hasattr(argument, '__call__'):
            argument = argument()
        elif argument in self._builder._ctx.keys():
            argument = self._builder._ctx[argument]
        self._args.append(argument)
        return self

    def background(self):
        self._background = True
        return self

    def redirect(self, stderr=None, stdout=None, both=None):
        self._stderr = stderr
        self._stdout = stdout
        self._both = both
        return self

    def pipe(self):
        # background should be on last command only
        self._background = False
        return ScriptCommandBuilder(self._builder, self)

    def done(self):
        cmd = []
        if self._command:
            cmd.append(self._command)
            cmd.extend(self._args)
            if self._both:
                cmd.append('&> %s' % self._both)
            elif self._stdout:
                cmd.append('> %s' % self._stdout)
            elif self._stderr:
                cmd.append('2> %s' % self._stderr)
            if self._background:
                cmd.append('&')
        if self._content:
            if self._command:
                cmd.append('|')
            cmd.append(' '.join(self._content))
        self._scriptBuilder.manual(' '.join(cmd))
        return self._scriptBuilder


class EnvironmentVariableBuilder(object):
    def __init__(self, scriptBuilder):
        self._scriptBuilder = scriptBuilder
        self._name = None
        self._export = False

    def export(self):
        self._export = True
        return self

    def name(self, name):
        self._name = name
        return self

    def from_context(self, name):
        builder = self._scriptBuilder.builder
        if not name in builder._ctx.keys():
            raise ValueError('[%s] is not in the context' % name)
        value = builder._ctx[name]
        value = value.replace(builder._ctx['BUILD_DIR'], '$HOME')
        line = []
        if self._export:
            line.append('export')
        line.append("%s=%s" % (name, value))
        self._scriptBuilder.manual(' '.join(line))
        return self._scriptBuilder

    def value(self, value):
        if not self._name:
            raise ValueError('You must specify a name')
        builder = self._scriptBuilder.builder
        if hasattr(value, '__call__'):
            value = value()
        elif value in builder._ctx.keys():
            value = builder._ctx[value]
        value = value.replace(builder._ctx['BUILD_DIR'], '$HOME')
        line = []
        if self._export:
            line.append('export')
        line.append("%s=%s" % (self._name, value))
        self._scriptBuilder.manual(' '.join(line))
        return self._scriptBuilder


class Builder(object):
    def __init__(self):
        self._installer = None
        self._ctx = None

    def configure(self):
        self._ctx = CloudFoundryUtil.initialize()
        return Configurer(self)

    def install(self):
        return Installer(self)

    def run(self):
        return Runner(self)

    def execute(self):
        return Executor(self)

    def create_start_script(self):
        return StartScriptBuilder(self)

    def detect(self):
        return Detecter(self)

    def copy(self):
        return FileUtil(self)

    def move(self):
        return FileUtil(self, move=True)

    def release(self):
        print 'default_process_types:'
        print '  web: %s' % self._ctx.get('START_SCRIPT_NAME',
                                          '$HOME/start.sh')
