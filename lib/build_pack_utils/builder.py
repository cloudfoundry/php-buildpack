import os
import sys
import shutil
import re
import logging
from collections import defaultdict
from StringIO import StringIO
from subprocess import Popen
from subprocess import PIPE
from cloudfoundry import CloudFoundryUtil
from cloudfoundry import CloudFoundryInstaller
from detecter import TextFileSearch
from detecter import ComposerJsonSearch
from detecter import RegexFileSearch
from detecter import StartsWithFileSearch
from detecter import EndsWithFileSearch
from detecter import ContainsFileSearch
from runner import BuildPack
from utils import rewrite_cfgs
from detecter import RegexFileSearch
from detecter import StartsWithFileSearch
from detecter import EndsWithFileSearch
from detecter import ContainsFileSearch
from runner import BuildPack
from utils import rewrite_cfgs
from utils import process_extension
from utils import process_extensions


_log = logging.getLogger('builder')


def log_output(cmd, retcode, stdout, stderr):
    _log.info('Comand %s completed with [%d]', str(cmd), retcode)
    if stdout:
        _log.debug('STDOUT: %s', stdout)
    if stderr:
        _log.error('STDERR: %s', stderr)
    if retcode != 0:
        raise RuntimeError('Script Failure')


class Configurer(object):
    def __init__(self, builder):
        self.builder = builder

    def default_config(self):
        self._merge(
            CloudFoundryUtil.load_json_config_file_from(
                self.builder._ctx['BP_DIR'],
                'defaults/options.json'))
        return self

    def stack_config(self):
        stack = os.environ.get('CF_STACK', None)
        if stack:
            self._merge(
                CloudFoundryUtil.load_json_config_file_from(
                    self.builder._ctx['BP_DIR'],
                    'defaults/%s/options.json' % stack))
        return self

    def user_config(self, path=None, step=None):
        if path is None:
            path = os.path.join('.bp-config', 'options.json')
        self._merge(
            CloudFoundryUtil.load_json_config_file_from(
                self.builder._ctx['BUILD_DIR'], path, step))
        return self

    def validate(self):
        web_server = self.builder._ctx['WEB_SERVER']
        if web_server != 'none' and web_server != 'nginx' and web_server != 'httpd':
            sys.stderr.write("{0} isn't a supported web server. Supported web servers are 'httpd' & 'nginx'\n".format(web_server))
            sys.exit(1)
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
        self._continue = False
        self._output = 'Found'
        self._ctx = builder._ctx
        self._root = builder._ctx['BUILD_DIR']

    def _config(self, detecter):
        detecter.recursive = self._recursive
        detecter.fullPath = self._fullPath
        return detecter

    def with_regex(self, regex):
        regex = self._ctx.format(regex)
        self._detecter = self._config(RegexFileSearch(regex))
        return self

    def by_name(self, name):
        name = self._ctx.format(name)
        self._detecter = self._config(TextFileSearch(name))
        return self

    def starts_with(self, text):
        text = self._ctx.format(text)
        self._detecter = self._config(StartsWithFileSearch(text))
        return self

    def ends_with(self, text):
        text = self._ctx.format(text)
        self._detecter = self._config(EndsWithFileSearch(text))
        return self

    def contains(self, text):
        text = self._ctx.format(text)
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
        self._output = self._ctx.format(text)
        return self

    def find_composer_path(self):
        self._detecter = self._config(ComposerJsonSearch(self._ctx))
        #search for composer.json at that path
        return self

    def when_not_found_continue(self):
        self._continue = True
        return self

    def under(self, root):
        self._root = self._ctx.format(root)
        self.recursive()
        return self

    def at(self, root):
        self._root = self._ctx.format(root)
        return self

    def done(self):
        # calls to sys.exit are expected here and needed to
        #  conform to the requirements of CF's detect script
        #  which must set exit codes
        if self._detecter and self._detecter.search(self._root):
            print self._output
            sys.exit(0)
        elif not self._continue:
            print 'no'
            sys.exit(1)
        else:
            return self._builder


