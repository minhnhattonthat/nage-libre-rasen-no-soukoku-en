"""Text codec for the game's Shift-JIS strings: byte-exact both ways.

Two-byte characters and ASCII decode as themselves, 0x0A as a newline, half-width katakana as themselves.
Control codes are ASCII and stay as written: %h %z (half-width on/off), %cNN (colour), %tNN, %p, %k (docs/re/text.md).
Any byte that would not survive decode -> encode (stray bytes, cp932 duplicates, a literal '[') becomes [XX].
"""
import re

HEX = re.compile(r"\[([0-9A-F]{2})\]")


def _char(b, i):
    """(text, length) for the character at b[i], or None when it must be escaped."""
    c = b[i]
    n = 2 if (0x81 <= c <= 0x9F or 0xE0 <= c <= 0xFC) else 1
    raw = bytes(b[i:i + n])
    # cp932 maps lone 0x80, 0xA0, 0xFD-0xFF to private-use characters; escape them (they are never game text)
    if len(raw) < n or raw == b"[" or (n == 1 and c < 0x20 and c != 0x0A) or c == 0x7F or (
            n == 1 and c >= 0x80 and not 0xA1 <= c <= 0xDF):
        return None
    try:
        ch = raw.decode("cp932")
    except UnicodeDecodeError:
        return None
    return (ch, n) if ch.encode("cp932") == raw else None


def decode(b):
    out, i = [], 0
    while i < len(b):
        r = _char(b, i)
        if r:
            out.append(r[0])
            i += r[1]
        else:
            out.append(f"[{b[i]:02X}]")
            i += 1
    return "".join(out)


def encode(s):
    out, i = bytearray(), 0
    while i < len(s):
        m = HEX.match(s, i)
        if m:
            out.append(int(m[1], 16))
            i = m.end()
        else:
            out += s[i].encode("cp932")
            i += 1
    return bytes(out)


def clean(s):
    """True if the text decoded with no escapes."""
    return not HEX.search(s)


if __name__ == "__main__":
    for raw in (b"\x82\xa0%h\x88\xea%z\n[x]\xff\x87\x40\xed\x40", b"\xa6\xdf ABC"):
        assert encode(decode(raw)) == raw, decode(raw)
    print("selftest ok", decode(b"\x82\xa0[\xff"))
