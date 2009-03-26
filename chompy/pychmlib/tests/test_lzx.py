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

import unittest
import struct

from util import *

load_modules()

from lzx import create_lzx_block

class LZXTest(unittest.TestCase):
        
    def test_lzx_1(self):
        data = read_file(get_filename("lzx_files/lzx_1"))
        block = create_lzx_block(block_no=50, window=65536, bytes=data, block_length=32768)
        self.assert_lzx_content(block.content, "lzx_files/lzx_1_content")
        
    def test_lzx_2(self):
        data = read_file(get_filename("lzx_files/lzx_1"))
        prev = create_lzx_block(block_no=50, window=65536, bytes=data, block_length=32768)
        data = read_file(get_filename("lzx_files/lzx_2"))
        block = create_lzx_block(block_no=51, window=65536, bytes=data, block_length=32768, prev_block=prev)
        self.assert_lzx_content(block.content, "lzx_files/lzx_2_content")
        
    def assert_lzx_content(self, actual, filename):
        expected = read_file(get_filename(filename))
        self.assertEquals(len(expected),len(actual))
        expected = struct.unpack("B"*len(expected), expected)
        self.assertEquals(list(expected), actual)


if __name__ == "__main__":
    unittest.main()