class Installer(object):
    def __init__(self, builder):
        self.builder = builder
        self._log = _log
        self._installer = CloudFoundryInstaller(self.builder._ctx)

    def package(self, key):
        if key in self.builder._ctx.keys():
            key = self.builder._ctx[key]
        self.builder._ctx['%s_INSTALL_PATH' % key] = \
            self._installer.install_binary(key)
        self._log.info("Installed [%s] to [%s]", key,
                       self.builder._ctx['%s_INSTALL_PATH' % key])
        return self

    def packages(self, *keys):
        for key in keys:
            self.package(key)
        return self

    def modules(self, key):
        return ModuleInstaller(self, key)

    def config(self):
        return ConfigInstaller(self)

    def extensions(self):
        ctx = self.builder._ctx
        extn_reg = self.builder._extn_reg

        def process(retcode):
            if retcode != 0:
                raise RuntimeError('Extension Failed with [%s]' % retcode)
        for path in extn_reg._paths:
            process_extension(path, ctx, 'compile', process, args=[self])
        ctx['EXTENSIONS'].extend(extn_reg._paths)
        return self

    def build_pack_utils(self):
        self._log.info("Installed build pack utils.")
        (self.builder.copy()
             .under('{BP_DIR}/lib/build_pack_utils')
             .into('{BUILD_DIR}/.bp/lib/build_pack_utils')
             .done())
        return self

    def build_pack(self):
        return BuildPackManager(self)

    def done(self):
        return self.builder


class Register(object):
    def __init__(self, builder):
        self._builder = builder
        self._builder._extn_reg = ExtensionRegister(builder, self)

    def extension(self):
        return self._builder._extn_reg

    def extensions(self):
        return self._builder._extn_reg

    def done(self):
        def process(resp):
            pass  # ignore result, don't care
        for extn in self._builder._extn_reg._paths:
            process_extension(extn, self._builder._ctx, 'configure', process)
        return self._builder


class ModuleInstaller(object):
    def __init__(self, installer, moduleKey):
        self._installer = installer
        self._ctx = installer.builder._ctx
        self._cf = CloudFoundryInstaller(self._ctx)
        self._moduleKey = moduleKey
        self._extn = ''
        self._modules = []
        self._load_modules = self._default_load_method
        self._regex = None
        self._log = _log

    def _default_load_method(self, path):
        with open(path, 'rt') as f:
            return [line.strip() for line in f]

    def _regex_load_method(self, path):
        modules = []
        with open(path, 'rt') as f:
            for line in f:
                m = self._regex.match(line.strip())
                if m:
                    modules.append(m.group(1))
        return modules

    def filter_files_by_extension(self, extn):
        self._extn = extn
        return self

    def find_modules_with(self, method):
        self._load_modules = method
        return self

    def find_modules_with_regex(self, regex):
        self._regex = re.compile(regex)
        self._load_modules = self._regex_load_method
        return self

    def include_module(self, module):
        self._modules.append(module)
        return self

    def include_modules_from(self, key):
        self._modules.extend(self._ctx.get(key, []))
        return self

    def from_application(self, path):
        fullPath = os.path.join(self._ctx['BUILD_DIR'], path)
        if os.path.exists(fullPath) and os.path.isdir(fullPath):
            for root, dirs, files in os.walk(fullPath):
                for f in files:
                    if f.endswith(self._extn):
                        self._log.debug('Loading modules from [%s]',
                                        os.path.join(root, f))
                        self._modules.extend(
                            self._load_modules(os.path.join(root, f)))
        elif os.path.exists(fullPath) and os.path.isfile(fullPath):
            self._log.debug('Loading modules from [%s]', fullPath)
            self._modules.extend(self._load_modules(fullPath))
        self._modules = list(set(self._modules))
        return self

    def done(self):
        toPath = os.path.join(self._ctx['BUILD_DIR'],
                              self._moduleKey.lower())
        strip = self._ctx.get('%s_MODULES_STRIP' % self._moduleKey, False)
        for module in set(self._modules):
            try:
                self._ctx['MODULE_NAME'] = module
                url = self._ctx['%s_MODULES_PATTERN' % self._moduleKey]
                self._cf._install_binary_from_manifest(url, toPath,
                                               strip=strip)
            except Exception:
                self._log.warning('Module %s failed to install', module)
                self._log.debug('Module %s failed to install because',
                                module, exc_info=True)
            finally:
                if 'MODULE_NAME' in self._ctx.keys():
                    del self._ctx['MODULE_NAME']
        return self._installer


