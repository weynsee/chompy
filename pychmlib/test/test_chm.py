import unittest
import struct

from chm import chm, UnitInfo
from util import * 

class CHMFile1Test(unittest.TestCase):
    "test cases for CHMFile"
    
    def setUp(self):
        self.chm = chm("chm_files/CHM-example.chm")
        
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
        
    def test_enumeration(self):
        self.assertEquals(83,len(list(self.chm.all_files())))
        self.assertEquals(53,len(list(self.chm.content_files())))
        
    def test_unit_info(self):
        ui = self.chm.resolve_object("::DataSpace/Storage/MSCompressed/Transform/{7FC28940-9D31-11D0-9B27-00A0C91E9C7C}/InstanceData/ResetTable")
        self.assertEquals(168,len(ui.get_content()))
        
    def test_retrieve_object(self):
        assert_unit_info(self, self.chm, "/Garden/flowers.htm", "flowers.htm")
        
    def tearDown(self):
        self.chm.close()

class CHMFile2Test(unittest.TestCase):
    "test cases for CHMFile"
    
    def setUp(self):
        self.chm = chm("chm_files/iexplore.chm")
        
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
        
    def test_enumeration(self):
        self.assertEquals(246,len(list(self.chm.all_files())))
        self.assertEquals(218,len(list(self.chm.content_files())))
        
    def test_resolve_object(self):
        assert_unit_info(self, self.chm, "/lock.jpg")
        
    def tearDown(self):
        self.chm.close()

class UnitInfoTest(unittest.TestCase):
    
    def test_hhc_1(self):
        file = chm("chm_files/iexplore.chm")
        ui = UnitInfo(chm=file,name="/iexplore.hhc",compressed=True, length=18256, offset=1671249)
        content = ui.get_content()
        assert_content(self,content, "iexplore.hhc")
        
    def test_hhc_2(self):
        file = chm("chm_files/CHM-example.chm")
        ui = UnitInfo(chm=file,name="/CHM-example.hhc",compressed=True, length=4051, offset=423573)
        content = ui.get_content()
        assert_content(self,content, "CHM-example.hhc")
        
    def test_content_1(self):
        chm_file = chm("chm_files/CHM-example.chm")
        assert_unit_info(self, chm_file, "/design.css")
        assert_unit_info(self, chm_file, "/images/ditzum.jpg", "ditzum.jpg")
        
    def test_content_2(self):
        chm_file = chm("chm_files/iexplore.chm")
        assert_unit_info(self, chm_file, "/DLG_LMZL.htm")
        assert_unit_info(self, chm_file, "/minusHot.GIF")
        
    def save(self, filename, ui):
        f = open("chm_files/"+filename,"wb")
        f.write(ui.get_content())
        f.close()


def assert_unit_info(test, chm_file, entry_name, test_file=None):
    if not test_file:
        test_file = entry_name[1:]
    ui = chm_file.resolve_object(entry_name)
    content = chm_file.retrieve_object(ui)
    assert_content(test, content, test_file)

def assert_content(test, actual, filename):
    expected = read_file("chm_files/"+filename)
    test.assertEquals(len(expected),len(actual))
    test.assertEquals(expected, actual)

if __name__ == "__main__":
    unittest.main()