import unittest

from pychmlib.chm import loadCHM 

class CHMFile1Test(unittest.TestCase):
    "test cases for CHMFile"
    
    def setUp(self):
        self.chm = loadCHM("chm_files/CHM-example.chm")
        
    def test_itsf(self):
        itsf = self.chm.itsf
        self.assertEquals(3,itsf.version)
        self.assertEquals(96,itsf.length)
        self.assertEquals(1031,itsf.lang_id)
        self.assertEquals(120,itsf.dir_offset)
        self.assertEquals(4180,itsf.dir_length)
        self.assertEquals(4300,itsf.data_offset)
    
    def test_itsp(self):
        itsp = self.chm.itsp
        self.assertEquals(1,itsp.version)
        self.assertEquals(84,itsp.length)
        self.assertEquals(4096,itsp.dir_block_length)
        self.assertEquals(1,itsp.index_depth)
        self.assertEquals(-1,itsp.index_root)
        self.assertEquals(0,itsp.first_pmgl_block)
        self.assertEquals(0,itsp.last_pmgl_block)
        
    def test_encoding(self):
        self.assertEquals("iso-8859-1",self.chm.encoding)
        
    def test_pmgi(self):
        self.assertEquals(None,self.chm.pmgi)
        
    def test_lrt(self):
        lrt = self.chm.lrt
        self.assertEquals(32768,lrt.block_length)
        self.assertEquals(16,len(lrt.block_addresses))
        
    def test_clcd(self):
        clcd = self.chm.clcd
        self.assertEquals(2,clcd.version)
        self.assertEquals(2,clcd.reset_interval)
        self.assertEquals(65536,clcd.window_size)
        
    def tearDown(self):
        self.chm.close()


class CHMFile2Test(unittest.TestCase):
    "test cases for CHMFile"
    
    def setUp(self):
        self.chm = loadCHM("chm_files/iexplore.chm")
        
    def test_itsf(self):
        itsf = self.chm.itsf
        self.assertEquals(3,itsf.version)
        self.assertEquals(96,itsf.length)
        self.assertEquals(1033,itsf.lang_id)
        self.assertEquals(120,itsf.dir_offset)
        self.assertEquals(12372,itsf.dir_length)
        self.assertEquals(12492,itsf.data_offset)
    
    def test_itsp(self):
        itsp = self.chm.itsp
        self.assertEquals(1,itsp.version)
        self.assertEquals(84,itsp.length)
        self.assertEquals(4096,itsp.dir_block_length)
        self.assertEquals(2,itsp.index_depth)
        self.assertEquals(2,itsp.index_root)
        self.assertEquals(0,itsp.first_pmgl_block)
        self.assertEquals(1,itsp.last_pmgl_block)
        
    def test_encoding(self):
        self.assertEquals("iso-8859-1",self.chm.encoding)
        
    def test_pmgi(self):
        entries = self.chm.pmgi.entries
        self.assertEquals(2,len(entries))
        self.assertEquals("/", entries[0][0])
        self.assertEquals(0, entries[0][1])
        self.assertEquals("/infobar.jpg", entries[1][0])
        self.assertEquals(1,entries[1][1])
        
    def test_lrt(self):
        lrt = self.chm.lrt
        self.assertEquals(32768,lrt.block_length)
        self.assertEquals(73,len(lrt.block_addresses))
        
    def test_clcd(self):
        clcd = self.chm.clcd
        self.assertEquals(2,clcd.version)
        self.assertEquals(2,clcd.reset_interval)
        self.assertEquals(65536,clcd.window_size)
        
    def tearDown(self):
        self.chm.close()


if __name__ == "__main__":
    unittest.main()