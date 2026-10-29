"""MAPDAT event-script bytecode: parse, list strings, re-encode with remapped offsets (docs/re/text.md §Opcodes).

usage:
  script.py dump MAPDAT.BIN SLOT     list one script's instructions
  script.py check [TREE]             parse every script of every MAPDAT, report gaps (coverage) and roundtrip

A script is a run of 16-bit opcode words with u16 arguments. Arguments that hold script offsets (jump targets,
string offsets, data offsets) are kinds 'j', 's', 'd'; plain values are 'v'. Parsing follows control flow from
offset 0, so data and strings reached by offset are told apart from code.
"""
import bisect
import glob
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sweep_packed import table  # noqa: E402

FIRST, LAST = 186, 216  # MAPDAT slots that hold event scripts

# opcode -> (argument kinds, flow continues after it). Lengths from the handlers at 0x8005E49C-0x80060928.
OPS = {
    0x01: ("j", False), 0x02: ("j", True), 0x03: ("", False),
    0x06: ("vj", True), 0x07: ("vjj", False), 0x08: ("vj", True), 0x09: ("vjj", False),
    0x0A: ("v", True), 0x0B: ("", False), 0x0C: ("s", True),
    0x0F: ("v", True), 0x10: ("v", True), 0x11: ("v", True), 0x12: ("v", True), 0x13: ("vv", True),
    0x14: ("", True), 0x15: ("d", True), 0x16: ("vv", True), 0x17: ("", True), 0x18: ("", True),
    0x19: ("", True), 0x1A: ("vv", True), 0x1B: ("vvd", True), 0x1C: ("s", True),
    0x1F: ("vj", True), 0x20: ("vjj", True), 0x21: ("vj", True), 0x22: ("vjj", True),
    0x23: ("vs", True), 0x24: ("vss", True), 0x25: ("vs", True), 0x26: ("vss", True),
    0x27: ("vs", True), 0x28: ("vss", True), 0x29: ("vs", True), 0x2A: ("vss", True),
    0x2B: ("vv", True), 0x2C: ("v", True), 0x2D: ("v", True), 0x2E: ("vv", True), 0x2F: ("vv", True),
    0x30: ("vv", True), 0x31: ("vvv", True), 0x32: ("v", True), 0x33: ("", True), 0x34: ("v", True),
    0x35: ("", False), 0x36: ("", False), 0x37: ("v", True), 0x38: ("v", True), 0x39: ("v", True),
    0x3A: ("v", True), 0x3B: ("v", False), 0x3C: ("", True), 0x3D: ("", True), 0x3E: ("vv", True),
    0x3F: ("v", True), 0x40: ("v", True), 0x41: ("v", True), 0x42: ("", True), 0x43: ("vv", True),
    0x44: ("v", True), 0x45: ("vv", True), 0x46: ("", True), 0x47: ("v", True), 0x48: ("vv", True),
    0x49: ("v", True), 0x4A: ("v", True), 0x4B: ("v", True), 0x4C: ("vvv", True), 0x4D: ("v", True),
    0x4E: ("v", True), 0x4F: ("", True), 0x51: ("vv", True),
}
SWITCH = (0x04, 0x05)       # v n j*n (0xFFFF = fall through)
STRTAB = (0x0E, 0x1E)       # v n s*n (0xFFFF = none)
INLINE = (0x0D, 0x1D)       # SJIS string right after the opcode, NUL, one more NUL if the next byte is 0


def data_len(ins):
    """Bytes the handler reads at a 'd' offset: 0x15 four halfwords; 0x1B (move list) 8 per entry, count byte >= 1."""
    return 8 if ins.op == 0x15 else 8 * max(1, ins.args[1] & 0xFF)


def sjis_end(b, i):
    """Offset of the NUL that ends the string at i (lead bytes 0x81-0x9F/0xE0-0xFC take two bytes)."""
    while b[i]:
        i += 2 if 0x81 <= b[i] <= 0x9F or 0xE0 <= b[i] <= 0xFC else 1
    return i


