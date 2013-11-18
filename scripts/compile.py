#!/usr/bin/env python

# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
from build_pack_utils import Builder


def maven_command(cfg):
    mvnCmd = cfg.get('MAVEN_BUILD_COMMAND', 'test')
    mvn = os.path.join(cfg['MAVEN_INSTALL_PATH'], 'bin', 'mvn')
    mvnRepo = os.path.join(cfg['CACHE_DIR'], 'repo')
    pom = os.path.join(cfg['BUILD_DIR'], 'pom.xml')
    return [mvn, '-Dmaven.repo.local=%s' % mvnRepo, '-f', pom, mvnCmd]


def copy_maven_repo_to_droplet(cfg):
    return ['cp', '-R', os.path.join(cfg['CACHE_DIR'], 'repo'), '.']


def log_run(cmd, retcode, stdout, stderr):
    print 'Comand %s completed with [%d]' % (str(cmd), retcode)
    print 'STDOUT:'
    print stdout
    print 'STDERR:'
    print stderr
    if retcode != 0:
        raise RuntimeError('Script Failure')


if __name__ == '__main__':
    (Builder()
        .configure()
            .default_config()
            .user_config()
            .done()
        .install()
            .package('JAVA')
            .package('MAVEN')
            .done()
        .run()
            .command('rm java/src.zip')
            .out_of('BUILD_DIR')
            .done()
        .run()
            .command(maven_command)
            .environment_variable()
                .name('JAVA_HOME')
                .value('JAVA_INSTALL_PATH')
            .out_of('BUILD_DIR')
            .with_shell()
            .on_finish(log_run)
            .done()
        .run()
            .command(copy_maven_repo_to_droplet)
            .out_of('BUILD_DIR')
            .done()
        .create_start_script()
            .environment_variable()
                .export()
                .name('JAVA_HOME')
                .value('JAVA_INSTALL_PATH')
            .environment_variable()
                .export()
                .name('M2_HOME')
                .value('MAVEN_INSTALL_PATH')
            .command()
                .run('$M2_HOME/bin/mvn')
                .with_argument('-Dmaven.repo.local=$HOME/repo')
                .with_argument('MAVEN_RUN_COMMAND')
                .done()
            .write())
