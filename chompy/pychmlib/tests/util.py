# Copyright 2009 Wayne See
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import struct
import os
import sys

def read_file(filename):
    f = open(filename, "rb")
    try:
        return f.read()
    finally:
        f.close()
        
def load_modules():
    parpath = os.path.join(os.path.dirname(sys.argv[0]), os.pardir)
    sys.path.insert(0, os.path.abspath(parpath))
    
def get_filename(filename):
    return os.path.join(os.path.dirname(sys.argv[0]), filename)