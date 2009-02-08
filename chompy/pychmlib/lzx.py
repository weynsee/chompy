import struct

_NUM_CHARS = 256

_LZX_PRETREE_MAXSYMBOLS = 20
_LZX_PRETREE_NUM_ELEMENTS_BITS = 4
_LZX_PRETREE_TABLEBITS = 6

_LZX_MAINTREE_TABLEBITS = 12
_LZX_MAINTREE_MAXSYMBOLS = _NUM_CHARS + 50 * 8

_NUM_SECONDARY_LENGTHS = 249
_LZX_LENGTH_TABLEBITS = 12
_LZX_LENGTH_MAXSYMBOLS = _NUM_SECONDARY_LENGTHS + 1

_LZX_NUM_PRIMARY_LENGTHS = 7

_MIN_MATCH = 2

_EXTRA_BITS = [ 0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4,
            5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13, 14,
            14, 15, 15, 16, 16, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17,
            17, 17, 17 ]

_POSITION_BASE = [ 0, 1, 2, 3, 4, 6, 8, 12, 16, 24,
            32, 48, 64, 96, 128, 192, 256, 384, 512, 768, 1024, 1536, 2048,
            3072, 4096, 6144, 8192, 12288, 16384, 24576, 32768, 49152, 65536,
            98304, 131072, 196608, 262144, 393216, 524288, 655360, 786432,
            917504, 1048576, 1179648, 1310720, 1441792, 1572864, 1703936,
            1835008, 1966080, 2097152 ]

class _LzxBlock:
    
    def __init__(self):
        self.content_length = 0
        self.lzx_state = _LzxState()
    
class _LzxState:
    
    def __init__(self):
        self.block_length = 0
        self.block_remaining = 0
        self.type = None
        self.intel_file_size = 0
        self.header_read = False
        self.intel_started = False
        self.R0 = 1
        self.R1 = 1
        self.R2 = 1
        
class _BitBuffer:
    
    def __init__(self, bytes):
        self.left = 0
        self.value = 0
        self.bytes = bytes
        self.length = len(bytes)
        self.traversed = 0
        
    def read_bits(self, get_bits, remove_bits=None):
        if remove_bits is None:
            remove_bits = get_bits
        while self.left < 16:
            self.value = (self.value << 16) + self.pop() + (self.pop() << 8)
            self.left += 16
        temp = self.value >> (self.left - get_bits)
        self.left -= remove_bits
        t = self.value >> self.left
        self.value -= (t << self.left)
        return temp
    
    def pop(self):
        if self.traversed < self.length:
            val, = struct.unpack("B", self.bytes[self.traversed])
            self.traversed += 1
            return val
        else:
            return 0
    
    def check_bit(self, i):
        n = 1 << (self.left - i)
        if (self.value & n) == 0:
            return 0
        return 1
        

def create_lzx_block(block_no, window, bytes, block_length, prev_block=None):
    block = _create_empty_block(window)
    block.block_no = block_no
    if prev_block is None:
        prev_block = _create_empty_block(window)
    lzx_state = prev_block.lzx_state
    if lzx_state.block_length > lzx_state.block_remaining:
        prev_content = prev_block.content
    buf = _BitBuffer(bytes)
    if not lzx_state.header_read:
        lzx_state.header_read = True
        if buf.read_bits(1) == 1:
            lzx_state.intel_file_size = (buf.read_bits(16) << 16) + buf.read_bits(16) 
    while block.content_length < block_length:
        if lzx_state.block_remaining == 0:
            lzx_state.type = buf.read_bits(3)
            assert lzx_state.type == 1 #can't handle anything but verbatim
            lzx_state.block_length = (buf.read_bits(16) << 8) + buf.read_bits(8)
            lzx_state.block_remaining = lzx_state.block_length
            lzx_state._main_tree_table = _create_main_tree_table(lzx_state, buf)
            lzx_state._length_tree_table = _create_length_tree_table(lzx_state, buf)
            if lzx_state._main_tree_length_table[0xe8] != 0:
                lzx_state.intel_started = True
            break
        if block.content_length + lzx_state.block_remaining > block_length:
            lzx_state.block_remaining = block.content_length + lzx_state.block_remaining - block_length
            length = block_length
        else:
            length = block.content_length + lzx_state.block_remaining
            lzx_state.block_remaining = 0
        _decompress_verbatim_block(lzx_state, block.content_length, buf, length, block_length, prev_content)
        block.content_length = length
    return block

def _get_main_tree_index(buf, main_bits, tree_table, main_max_symbol):
    f = buf.read_bits(main_bits, 0)
    z = tree_table[f]
    if z >= main_max_symbol:
        x = main_bits
        while True:
            x += 1
            z <<= 1
            z += buf.check_bit(x)
            z = pre_tree_table[z]
            if z < main_max_symbol:
                break
    return z

