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
from build_pack_utils import Builder
import sys

(Builder()
     .configure()  # noqa
         .default_config()
         .user_config(step='detect')
         .done()
     .detect()
         .find_composer_path()
         .if_found_output('php ' + sys.argv[2])
         .when_not_found_continue()
         .done()
     .detect()
         .ends_with(".php")
         .recursive()
         .if_found_output('php ' + sys.argv[2])
         .when_not_found_continue()
         .done()
     .detect()
        .by_name('{WEBDIR}')
        .if_found_output('php ' + sys.argv[2])
        .done())