class ExtensionRegister(object):
    def __init__(self, builder, reg):
        self._builder = builder
        self._ctx = builder._ctx
        self._paths = []
        self._reg = reg

    def from_build_pack(self, path):
        return self.from_path(os.path.join(self._ctx['BP_DIR'], path))

    def from_application(self, path):
        return self.from_path(os.path.join(self._ctx['BUILD_DIR'], path))

    def from_path(self, path):
        path = self._ctx.format(path)
        if os.path.exists(path):
            if os.path.exists(os.path.join(path, 'extension.py')):
                self._paths.append(os.path.abspath(path))
            else:
                for p in os.listdir(path):
                    self._paths.append(os.path.abspath(os.path.join(path, p)))
        return self._reg


class ConfigInstaller(object):
    def __init__(self, installer):
        self._installer = installer
        self._cfInst = installer._installer
        self._ctx = installer.builder._ctx
        self._app_path = None
        self._bp_path = None
        self._to_path = None
        self._delimiter = None

    def from_build_pack(self, fromFile):
        self._bp_path = self._ctx.format(fromFile)
        return self

    def or_from_build_pack(self, fromFile):
        self._bp_path = self._ctx.format(fromFile)
        return self

    def from_application(self, fromFile):
        self._app_path = self._ctx.format(fromFile)
        return self

    def to(self, toPath):
        self._to_path = self._ctx.format(toPath)
        return self

    def rewrite(self, delimiter='#'):
        self._delimiter = delimiter
        return self

    def _rewrite_cfgs(self):
        rewrite_cfgs(os.path.join(self._ctx['BUILD_DIR'], self._to_path),
                     self._ctx,
                     delim=self._delimiter)

    def done(self):
        if (self._bp_path or self._app_path) and self._to_path:
            if self._bp_path:
                self._cfInst.install_from_build_pack(self._bp_path,
                                                     self._to_path)
            if self._app_path:
                self._cfInst.install_from_application(self._app_path,
                                                      self._to_path)
        if self._delimiter:
            self._rewrite_cfgs()
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
        self._log = _log

    def done(self):
        if os.path.exists(self._path):
            cwd = os.getcwd()
            try:
                self._log.debug('Running [%s] from [%s] with shell [%s]',
                                self._cmd, self._path, self._shell)
                self._log.debug('Running with env [%s]', self._env)
                os.chdir(self._path)
                proc = Popen(self._cmd, stdout=PIPE, env=self._env,
                             stderr=PIPE, shell=self._shell)
                stdout, stderr = proc.communicate()
                retcode = proc.poll()
                self._log.debug("Command completed with [%s]", retcode)
                if self._on_finish:
                    self._on_finish(self._cmd, retcode, stdout, stderr)
                else:
                    if retcode == 0 and self._on_success:
                        self._on_success(self._cmd, retcode, stdout)
                    elif retcode != 0 and self._on_fail:
                        self._on_fail(self._cmd, retcode, stderr)
                    elif retcode != 0:
                        self._log.error(
                            'Command [%s] failed with [%d], add an '
                            '"on_fail" or "on_finish" method to debug '
                            'further', self._cmd, retcode)
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
            self._path = self._builder._ctx.format(path)
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
        self._match = all
        self._log = _log

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

    def where_name_is(self, name):
        self._filters.append(
            lambda path: os.path.basename(path) == name)
        return self

    def where_name_is_not(self, name):
        self._filters.append(
            lambda path: os.path.basename(path) != name)
        return self

    def where_name_matches(self, pattern):
        if hasattr(pattern, 'strip'):
            pattern = re.compile(pattern)
        self._filters.append(
            lambda path: (pattern.match(path) is not None))
        return self

    def where_name_does_not_match(self, pattern):
        if hasattr(pattern, 'strip'):
            pattern = re.compile(pattern)
        self._filters.append(
            lambda path: (pattern.match(path) is None))
        return self

    def all_true(self):
        self._match = all
        return self

    def any_true(self):
        self._match = any
        return self

    def under(self, path):
        if path in self._builder._ctx.keys():
            self._from_path = self._builder._ctx[path]
        else:
            self._from_path = self._builder._ctx.format(path)
        if not self._from_path.startswith('/'):
            self._from_path = os.path.join(os.getcwd(), self._from_path)
        return self

    def into(self, path):
        if path in self._builder._ctx.keys():
            self._into_path = self._builder._ctx[path]
        else:
            self._into_path = self._builder._ctx.format(path)
        if not self._into_path.startswith('/'):
            self._into_path = os.path.join(self._from_path, self._into_path)
        return self

    def _copy_or_move(self, src, dest):
        dest_base = os.path.dirname(dest)
        if not os.path.exists(dest_base):
            os.makedirs(os.path.dirname(dest))
        if self._move:
            self._log.debug("Moving [%s] to [%s]", src, dest)
            shutil.move(src, dest)
        else:
            self._log.debug("Copying [%s] to [%s]", src, dest)
            shutil.copy(src, dest)

    def done(self):
        if self._from_path and self._into_path:
            self._log.debug('Copying files from [%s] to [%s]',
                            self._from_path, self._into_path)
            if self._from_path == self._into_path:
                raise ValueError("Source and destination paths "
                                 "are the same [%s]" % self._from_path)
            if not os.path.exists(self._from_path):
                raise ValueError("Source path [%s] does not exist"
                                 % self._from_path)
            for root, dirs, files in os.walk(self._from_path.decode('utf-8'),
                                             topdown=False):
                for f in files:
                    fromPath = os.path.join(root, f)
                    toPath = fromPath.replace(self._from_path, self._into_path)
                    if self._match([f(fromPath) for f in self._filters]):
                        self._copy_or_move(fromPath, toPath)
                if self._move:
                    for d in dirs:
                        dirPath = os.path.join(root, d)
                        if len(os.listdir(dirPath)) == 0:
                            self._log.debug(
                                "Cleaning up empty directory [%s]",
                                dirPath)
                            os.rmdir(os.path.join(root, d))
        return self._builder