def _decompress_verbatim_block(lzx_state, content_length, buf, length, block_length, prev_content):
    main_tree = lzx_state._main_tree_table
    main_tree_length = lzx_state._main_tree_length_table
    length_tree = lzx_state._length_tree_table
    length_tree_length = lzx_state._length_tree_length_table
    R0 = lzx_state.R0
    R1 = lzx_state.R1
    R2 = lzx_state.R2
    content = []
    i = content_length
    while i < length:
        s = _get_main_tree_index(buf, _LZX_MAINTREE_TABLEBITS, main_tree, lzx_state._main_tree_elements) 
        buf.read_bits(main_tree_length[s])
        if s < _NUM_CHARS:
            content.append(s)
        else:
            s -= _NUM_CHARS
            match_length = s & _LZX_NUM_PRIMARY_LENGTHS
            if match_length == _LZX_NUM_PRIMARY_LENGTHS:
                match_footer = _get_main_tree_index(buf, _LZX_LENGTH_TABLEBITS, length_tree, _NUM_SECONDARY_LENGTHS)
                buf.read_bits(main_tree_length[match_footer])
                match_length += match_footer
            match_length += _MIN_MATCH
            match_offset = s >> 3
            if match_offset > 2:
                if match_offset != 3:
                    extra = _EXTRA_BITS[match_offset]
                    l = buf.read_bits(extra)
                    match_offset = _POSITION_BASE[matcho_ffset] - 2 + l
                else:
                    match_offset = 1
                R2 = R1
                R1 = R0
                R0 = match_offset
            elif match_offset == 0:
                match_offset = R0
            elif match_offset == 1:
                match_offset = R1
                R1 = R0
                R0 = match_offset
            else:
                match_offset = R2
                R2 = R0
                R0 = match_offset
            run_dest = i
            run_src = run_dest - match_offset
            i += (match_length - 1)
            if i > len:
                break
            if run_src < 0:
                if match_length + run_src <= 0:
                    run_src += len(prev_content)
                    while match_length > 0:
                        match_length -= 1
                        content[run_dest] = prev_content[run_src]
                        run_dest += 1
                        run_src += 1
                else:
                    prev_content_length = len(prev_content) 
                    run_src += prev_content_length
                    while run_src < prev_content_length:
                        content[run_dest] = prev_content[run_src]
                        run_dest += 1
                        run_src += 1
                    match_length = matchlen + run_src - prev_content_length
                    run_src = 0
                    while match_length > 0:
                        match_length -= 1
                        content[run_dest] = content[run_src]
                        run_dest += 1
                        run_src += 1
            else:
                while (run_src < 0) and (match_length > 0):
                    content[run_dest] = content[run_src + block_length]
                    run_dest += 1
                    match_length -= 1
                    run_src += 1
                while match_length > 0:
                    match_length -= 1
                    content[run_dest] = content[run_src]
                    run_dest += 1
                    run_src += 1
    if length == block_length:
        lzx_state.R0 = R0
        lzx_state.R1 = R1
        lzx_state.R2 = R2

def _create_length_tree_table(lzx_state, buf):
    pre_length_table = _create_pre_length_table(buf)
    pre_tree_table = _create_pre_tree_table(pre_length_table,
                (1 << _LZX_PRETREE_TABLEBITS) + (_LZX_PRETREE_MAXSYMBOLS << 1),
                _LZX_PRETREE_TABLEBITS, _LZX_PRETREE_MAXSYMBOLS)
    _init_tree_length_table(lzx_state._length_tree_length_table, buf, 0, _NUM_SECONDARY_LENGTHS,
                             pre_tree_table, pre_length_table)
    return _create_pre_tree_table(lzx_state._length_tree_length_table,
                (1 << _LZX_LENGTH_TABLEBITS) + (_LZX_LENGTH_MAXSYMBOLS << 1),
                _LZX_LENGTH_TABLEBITS, _NUM_SECONDARY_LENGTHS)

def print_tree(tree):
    for t in xrange(len(tree)):
        print str(t)+"    "+str(tree[t])