class Ins:
    __slots__ = ("off", "op", "args", "kinds", "text", "size", "dead")

    def __repr__(self):
        a = " ".join(f"{k}{v:X}" for k, v in zip(self.kinds, self.args))
        return f"{self.off:04X} {self.op:02X} {a}" + (f" {self.text!r}" if self.text is not None else "")


def decode_ins(b, off):
    op, hi = b[off], b[off + 1]
    if hi != 0:
        raise ValueError(f"opcode word {op:02X}{hi:02X} at {off:X}")
    ins = Ins()
    ins.off, ins.op, ins.text = off, op, None
    p = off + 2
    if op in SWITCH or op in STRTAB:
        v, n = struct.unpack_from("<hH", b, p)
        ins.kinds = "vn" + ("j" if op in SWITCH else "s") * n
        ins.args = list(struct.unpack_from(f"<{n + 2}H", b, p))
        p += 4 + 2 * n
    elif op in INLINE:
        e = sjis_end(b, p)
        ins.kinds, ins.args, ins.text = "", [], bytes(b[p:e])
        p = e + 1
        if p < len(b) and b[p] == 0:
            p += 1
    elif op in OPS:
        ins.kinds = OPS[op][0]
        ins.args = list(struct.unpack_from(f"<{len(ins.kinds)}H", b, p))
        p += 2 * len(ins.kinds)
    else:
        raise ValueError(f"unknown opcode {op:02X} at {off:X}")
    ins.size = p - off
    return ins


def flows_on(ins):
    return OPS[ins.op][1] if ins.op in OPS else True


def parse(b):
    """Follow control flow from 0, then decode what is left as dead code where it decodes cleanly (cut scenes
    skipped by a goto still hold dialogue). Returns (code {off: Ins}, strings {off: end}, data {off: len});
    dead instructions have .dead set."""
    code, strings, data = {}, {}, {}

    def walk(todo, limit=None):
        while todo:
            off = todo.pop()
            while off not in code:
                if off >= len(b):
                    raise ValueError(f"flow runs off the end at {off:X}")
                try:
                    ins = decode_ins(b, off)
                except (struct.error, IndexError):
                    raise ValueError(f"instruction at {off:X} runs off the end")
                if limit and off + ins.size > limit:
                    raise ValueError(f"dead instruction at {off:X} crosses {limit:X}")
                ins.dead = limit is not None
                code[off] = ins
                for k, a in zip(ins.kinds, ins.args):
                    if a == 0xFFFF:
                        continue
                    if k == "j":
                        if limit is None:  # dead code is decoded linearly, its jumps not followed
                            todo.append(a)
                    elif k == "s":
                        strings[a] = sjis_end(b, a)
                    elif k == "d":
                        data[a] = data_len(ins)
                if (limit is None and not flows_on(ins)) or (limit and not any(b[off + ins.size:limit])):
                    break
                off += ins.size

    walk([0])
    done = set()
    while True:
        gaps = [g for g in coverage(b, code, strings, data) if g not in done]
        if not gaps:
            break
        for s, e in gaps:
            done.add((s, e))
            if s % 2 == 0:
                snap = dict(code), dict(strings), dict(data)
                try:
                    walk([s], e)
                except ValueError:  # not code: roll back to raw bytes
                    for live, old in zip((code, strings, data), snap):
                        live.clear()
                        live.update(old)
    return code, strings, data


def coverage(b, code, strings, data):
    """Byte ranges no instruction, string or data block accounts for (NUL padding excluded)."""
    used = bytearray(len(b))
    for ins in code.values():
        used[ins.off:ins.off + ins.size] = b"\1" * ins.size
    for s, e in strings.items():
        used[s:e + 1] = b"\1" * (e + 1 - s)
    for s, n in data.items():
        if n:
            used[s:s + n] = b"\1" * n
    gaps, i = [], 0
    while i < len(b):
        if used[i] or b[i] == 0:
            i += 1
            continue
        j = i
        while j < len(b) and not used[j]:
            j += 1
        gaps.append((i, j))
        i = j
    return gaps


