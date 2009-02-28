import unittest
import struct

from lzx import create_lzx_block
from util import *

class LZXTest(unittest.TestCase):
        
    def test_lzx_1(self):
        data = read_file("lzx_files/lzx_1")
        block = create_lzx_block(block_no=50, window=65536, bytes=data, block_length=32768)
        self.assert_lzx_content(block.content, "lzx_files/lzx_1_content")
        
    def test_lzx_2(self):
        data = read_file("lzx_files/lzx_1")
        prev = create_lzx_block(block_no=50, window=65536, bytes=data, block_length=32768)
        data = read_file("lzx_files/lzx_2")
        block = create_lzx_block(block_no=51, window=65536, bytes=data, block_length=32768, prev_block=prev)
        self.assert_lzx_content(block.content, "lzx_files/lzx_2_content")
        
    def assert_lzx_content(self, actual, filename):
        expected = read_file(filename)
        self.assertEquals(len(expected),len(actual))
        expected = struct.unpack("B"*len(expected), expected)
        self.assertEquals(list(expected), actual)


if __name__ == "__main__":
    unittest.main()