class StartScriptBuilder(object):
    def __init__(self, builder):
        self.builder = builder
        self.content = []
        self._use_pm = False
        self._debug_console = False
        self._log = _log

    def manual(self, cmd):
        self.content.append(cmd)

    def environment_variable(self):
        return EnvironmentVariableBuilder(self)

    def command(self):
        return ScriptCommandBuilder(self.builder, self)

    def using_process_manager(self):
        self._use_pm = True
        return self

    def on_fail_run_debug_console(self):
        self._debug_console = True
        return self

    def _process_extensions(self):
        def process(cmds):
            for cmd in cmds:
                self.content.append(' '.join(cmd))
        process_extensions(self.builder._ctx, 'preprocess_commands', process)

    def write(self, wait_forever=False):
        if os.path.exists(os.path.join(self.builder._ctx['BUILD_DIR'],
                                       '.bp', 'lib', 'build_pack_utils')):
            self._log.debug("Setting PYTHONPATH to include build pack utils")
            self.content.append('export PYTHONPATH=$HOME/.bp/lib')

        self._process_extensions()

        if self._debug_console:
            self._log.debug("Enabling debug console, if start script fails.")
            self.content.append(
                'curl -s https://raw.github.com/dmikusa-pivotal/'
                'cf-debug-tools/master/debug-console.sh | bash')

        if wait_forever:
            self._log.debug('Adding wait-for-ever to start script')
            self.content.append("while [ 1 -eq 1 ]; do")
            self.content.append("    sleep 100000")
            self.content.append("done")

        scriptName = self.builder._ctx.get('START_SCRIPT_NAME',
                                           'rewrite.sh')
        startScriptPath = os.path.join(
            self.builder._ctx['BUILD_DIR'], '.profile.d', scriptName)
        self._log.debug('Writing start script to [%s]', startScriptPath)
        with open(startScriptPath, 'wt') as out:
            if self.content:
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
        self._log = _log

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
        self._log.debug('Adding command [%s]', ' '.join(cmd))
        self._scriptBuilder.manual(' '.join(cmd))
        return self._scriptBuilder


class EnvironmentVariableBuilder(object):
    def __init__(self, scriptBuilder):
        self._log = _log
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
        if name not in builder._ctx.keys():
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
        value = builder._ctx.format(value)
        value = value.replace(builder._ctx['BUILD_DIR'], '$HOME')
        line = []
        if self._export:
            line.append('export')
        line.append("%s=%s" % (self._name, value))
        self._log.debug('Adding env variable [%s]', ' '.join(line))
        self._scriptBuilder.manual(' '.join(line))
        return self._scriptBuilder