def str_piece(b, s, e):
    """Bytes a referenced string occupies: text, NUL, and one 0 pad byte that keeps the next item 2-aligned."""
    n = e + 1 - s
    return n + 1 if n % 2 and e + 1 < len(b) and b[e + 1] == 0 else n


def pad_text(text, base):
    """text + NUL, padded so base + length stays even (base = bytes before the text in its piece)."""
    out = text + b"\0"
    return out + b"\0" if (base + len(out)) % 2 else out


def strings_of(b, parsed=None):
    """{offset: (bytes, kind, dead)} for every string: kind 'inline' (offset = its 0D/1D opcode) or 'ref'."""
    code, strings, _ = parsed or parse(b)
    out = {o: (i.text, "inline", i.dead) for o, i in code.items() if i.text is not None}
    for s, e in strings.items():
        out[s] = (bytes(b[s:e]), "ref", False)
    return out


def rebuild(b, texts, parsed=None):
    """Re-encode script b with texts {offset: new bytes} (offsets as in strings_of). Every jump, string and data
    offset is remapped; bytes no instruction or string accounts for are copied as they are."""
    code, strings, data = parsed or parse(b)
    pieces = {o: ("ins", i.size) for o, i in code.items()}
    for s, e in strings.items():
        if s in pieces:
            raise ValueError(f"string {s:X} is also code")
        pieces[s] = ("str", str_piece(b, s, e))
    starts = sorted(pieces)
    for a, c in zip(starts, starts[1:]):
        if a + pieces[a][1] > c:
            raise ValueError(f"items overlap at {a:X}/{c:X}")
    # raw runs fill the space between items
    items, pos = [], 0
    for s in starts:
        if s > pos:
            items.append((pos, "raw", s - pos))
        items.append((s, *pieces[s]))
        pos = s + pieces[s][1]
    if pos < len(b):
        items.append((pos, "raw", len(b) - pos))

    out, new = bytearray(), {}
    for s, kind, n in items:
        new[s] = len(out)
        if kind == "ins" and code[s].text is not None and s in texts:
            out += b[s:s + 2] + pad_text(texts[s], 2)
        elif kind == "str" and s in texts:
            out += pad_text(texts[s], 0)
        else:
            out += b[s:s + n]
        if kind != "raw" and len(out) % 2:
            raise ValueError(f"item {s:X} leaves the script odd-aligned")
    item_at = [s for s, _, _ in items]

    def remap(a, dead):
        if a in new:
            return new[a]
        s, kind, n = items[bisect.bisect_right(item_at, a) - 1]
        if kind == "raw" or dead:  # inside unchanged bytes, or a dead jump nobody takes
            return new[s] + a - s
        raise ValueError(f"offset {a:X} points inside item {s:X}")

    for s, ins in code.items():
        p = new[s] + 2
        for k, a in zip(ins.kinds, ins.args):
            if k in "jsd" and a != 0xFFFF:
                v = remap(a, ins.dead)
                if v > 0x7FFF:
                    raise ValueError("script over 32 KB (the PC is a signed 16-bit offset)")
                struct.pack_into("<H", out, p, v)
            p += 2
    return bytes(out)


def rebuild_mapdat(d, new_scripts):
    """MAPDAT bytes with slots {slot: script bytes} replaced; later offset-table entries shift. Each slot keeps its
    original start alignment mod 4 by padding the previous slot with zeros."""
    t = table(d)
    n = t[0] // 4
    out = bytearray(d[:t[FIRST]])
    offs = list(t[:n])
    for s in range(FIRST, n):
        while len(out) % 4 != t[s] % 4:
            out.append(0)
        offs[s] = len(out)
        out += new_scripts.get(s, d[t[s]:t[s + 1]])
    struct.pack_into(f"<{n}I", out, 0, *offs)
    return bytes(out)


