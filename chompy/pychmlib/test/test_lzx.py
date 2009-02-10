import unittest
import struct
from pychmlib.lzx import create_lzx_block

class LZXTest(unittest.TestCase):
        
    def test_lzx_1(self):
        data = open_file("lzx_files/lzx_1")
        block = create_lzx_block(block_no=50, window=65536, bytes=data, block_length=32768)
        self.assert_lzx_content(block, "lzx_files/lzx_1_content")
        
    def test_lzx_2(self):
        data = open_file("lzx_files/lzx_1")
        prev = create_lzx_block(block_no=50, window=65536, bytes=data, block_length=32768)
        data = open_file("lzx_files/lzx_2")
        block = create_lzx_block(block_no=51, window=65536, bytes=data, block_length=32768, prev_block=prev)
        self.assert_lzx_content(block, "lzx_files/lzx_2_content")
        
    def assert_lzx_content(self, block, filename):
        content = open_file(filename)
        self.assertEquals(len(content),len(block.content))
        content = struct.unpack("B"*len(content), content)
        self.assertEquals(list(content), block.content)


def open_file(filename):
    f = open(filename, "rb")
    try:
        return f.read()
    finally:
        f.close()


if __name__ == "__main__":
    unittest.main()