def _create_main_tree_table(lzx_state, buf):
    pre_length_table = _create_pre_length_table(buf)
    pre_tree_table = _create_pre_tree_table(pre_length_table,
                (1 << _LZX_PRETREE_TABLEBITS) + (_LZX_PRETREE_MAXSYMBOLS << 1),
                _LZX_PRETREE_TABLEBITS, _LZX_PRETREE_MAXSYMBOLS)
    _init_tree_length_table(lzx_state._main_tree_length_table, buf, 0, _NUM_CHARS, pre_tree_table, pre_length_table)
    pre_length_table = _create_pre_length_table(buf)
    pre_tree_table = _create_pre_tree_table(pre_length_table,
                (1 << _LZX_PRETREE_TABLEBITS) + (_LZX_PRETREE_MAXSYMBOLS << 1),
                _LZX_PRETREE_TABLEBITS, _LZX_PRETREE_MAXSYMBOLS)
    _init_tree_length_table(lzx_state._main_tree_length_table, buf, _NUM_CHARS,
                            lzx_state._main_tree_elements, pre_tree_table, pre_length_table)
    return _create_pre_tree_table(lzx_state._main_tree_length_table,
                (1 << _LZX_MAINTREE_TABLEBITS) + (_LZX_MAINTREE_MAXSYMBOLS << 1),
                _LZX_MAINTREE_TABLEBITS, lzx_state._main_tree_elements)

def _init_tree_length_table(table, buf, counter, table_length, pre_tree_table, pre_length_table):
    while counter < table_length:
        z = _get_main_tree_index(buf, _LZX_PRETREE_TABLEBITS, pre_tree_table, _LZX_PRETREE_MAXSYMBOLS)
        buf.read_bits(pre_length_table[z])
        if z < 17:
            z = table[counter] - z
            if (z < 0):
                z += 17
            table[counter] = z
            counter += 1
        elif z == 17:
            y = buf.read_bits(4)
            y += 4
            for j in xrange(y):
                table[counter] = 0
                counter += 1
        elif z == 18:
            y = buf.read_bits(5)
            y += 20
            for j in xrange(y):
                table[counter] = 0
                counter += 1
        elif z == 19:
            y = buf.read_bits(1)
            y += 4
            z = _get_main_tree_index(buf, _LZX_PRETREE_TABLEBITS, pre_tree_table, _LZX_PRETREE_MAXSYMBOLS)
            buf.read_bits(pre_length_table[z])
            z = table[counter] - z
            if z < 0:
                z += 17
            for j in xrange(y):
                table[counter] = z
                counter += 1 
    
def _create_pre_tree_table(length_table, table_length, bits, max_symbol):
    bit_num = 1
    pos = 0
    table_mask = 1 << bits
    bit_mask = table_mask >> 1
    next_symbol = bit_mask
    tmp = [0 for x in xrange(table_length)]
    while bit_num <= bits:
        for x in xrange(max_symbol):
            if (length_table[x] == bit_num):
                leaf = pos
                pos += bit_mask
                assert pos <= table_mask, "invalid state"
                fill = bit_mask
                while (fill > 0):
                    fill -= 1
                    tmp[leaf] = x
                    leaf += 1
        bit_mask >>= 1
        bit_num += 1
    if pos != table_mask:
        for x in xrange(pos, table_mask):
            tmp[x] = 0
        pos <<= 16
        table_mask <<= 16
        bit_mask = 1 << 15
        while bit_num <= 16:
            for i in xrange(max_symbol):
                if length_table[i] == bit_num:
                    leaf = pos >> 16
                    for j in xrange(bit_num - bits):
                        if tmp[leaf] == 0:
                            tmp[(next_symbol << 1)] = 0
                            tmp[(next_symbol << 1) + 1] = 0
                            next_symbol += 1
                            tmp[leaf] = next_symbol
                        leaf = tmp[leaf] << 1
                        if ((pos >> (15 - j)) & 1) != 0:
                            leaf += 1
                    tmp[leaf] = i
                    pos += bit_mask
                    assert pos <= table_mask, "invalid state"
            bit_mask >>= 1
            bit_num += 1
    if pos == table_mask:
        return tmp
    return tmp

def _create_pre_length_table(buf):
    return [buf.read_bits(_LZX_PRETREE_NUM_ELEMENTS_BITS) for i in xrange(_LZX_PRETREE_MAXSYMBOLS)]

def _create_empty_block(win):
    window = 0
    while (win > 1):
        win >>= 1
        window += 1
    if window < 15 or window > 21:
        window = 16
    if window == 21:
        num_pos_slots = 50
    elif window == 20:
        num_pos_slots = 42
    else:
        num_pos_slots = window << 1
    block = _LzxBlock()
    lzx_state = block.lzx_state
    lzx_state._main_tree_elements = _NUM_CHARS + num_pos_slots * 8
    lzx_state._main_tree_length_table = [0 for i in xrange(lzx_state._main_tree_elements)]
    lzx_state._length_tree_length_table = [0 for i in xrange(_NUM_SECONDARY_LENGTHS)]
    block.content_length = 0
    return block