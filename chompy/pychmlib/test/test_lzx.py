import unittest
from pychmlib.lzx import create_lzx_block

class LZXTest(unittest.TestCase):
        
    def test_lzx_1(self):
        data = open_file("lzx_files/lzx_1")
        block = create_lzx_block(block_no=50, window=65536, bytes=data, block_length=32768)

def open_file(filename):
    f = open(filename, "rb")
    try:
        return f.read()
    finally:
        f.close()


if __name__ == "__main__":
    unittest.main()