from __future__ import generators, nested_scopes
from struct import unpack, pack

import lzx

_CHARSET_TABLE = { 
    0x0804:"gbk",
    0x0404:"big5",
    0xc04:"big5",
    0x0401:"iso-8859-6",
    0x0405:"ISO-8859-2",
    0x0408:"ISO-8859-7",
    0x040D:"ISO-8859-8",
    0x0411:"euc-jp",
    0x0412:"euc-kr",
    0x0419:"ISO-8859-5",
    0x041F:"ISO-8859-9"       
}

_ITSF_MAX_LENGTH = 0x60
_ITSP_MAX_LENGTH = 0x54
_RESET_TABLE = "::DataSpace/Storage/MSCompressed/Transform/{7FC28940-9D31-11D0-9B27-00A0C91E9C7C}/InstanceData/ResetTable"
_CONTENT = "::DataSpace/Storage/MSCompressed/Content"
_LZXC_CONTROLDATA = "::DataSpace/Storage/MSCompressed/ControlData"


class _CHMFile:
    "a class to manage access to CHM files"
    
    def __init__(self, filename):
        self.filename = filename
        self.file = open(filename, "rb")
        self._parse_chm()
        
    def _parse_chm(self):
        try:
            self.itsf = self._get_ITSF()
            self.encoding = self._get_encoding()
            self.itsp = self._get_ITSP()
            self._dir_offset = self.itsf.dir_offset + self.itsp.length;
            self.pmgi = self._get_PMGI()
            entry = self.resolve_object(_RESET_TABLE)
            self.lrt = self._get_LRT(entry)
            entry = self.resolve_object(_CONTENT)
            self._lzx_block_length = entry.length
            self._lzx_block_offset = entry.offset + self.itsf.data_offset
            entry = self.resolve_object(_LZXC_CONTROLDATA)
            self.clcd = self._get_CLCD(entry)
        except:
            #in case of errors, close file as it will not be used again
            self.file.close()
            raise
        
    def enumerate_files(self, condition=None):
        pmgl = self._get_PMGL(self.itsp.first_pmgl_block)
        while pmgl:
            for ui in pmgl.entries():
                if condition and condition(ui):
                    yield ui
                elif not condition:
                    yield ui
            pmgl = self._get_PMGL(pmgl.next_block)
            
    def content_files(self):
        def content_only(ui):
            name = ui.name
            if name.startswith("/") and len(name) > 1 and not(name.startswith("/#") or name.startswith("/$")):
                return True
        return self.enumerate_files(content_only)
    
    def get_hhc(self):
        def hhc_only(ui):
            name = ui.name
            if name.endswith(".hhc"):
                return True
        for content in self.enumerate_files(hhc_only):
            return content
        return None
    
    def all_files(self):
        return self.enumerate_files()
    
    def retrieve_object(self, unit_info):
        return unit_info.get_content()
        
    def resolve_object(self, filename):
        filename = filename.lower()
        start = self.itsp.first_pmgl_block
        stop = self.itsp.last_pmgl_block
        if self.pmgi:
            entries = self.pmgi.entries
            for name, block in entries:
                if filename <= name:
                    start = block - 1
                    break
            else:
                start = len(entries) - 1
        while True:
            pmgl = self._get_PMGL(start)
            for ui in pmgl.entries():
                if filename == ui.name:
                    return ui
            else:
                if start == stop:
                    return None
                else:
                    start = pmgl.next_block
                           
    def _get_PMGL(self, start):
        if (start == - 1):
            return None
        return self._pmgl(self._get_segment(self._dir_offset + start * self.itsp.dir_block_length, self.itsp.dir_block_length))  
        
    def _get_encoding(self):
        lang_id = self.itsf.lang_id
        return _CHARSET_TABLE.get(lang_id, "iso-8859-1")
    
    def _get_PMGI(self):
        if self.itsp.index_depth == 2:
            return self._pmgi(self._get_segment(self._dir_offset + self.itsp.index_root * 
                                          self.itsp.dir_block_length, self.itsp.dir_block_length))
        else:
            return None
        
    def _get_LRT(self, entry):
        return self._lrt(self._get_segment(self.itsf.data_offset + entry.offset, entry.length))
    
    def _get_CLCD(self, entry):
        return self._clcd(self._get_segment(self.itsf.data_offset + entry.offset, entry.length))
        
    def _get_ITSF(self):
        return self._itsf(self._get_segment(0, _ITSF_MAX_LENGTH))
    
    def _get_ITSP(self):
        offset = self.itsf.dir_offset
        return self._itsp(self._get_segment(offset, _ITSP_MAX_LENGTH))
    
    def _get_segment(self, start, length):
        self.file.seek(start)
        return self.file.read(length)
    
    def _itsf(self, segment):
        section = _Section()
        fmt = "<i i 4x 4x l 16x 16x 16x l 4x l 4x"
        section.version, section.length, section.lang_id, \
        section.dir_offset, section.dir_length = unpack(fmt, segment[4:88])
        if section.version == 3:
            section.data_offset, = unpack("<l 4x", segment[88:96])
        else:
            section.data_offset = section.dir_offset + section.dir_length
        return section
    
    def _itsp(self, segment):
        section = _Section()
        fmt = "<i i 4x l 4x i i i i"
        section.version, section.length, section.dir_block_length, \
        section.index_depth, section.index_root, section.first_pmgl_block, \
        section.last_pmgl_block = unpack(fmt, segment[4:40])
        return section
        
    def _pmgl(self, segment):
        section = _Section()
        fmt = "<l 4x 4x i"
        free_space , section.next_block = unpack(fmt, segment[4:20])
        br = len(segment) - 20 - free_space
        by = segment[20:20 + br]
        def entries():
            pointer = 0
            bytes = by
            bytes_remaining = br
            while bytes_remaining > 0:
                iter_read = 0
                ui = UnitInfo(self)
                name_length, bytes_read = self._get_encint(bytes, pointer);
                pointer += bytes_read
                iter_read += bytes_read
                ui.name = unicode(bytes[pointer:pointer + name_length], 'utf-8').lower()
                pointer += name_length
                iter_read += name_length
                ui.compressed, bytes_read = self._get_encint(bytes, pointer);
                pointer += bytes_read
                iter_read += bytes_read
                ui.offset, bytes_read = self._get_encint(bytes, pointer);
                pointer += bytes_read
                iter_read += bytes_read
                ui.length, bytes_read = self._get_encint(bytes, pointer);
                pointer += bytes_read
                iter_read += bytes_read
                bytes_remaining -= iter_read
                yield ui
        section.entries = entries
        return section
        
    def _pmgi(self, segment):
        section = _Section()
        fmt = "<l"
        free_space = unpack(fmt, segment[4:8])[0] 
        bytes_remaining = len(segment) - 8 - free_space
        bytes = segment[8:8 + bytes_remaining]
        pointer = 0
        entries = []
        while bytes_remaining > 0:
            iter_read = 0
            name_length, bytes_read = self._get_encint(bytes, pointer);
            pointer += bytes_read
            iter_read += bytes_read
            name = unicode(bytes[pointer:pointer + name_length], 'utf-8').lower()
            pointer += name_length
            iter_read += name_length
            block, bytes_read = self._get_encint(bytes, pointer);
            pointer += bytes_read
            iter_read += bytes_read
            bytes_remaining -= iter_read
            entries.append((name, block))
        section.entries = entries
        return section
    
    def _lrt(self, segment):
        section = _Section()
        blocks = (len(segment) - 40) / 8
        fmt = "<32x l 4x " + ("l 4x " * blocks) 
        result = unpack(fmt, segment)
        section.block_length = result[0]
        section.block_addresses = result[1:]
        return section
    
    def _clcd(self, segment):
        section = _Section()
        fmt = "<4x 4x l l l 4x 4x" 
        section.version, section.reset_interval, section.window_size = unpack(fmt, segment)
        if section.version == 2:
            section.window_size = section.window_size * 0x8000;
        return section

    def _get_encint(self, bytes, start):
        pointer = start
        byte = ord(bytes[pointer])
        pointer += 1
        bi = 0
        while byte > 127:
            bi = (bi << 7) + (byte & 0x7f)
            byte = ord(bytes[pointer])
            pointer += 1
        bi = (bi << 7) + (byte & 0x7f)
        return bi, pointer - start

    def close(self):
        self.file.close()
        
    __del__ = close

