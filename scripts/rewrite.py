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
import sys
import os
from compile_helpers import FakeBuilder
from compile_helpers import FakeInstaller
from build_pack_utils import ConfigInstaller


if len(sys.argv) != 2:
    print 'Argument required!  Specify path to configuration directory.'
    sys.exit(-1)

toPath = sys.argv[1]
if not os.path.exists(toPath):
    print 'Path [%s] not found.' % toPath
    sys.exit(-1)

if not os.path.isdir(toPath):
    print 'Path [%s] is not a directory.' % toPath
    sys.exit(-1)

ctx = {
    'BUILD_DIR': ''
}
ctx.update(os.environ)

ci = ConfigInstaller(FakeInstaller(FakeBuilder(ctx), None))
ci.rewrite(runtime=True)
ci.to(sys.argv[1])
ci.done()