class BuildPackManager(object):
    def __init__(self, builder):
        self._builder = builder
        self._log = _log

    def from_buildpack(self, url):
        self._log.debug('Using build pack [%s]', url)
        self._bp = BuildPack(self._builder._ctx, url)
        return self

    def using_branch(self, branch):
        self._bp._branch = branch
        return self

    def using_stream(self, stream):
        self._bp._stream = stream

    def done(self):
        if self._bp:
            self._bp._clone()
            self._bp._compile()
        return self._builder


class SaveBuilder(object):
    def __init__(self, builder):
        self._builder = builder

    def runtime_environment(self):
        # run service_environment on all extensions, pool the results
        #  into one dict, duplicates are grouped in a list and kept
        #  in the same order.
        all_extns_env = defaultdict(list)

        def process(env):
            for key, val in env.iteritems():
                if hasattr(val, 'append'):
                    all_extns_env[key].extend(val)
                else:
                    all_extns_env[key].append(val)
        process_extensions(self._builder._ctx, 'service_environment', process)
        # Write pool of environment items to disk, a single item is
        #  written in 'key=val' format, while lists are written as
        #  'key=val:val:val' where ':' is os.pathsep.
        profile_d_directory = os.path.join(self._builder._ctx['BUILD_DIR'],
                                           '.profile.d')
        if not os.path.exists(profile_d_directory):
            os.makedirs(profile_d_directory)
        envPath = os.path.join(profile_d_directory, 'bp_env_vars.sh')
        with open(envPath, 'at') as envFile:
            for key, val in all_extns_env.iteritems():
                if len(val) == 0:
                    val = ''
                elif len(val) == 1:
                    val = val[0]
                elif len(val) > 1:
                    val = os.pathsep.join(val)
                envFile.write("export %s=%s\n" % (key, val))
        return self

    def process_list(self):
        def process(cmds):
            procPath = os.path.join(self._builder._ctx['BUILD_DIR'], '.procs')
            with open(procPath, 'at') as procFile:
                for name, cmd in cmds.iteritems():
                    procFile.write("%s: %s\n" % (name, ' '.join(cmd)))
        process_extensions(self._builder._ctx, 'service_commands', process)
        return self

    def done(self):
        return self._builder


class Shell(object):
    EXIT_KEY = '##exit-code##-->'

    def __init__(self, shell='/bin/bash', stream=sys.stdout):
        self._proc = Popen(shell,
                           stdin=PIPE,
                           stdout=PIPE,
                           stderr=PIPE,
                           shell=False)
        self._stream = stream

    def __getattr__(self, name):
        def cmd(*args):
            cmd = '"%s" %s\necho "\n%s$?"\n' % (
                name,
                ' '.join([(arg == '|') and arg or '"%s"' %
                          arg for arg in args]),
                Shell.EXIT_KEY)
            self._proc.stdin.write(cmd)
            for c in iter(lambda: self._proc.stdout.readline(), ''):
                if c.startswith(Shell.EXIT_KEY):
                    return int(c[len(Shell.EXIT_KEY):])
                self._stream.write(c)
        return cmd

    def __getitem__(self, key):
        oldstream = self._stream
        self._stream = StringIO()
        try:
            self.echo("$%s" % key)
            return self._stream.getvalue().strip()
        finally:
            self._stream = oldstream

    def __setitem__(self, key, value):
        cmd = "%s=%s\n" % (key, value)
        self._proc.stdin.write(cmd)

    def __delitem__(self, key):
        cmd = "unset %s" % key
        self._proc.stdin.write(cmd)

    def __contains__(self, key):
        return self[key] != ''


class Builder(object):
    def __init__(self):
        self._installer = None
        self._ctx = None

    def configure(self):
        self._ctx = CloudFoundryUtil.initialize()
        return Configurer(self)

    def install(self):
        return Installer(self)

    def register(self):
        return Register(self)

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

    def shell(self, shell='/bin/bash'):
        return Shell(self, shell=shell)

    def save(self):
        return SaveBuilder(self)

    def release(self):
        print 'default_process_types:'
        print '  web: $HOME/%s' % self._ctx.get('START_SCRIPT_NAME',
                                                '.bp/bin/start')
