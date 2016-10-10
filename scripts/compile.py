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
from datetime import datetime
from build_pack_utils import Builder
from compile_helpers import setup_webdir_if_it_doesnt_exist
from compile_helpers import setup_log_dir
from compile_helpers import log_bp_version


if __name__ == '__main__':
    (Builder()
        .configure()
            .default_config()  # noqa
            .stack_config()
            .user_config()
            .validate()
            .done()
        .execute()
            .method(log_bp_version)
        .execute()
            .method(setup_webdir_if_it_doesnt_exist)
        .execute()
            .method(setup_log_dir)
        .register()
            .extension()
                .from_build_pack('lib/{WEB_SERVER}')
            .extension()
                .from_build_pack('lib/php')
            .extension()
                .from_build_pack('lib/env')
            .extensions()
                .from_build_pack('extensions')
            .extensions()
                .from_application('.extensions')
            .extension()
                .from_build_pack('lib/additional_commands')
            .done()
        .install()
            .build_pack_utils()
            .extensions()
            .done()
        .copy()
            .under('{BP_DIR}/bin')
            .into('{BUILD_DIR}/.bp/bin')
            .where_name_is('rewrite')
            .where_name_is('start')
            .any_true()
            .done()
        .save()
            .runtime_environment()
            .process_list()
            .done()
        .create_start_script()
            .using_process_manager()
            .write())

    print 'Finished: [%s]' % datetime.now()