def scripts(path):
    """(file bytes, offset table, {slot: script}) for the used slots; an unused slot holds `1A 00 00 00` (+ stray)."""
    d = open(path, "rb").read()
    t = table(d)
    return d, t, {s: d[t[s]:t[s + 1]] for s in range(FIRST, LAST + 1)
                  if t[s + 1] > t[s] and d[t[s]:t[s] + 4] != b"\x1a\0\0\0"}  # MAP40 #187 is zero bytes


def has_sjis(raw):
    return any("぀" <= c <= "ヿ" or "一" <= c <= "鿿" for c in raw.decode("cp932", "ignore"))  # kana or kanji


def check_script(b):
    """Problems with one script: parse errors, Japanese left outside parsed strings, identity or stretched rebuild
    that does not give back the same program."""
    try:
        parsed = parse(b)
    except ValueError as e:
        return [f"parse: {e}"]
    probs = [f"Japanese in unparsed bytes {s:X}-{e:X}" for s, e in coverage(b, *parsed) if has_sjis(b[s:e])]
    if rebuild(b, {}, parsed) != b:
        probs.append("identity rebuild differs")
    st = strings_of(b, parsed)
    grown = {o: t + "あ".encode("cp932") * (1 + o % 3) for o, (t, _, _) in st.items()}
    try:
        nb = rebuild(b, grown, parsed)
        np_ = parse(nb)
    except ValueError as e:
        return probs + [f"stretched: {e}"]
    nst = strings_of(nb, np_)
    old_code, new_code = [parsed[0][o] for o in sorted(parsed[0])], [np_[0][o] for o in sorted(np_[0])]
    if [nst[o][0] for o in sorted(nst)] != [grown[o] for o in sorted(grown)]:
        probs.append("stretched: strings differ")
    order_old = {o: i for i, o in enumerate(sorted(set(parsed[0]) | set(parsed[1]) | set(parsed[2])))}
    order_new = {o: i for i, o in enumerate(sorted(set(np_[0]) | set(np_[1]) | set(np_[2])))}
    for a, c in zip(old_code, new_code):
        if (a.op, a.kinds, a.dead) != (c.op, c.kinds, c.dead) or any(
                k in "jsd" and x != 0xFFFF and order_old.get(x) != order_new.get(y)
                for k, x, y in zip(a.kinds, a.args, c.args)) or any(
                k not in "jsd" and x != y for k, x, y in zip(a.kinds, a.args, c.args)):
            probs.append(f"stretched: instruction {a.off:X} -> {c.off:X} differs")
            break
    if len(old_code) != len(new_code):
        probs.append("stretched: instruction count differs")
    return probs


def main():
    if sys.argv[1] == "dump":
        _, _, sc = scripts(sys.argv[2])
        b = sc[int(sys.argv[3])]
        code, strings, data = parse(b)
        for o in sorted(code):
            print(code[o])
        for s, e in sorted(strings.items()):
            print(f"{s:04X} str {b[s:e].decode('cp932', 'replace')!r}")
        for s, n in sorted(data.items()):
            print(f"{s:04X} data {b[s:s + (n or 16)].hex(' ')}")
        for s, e in coverage(b, code, strings, data):
            print(f"{s:04X}-{e:04X} GAP {b[s:e][:32].hex(' ')}")
    elif sys.argv[1] == "check":
        tree = sys.argv[2] if len(sys.argv) > 2 else "work/disc/tree"
        bad = n = 0
        for path in sorted(glob.glob(f"{tree}/MAP01_06/*/MAPDAT.BIN")):
            d, _, sc = scripts(path)
            if rebuild_mapdat(d, {}) != d:
                print(path, "MAPDAT identity rebuild differs")
                bad += 1
            for slot, b in sc.items():
                n += 1
                for p in check_script(b):
                    print(path, slot, p)
                    bad += 1
        print(f"{n} scripts, {bad} problems")
        return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
