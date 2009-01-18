import unittest
import struct
from pychmlib.chm import _get_encint
from pychmlib.chm import _itsp, _itsf, SegmentError


class CHMTest(unittest.TestCase):
    
    def test_get_encint(self):
        encint,traversed = _get_encint('\007', 0)
        self.assertEquals(7, encint)
        self.assertEquals(1, traversed)
        encint,traversed = _get_encint('\xFD\007', 0)
        self.assertEquals(16007, encint)
        self.assertEquals(2, traversed)

class ITSPTest(unittest.TestCase):
    
    def test_invalid_segment(self):
        self.assertRaises(SegmentError,_itsp,'\x09\x01\x00\x00')
        
    def test_valid_segment(self):
        fmt = 'B '* 84

class ITSFTest(unittest.TestCase):
    
    def test_invalid_segment(self):
        self.assertRaises(SegmentError,_itsf,'\x09\x01\x00\x00')
        
    def test_valid_segment(self):
        fmt = 'B '* 96
        data = struct.pack(fmt,73, 84, 83, 70, 3, 0, 0, 0, 96, 0, 0, 0,
                            1, 0, 0, 0, 253, 5, 23, 136, 7, 4, 0, 0, 
                            16, 253, 1, 124, 170, 123, 208, 17, 158, 12, 0, 160, 
                            201, 34, 230, 236, 17, 253, 1, 124, 170, 123, 208, 17,
                            158, 12, 0, 160, 201, 34, 230, 236, 96, 0, 0, 0,
                            0, 0, 0, 0, 24, 0, 0, 0, 0, 0, 0, 0, 120, 0, 0, 0, 0,
                            0, 0, 0, 84, 16, 0, 0, 0, 0, 0, 0, 204, 16, 0, 0, 0, 0, 0, 0)
        itsf = _itsf(data)
        self.assertEquals(3,itsf.version)
        self.assertEquals(96,itsf.length)
        self.assertEquals(1031,itsf.lang_id)
        self.assertEquals(120,itsf.dir_offset)
        self.assertEquals(4180,itsf.dir_length)
        self.assertEquals(4300,itsf.data_offset)
        

if __name__ == "__main__":
    unittest.main()