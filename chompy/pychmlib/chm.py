from __future__ import generators, nested_scopes
from struct import unpack

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

DEBUG = True

_ITSF_MAX_LENGTH = 0x60
_ITSP_MAX_LENGTH = 0x54
_RESET_TABLE = "::DataSpace/Storage/MSCompressed/Transform/{7FC28940-9D31-11D0-9B27-00A0C91E9C7C}/InstanceData/ResetTable"
_CONTENT = "::DataSpace/Storage/MSCompressed/Content"
_LZXC_CONTROLDATA = "::DataSpace/Storage/MSCompressed/ControlData"

def chm(filename):
    return _CHMFile(filename)

class _CHMFile:
    "a class to manage access to CHM files"
    
    def __init__(self, filename):
        self.filename = filename
        self.file = open(filename, "rb")
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
    
    def all_files(self):
        return self.enumerate_files()
        
    def resolve_object(self, filename):
        filename = filename.lower()
        start = self.itsp.first_pmgl_block
        stop = self.itsp.last_pmgl_block
        if self.pmgi:
            entries = self.pmgi.entries
            for name, block in entries:
                if filename <= name:
                    start = block
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
        return _pmgl(self._get_segment(self._dir_offset + start * self.itsp.dir_block_length, self.itsp.dir_block_length), self)  
        
    def _get_encoding(self):
        lang_id = self.itsf.lang_id
        return _CHARSET_TABLE.get(lang_id, "iso-8859-1")
    
    def _get_PMGI(self):
        if self.itsp.index_depth == 2:
            return _pmgi(self._get_segment(self._dir_offset + self.itsp.index_root * 
                                          self.itsp.dir_block_length, self.itsp.dir_block_length))
        else:
            return None
        
    def _get_LRT(self, entry):
        return _lrt(self._get_segment(self.itsf.data_offset + entry.offset, entry.length))
    
    def _get_CLCD(self, entry):
        return _clcd(self._get_segment(self.itsf.data_offset + entry.offset, entry.length))
        
    def _get_ITSF(self):
        return _itsf(self._get_segment(0, _ITSF_MAX_LENGTH))
    
    def _get_ITSP(self):
        offset = self.itsf.dir_offset
        return _itsp(self._get_segment(offset, _ITSP_MAX_LENGTH))
    
    def _get_segment(self, start, length):
        self.file.seek(start)
        return self.file.read(length)

    def close(self):
        self.file.close()

class _Section:
    pass

class UnitInfo:
    
    def __init__(self, chm):
        self.chm = chm
    
    def get_content(self):
        if self.compression == False:
            return self.chm._get_segment(self.chm.itsf.data_offset + self.offset, self.length)
        else:
            bytes_per_block = self.chm.lrt.block_length
            start_block = self.offset / bytes_per_block
            end_block = (self.offset + self.length) / bytes_per_block
            start_offset = self.offset % bytes_per_block
            end_block = (self.offset + self.length) % bytes_per_block
            ini_block = start_block - start_block % self.chm.clcd.reset_interval
        

class SegmentError(Exception):
    
    def __init__(self, segment_type):
        self.segment_type = segment_type
        
    def __str__(self):
        return "Invalid segment (Expected %s)" % self.segment_type


def _itsf(segment):
    _validate_header(segment, "ITSF")
    section = _Section()
    fmt = "<i i 4x 4x l 16x 16x 16x l 4x l 4x"
    section.version, section.length, section.lang_id, \
    section.dir_offset, section.dir_length = unpack(fmt, segment[4:88])
    if section.version == 3:
        section.data_offset, = unpack("<l 4x", segment[88:96])
    else:
        section.data_offset = section.dir_offset + section.dir_length
    return section
    
def _itsp(segment):
    _validate_header(segment, "ITSP")
    section = _Section()
    fmt = "<i i 4x l 4x i i i i"
    section.version, section.length, section.dir_block_length, \
    section.index_depth, section.index_root, section.first_pmgl_block, \
    section.last_pmgl_block = unpack(fmt, segment[4:40])
    return section
    
def _pmgl(segment,chm):
    _validate_header(segment, "PMGL")
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
            ui = UnitInfo(chm)
            name_length, bytes_read = _get_encint(bytes, pointer);
            pointer += bytes_read
            iter_read += bytes_read
            ui.name = unicode(bytes[pointer:pointer + name_length], 'utf-8').lower()
            pointer += name_length
            iter_read += name_length
            ui.compression, bytes_read = _get_encint(bytes, pointer);
            pointer += bytes_read
            iter_read += bytes_read
            ui.offset, bytes_read = _get_encint(bytes, pointer);
            pointer += bytes_read
            iter_read += bytes_read
            ui.length, bytes_read = _get_encint(bytes, pointer);
            pointer += bytes_read
            iter_read += bytes_read
            bytes_remaining -= iter_read
            yield ui
    section.entries = entries
    return section
    
def _pmgi(segment):
    _validate_header(segment, "PMGI")
    section = _Section()
    fmt = "<l"
    free_space = unpack(fmt, segment[4:8])[0] 
    bytes_remaining = len(segment) - 8 - free_space
    bytes = segment[8:8 + bytes_remaining]
    pointer = 0
    entries = []
    while bytes_remaining > 0:
        iter_read = 0
        name_length, bytes_read = _get_encint(bytes, pointer);
        pointer += bytes_read
        iter_read += bytes_read
        name = unicode(bytes[pointer:pointer + name_length], 'utf-8').lower()
        pointer += name_length
        iter_read += name_length
        block, bytes_read = _get_encint(bytes, pointer);
        pointer += bytes_read
        iter_read += bytes_read
        bytes_remaining -= iter_read
        entries.append((name, block))
    section.entries = entries
    return section

def _lrt(segment):
    section = _Section()
    blocks = (len(segment) - 40) / 8
    fmt = "<32x l 4x " + ("l 4x " * blocks) 
    result = unpack(fmt, segment)
    section.block_length = result[0]
    section.block_addresses = result[1:]
    return section

def _clcd(segment):
    section = _Section()
    fmt = "<4x 4x l l l 4x 4x" 
    section.version, section.reset_interval, section.window_size = unpack(fmt, segment)
    if section.version == 2:
        section.window_size = section.window_size * 0x8000;
    return section
    
def _validate_header(segment, type):
    if DEBUG and segment[:len(type)] != type:
        raise SegmentError(type)

def _get_encint(bytes, start):
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