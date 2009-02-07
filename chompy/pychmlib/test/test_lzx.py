import unittest
import struct
from pychmlib.lzx import create_lzx_block

class LZXTest(unittest.TestCase):
    
    def setUp(self):
        fmt = 'b '* 67
        data = struct.pack(fmt,16,
                16, 0, 0, 0, 0, 2, 0, 0, 19, 0, 0, 49, 0, 62, 42, -93, -124,
                -96, -23, -67, -88, 33, -18, 94, 94, -117, 11, -9, -34, 111,
                -68, 19, 34, 72, -22, -63, -117, 79, 31, 41, -86, -96, 20, 82,
                -91, 21, 85, -110, 72, 18, -91, -86, 84, 85, 82, 70, 21, -120,
                0, 104, 68, 0, -83, 0, 0, 29)
        self.block = create_lzx_block(1, 65536, data, 32768)
        
    def test_block_no(self):
        self.assertEquals(1,self.block.block_no)


if __name__ == "__main__":
    unittest.main()