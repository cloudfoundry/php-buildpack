import os
import subprocess

class CompileExtensions(object):
    def __init__(self, buildpack_dir):
        self._buildpack_dir = buildpack_dir

    def call_compile_extensions_script(self, script, *args):
        process = subprocess.Popen([os.path.join(self._buildpack_dir, 'compile-extensions', 'bin', script)] + list(args), stdout=subprocess.PIPE)
        exit_code = process.wait()
        output = process.stdout.read().rstrip()
        return (exit_code, output)

    def filter_dependency_url(self, url):
        _, filter_output = self.call_compile_extensions_script('filter_dependency_url', url)
        return filter_output

    def translate_dependency_url(self, url):
        exit_code, translate_output = self.call_compile_extensions_script('translate_dependency_url', url)
        return (exit_code, translate_output)

    def default_version_for(self, manifest_file_path, dependency):
        exit_code, default_version = self.call_compile_extensions_script('default_version_for', manifest_file_path, dependency)
        return (exit_code, default_version)

    def download_dependency(self, url, toFile):
        exit_code, default_version = self.call_compile_extensions_script('download_dependency', url, toFile)
        return (exit_code, default_version)








