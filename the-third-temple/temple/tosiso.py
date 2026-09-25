"""Read files straight out of Terry's TempleOS.ISO.

The ISO holds a RedSea file system. Most files end in .Z: compressed with
TempleOS's own LZW, ::/Kernel/Compress.HC. ArcExpandBuf and ArcEntryGet
are ported below, table reuse and all.

  python3 -m temple.tosiso /path/to/TempleOS.ISO ls
  python3 -m temple.tosiso /path/to/TempleOS.ISO get Demo/Graphics/Elephant.HC out
"""
import struct
import sys

ARC_BITS_MAX = 12
CT_NONE, CT_7_BIT, CT_8_BIT = 1, 2, 3
U32_MAX = 0xFFFFFFFF


def _bits(buf, pos, n):
    b = pos >> 3
    v = int.from_bytes(buf[b:b + 5], "little") >> (pos & 7)
    return v & ((1 << n) - 1)


class _Arc:
    def __init__(self, ctype):
        self.min_bits = 7 if ctype == CT_7_BIT else 8
        self.min_table_entry = 1 << self.min_bits
        self.free_idx = self.min_table_entry
        self.next_bits = self.min_bits + 1
        self.free_limit = 1 << self.next_bits
        n = 1 << ARC_BITS_MAX
        self.base = [0] * n
        self.ch = [0] * n
        self.nxt = [-1] * n
        self.hash = [-1] * n
        self.cur_entry = None
        self.next_entry = None
        self.cur_bits = 0
        self.entry_used = True
        self.entry_get()
        self.entry_used = True

    def entry_get(self):
        if not self.entry_used:
            return
        i = self.free_idx
        self.entry_used = False
        self.cur_entry = self.next_entry
        self.cur_bits = self.next_bits
        if self.next_bits < ARC_BITS_MAX:
            self.next_entry = i
            i += 1
            if i == self.free_limit:
                self.next_bits += 1
                self.free_limit = 1 << self.next_bits
        else:
            while True:
                i += 1
                if i == self.free_limit:
                    i = self.min_table_entry
                if self.hash[i] == -1:
                    break
            tmp = i
            self.next_entry = tmp
            bc = self.base[tmp]
            prev, cur = None, self.hash[bc]
            while cur != -1:
                if cur == tmp:
                    if prev is None:
                        self.hash[bc] = self.nxt[tmp]
                    else:
                        self.nxt[prev] = self.nxt[tmp]
                    break
                prev, cur = cur, self.nxt[cur]
        self.free_idx = i


def expand(arc):
    """ExpandBuf: CArcCompress {I64 compressed, I64 expanded, U8 type}."""
    csize, esize, ctype = struct.unpack_from("<qqB", arc, 0)
    if ctype == CT_NONE:
        return bytes(arc[17:17 + esize])
    c = _Arc(ctype)
    src_size = csize << 3
    pos = 17 << 3
    dst = bytearray()
    stk = []
    lastcode = _bits(arc, pos, c.next_bits)
    pos += c.next_bits
    dst.append(lastcode)
    c.entry_get()
    last_ch = lastcode
    while len(dst) < esize and pos + c.next_bits <= src_size:
        basecode = _bits(arc, pos, c.next_bits)
        pos += c.next_bits
        if c.cur_entry == basecode:
            stk.append(last_ch)
            code = lastcode
        else:
            code = basecode
        while code >= c.min_table_entry:
            stk.append(c.ch[code])
            code = c.base[code]
        stk.append(code)
        last_ch = code
        c.entry_used = True
        tmp = c.cur_entry
        c.base[tmp] = lastcode
        c.ch[tmp] = last_ch
        c.nxt[tmp] = c.hash[lastcode]
        c.hash[lastcode] = tmp
        c.entry_get()
        while stk and len(dst) < esize:
            dst.append(stk.pop())
        lastcode = basecode
    return bytes(dst[:esize])


class ISO:
    """The distro CD: ISO 9660 on the outside so it boots, RedSea inside
    (::/Kernel/BlkDev/FileSysRedSea.HC). RedSea clusters are 512-byte
    blocks and every file is contiguous."""
    BLK = 512
    RS_ATTR_DIR = 0x10

    def __init__(self, path):
        self.data = open(path, "rb").read()
        self.boot = None
        for off in range(0, len(self.data) - 512, 512):
            if self.data[off + 3] == 0x88 and \
                    self.data[off + 510:off + 512] == b"\x55\xaa":
                self.boot = off
                break
        assert self.boot is not None, "no RedSea boot block"
        (self.drv_offset, self.sects, self.root_clus, self.bitmap_sects,
         _) = struct.unpack_from("<qqqqq", self.data, self.boot + 8)
        self.files = {}
        self._seen = set()
        self._walk(self.root_clus, "", None)

    def _entries(self, clus, size=None):
        off = clus * self.BLK
        first = True
        while True:
            attr = struct.unpack_from("<H", self.data, off)[0]
            name = self.data[off + 2:off + 40].split(b"\0")[0].decode(
                "latin-1")
            c, sz = struct.unpack_from("<qq", self.data, off + 40)
            if not name:
                break
            yield attr, name, c, sz, first
            first = False
            off += 64
            if size is not None and off >= clus * self.BLK + size:
                break

    def _walk(self, clus, prefix, size):
        if clus in self._seen:  # the boot directory lists itself
            return
        self._seen.add(clus)
        for attr, name, c, sz, first in self._entries(clus, size):
            if name in (".", ".."):
                continue
            path = prefix + name
            if attr & self.RS_ATTR_DIR:
                self._walk(c, path + "/", sz)
            else:
                self.files[path] = dict(clus=c, size=sz, attr=attr)

    def find(self, relpath):
        want = relpath.upper()
        for k in self.files:
            if k.upper() in (want, want + ".Z"):
                return k
        raise KeyError(relpath)

    def get(self, relpath):
        k = self.find(relpath)
        r = self.files[k]
        raw = self.data[r["clus"] * self.BLK:r["clus"] * self.BLK + r["size"]]
        return expand(raw) if k.upper().endswith(".Z") else raw


if __name__ == "__main__":
    iso = ISO(sys.argv[1])
    if sys.argv[2] == "ls":
        for k, r in sorted(iso.files.items()):
            print("%8d %s" % (r["size"], k))
    elif sys.argv[2] == "get":
        data = iso.get(sys.argv[3])
        with open(sys.argv[4], "wb") as f:
            f.write(data)
        print(len(data), "bytes")