class _Section:
    pass

class UnitInfo:
    
    def __init__(self, chm, name=None, compressed=False, length=0, offset=0):
        self.chm = chm
        self.name = name
        self.compressed = compressed
        self.length = length
        self.offset = offset
    
    def get_content(self):
        if self.compressed == False:
            data = self.chm._get_segment(self.chm.itsf.data_offset + self.offset, self.length)
            return data
        else:
            bytes_per_block = self.chm.lrt.block_length
            start_block = self.offset / bytes_per_block
            end_block = (self.offset + self.length) / bytes_per_block
            start_offset = self.offset % bytes_per_block
            end_offset = (self.offset + self.length) % bytes_per_block
            ini_block = start_block - start_block % self.chm.clcd.reset_interval
            data = [None for i in xrange(end_block - start_block + 1)]
            start = ini_block
            block = self._get_lzx_block(start)
            while start <= end_block:
                if start == start_block and start == end_block:
                    data[0] = block.content[start_offset:end_offset]
                    break
                if start == start_block:
                    data[0] = block.content[start_offset:]
                if start > start_block and start < end_block:
                    data[start - start_block] = block.content
                if start == end_block:
                    data[start - start_block] = block.content[0:end_offset]
                    break
                start += 1
                if start % self.chm.clcd.reset_interval == 0:
                    block = self._get_lzx_block(start)
                else:
                    block = self._get_lzx_block(start, block)
            byte_list = self._flatten(data)
            return pack("B" * len(byte_list), *byte_list)
    
    def _get_lzx_segment(self, block):
        addresses = self.chm.lrt.block_addresses
        if block < len(addresses) - 1:
            length = addresses[block + 1] - addresses[block]
        else:
            length = self.chm._lzx_block_length - addresses[block]
        return self.chm._get_segment(self.chm._lzx_block_offset + addresses[block], length)
    
    def _get_lzx_block(self, block_no, prev_block=None):
        return lzx.create_lzx_block(block_no, self.chm.clcd.window_size,
                                    self._get_lzx_segment(block_no),
                                    self.chm.lrt.block_length, prev_block)
        
    def _flatten(self, data):
        res = []
        for item in data:
            res.extend(item)
        return res
    
    def __repr__(self):
        return self.name

chm = _CHMFile 