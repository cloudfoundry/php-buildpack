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
import httpd
from build_pack_utils import log_output
from build_pack_utils import Builder

# TODO: Setup x-forwarded-for / x-forwarded-proto support

if __name__ == '__main__':
    (Builder()
        .configure()
            .default_config()
            .user_config()
            .done()
        .install()
            .package('HTTPD')
            .config()
                .from_application('config/httpd')
                .or_from_build_pack('defaults/config/httpd/{HTTPD_VERSION}')
                .to('httpd/conf')
                .done()
            .modules()
                .from_config('httpd/conf')
                .done()
            .done()
        .create_start_script()
            .environment_variable()
                .export()
                .name('LD_LIBRARY_PATH')
                .value('$LD_LIBRARY_PATH:$HOME/php/lib')
            .environment_variable()
                .export()
                .name('HTTPD_SERVER_ADMIN')
                .value('ADMIN_EMAIL')
            .command()
                .run("$HOME/httpd/bin/apachectl")
                .with_argument("-f $HOME/httpd/conf/httpd.conf")
                .with_argument("-k start")
                .with_argument("-DFOREGROUND")
                .done()
            .write())
