"""Translation batches (docs/translator-brief.md): split untranslated rows into work/tl/bNNN.tsv, check a translator's
work/tl/bNNN.out.tsv, merge checked batches into script/.

    python -X utf8 tools/batches.py split [--chars 3500]   new batches from rows with no `en` (never overwrites)
    python -X utf8 tools/batches.py check b001 [b002 ..]    exit 1 on any error; prints OK per clean batch
    python -X utf8 tools/batches.py merge b001 [b002 ..]    check, then write `en` into script/*.json
    python -X utf8 tools/batches.py pairs OUT b001 [..]     reviewer pairs file (>> id | JP / EN, +-2 context)
    python -X utf8 tools/batches.py refit                   move `long` rows that fit their field now into `en`

Input TSV: id, speaker, form, limit, jp (JP newlines shown as ` / `). Output TSV: id, English (`\\n` = a forced
break). Story order: MAP86 + MAP85 (New Game intro) first, then the maps by number, then exe, records, names.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import boxes  # noqa: E402
import extract  # noqa: E402
import lint  # noqa: E402
import script as sc  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TL = ROOT / "work/tl"
SCRIPT = ROOT / "script"
FIRST = ["MAP86", "MAP85"]
# op 16 face id -> speaker (ids 1-5 from who never names herself, docs/re/text.md §Speakers; 6-7 guessed)
FACES = {1: "Ann", 2: "Itsuki", 3: "Makoto", 4: "Shinobu", 5: "Mio", 6: "Jin?", 7: "Dai?"}
HONORIFIC = {"さん": "-san", "ちゃん": "-chan", "くん": "-kun", "君": "-kun", "様": "-sama", "先輩": "-senpai",
             "先生": "-sensei"}
CODE = re.compile(r"%c\d\d|%t\d\d|%p|%k|%d|\[[0-9A-F]{2}\]")


def files():
    maps = sorted(p.stem for p in (SCRIPT / "maps").glob("*.json"))
    return ([f"maps/{m}.json" for m in FIRST + [m for m in maps if m not in FIRST]]
            + ["exe.json", "records.json", "names.json"])


def load(name):
    return json.loads((SCRIPT / name).read_text(encoding="utf-8"))


def speakers():
    """{row id: speaker} for dialogue: the face of the last op 16 or 2B (op 17 = no face)."""
    out = {}
    for path in extract.map_files(extract.TREE):
        _, _, scripts = sc.scripts(path)
        for slot, b in scripts.items():
            code, face = sc.parse(b)[0], None
            for o in sorted(code):
                ins = code[o]
                if ins.op in (0x16, 0x2B):  # 16 opens the face box, 2B (face, expression) swaps the face
                    face = ins.args[0]
                elif ins.op == 0x17:
                    face = None
                if ins.text is not None:
                    out[f"{path.parent.name}/{slot}/{o:04X}"] = (
                        "(no face)" if face is None else FACES.get(face, f"NPC face {face}"))
    return out


def limit(rid, box):
    if box:
        px, lines = boxes.budget(box)
        return f"{box} {px}px x{lines}"
    f = boxes.field(rid)
    return f"{f[0]}px x{f[1]}" if f else "?"


def form(name, rid, spk):
    if name.startswith("maps/"):
        return "narration" if spk == "(no face)" else "dlg"
    return {"names.json": "name", "records.json": "label"}.get(name, "menu")


def show(s):
    return s.replace("\n", " / ")


def glossary():
    """[(jp, en, avoid)] from the tables in glossary.md."""
    out = []
    for line in (ROOT / "glossary.md").read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and len(cells) >= 5 and cells[0] not in ("JP", "") and not set(cells[0]) <= set("-"):
            out.append((cells[0], cells[1], [a.strip() for a in cells[4].split(",") if a.strip()]))
    return out


def _bare(jp):
    """JP with furigana (%h（よみ）%z) and control codes removed, for term matching."""
    return re.sub(r"%h（[^）]*）\s*　*%z", "", jp)


def has_term(jp, term):
    """Whole-run match on furigana-free JP: a katakana term not inside a longer katakana run; a one-kanji name
    (真 is also in 写真) only with its furigana or an honorific after it."""
    if len(term) == 1 and not "゠" <= term <= "ヿ":
        return re.search(re.escape(term) + r"(%h（|\s*(" + "|".join(HONORIFIC) + "))", jp) is not None
    jp = _bare(jp)
    for m in re.finditer(re.escape(term), jp):
        before, after = jp[m.start() - 1:m.start()], jp[m.end():m.end() + 1]
        kata = lambda c: c and ("゠" <= c <= "ヿ")  # noqa: E731
        kanji = lambda c: c and ("一" <= c <= "鿿")  # noqa: E731
        if kata(term[0]) and (kata(before) or kata(after)):
            continue
        if kanji(term[0]) and kanji(before):  # 魔物 inside 邪魔物
            continue
        return True
    return False


def split(chars):
    TL.mkdir(parents=True, exist_ok=True)
    done = {line.split("\t")[0] for p in TL.glob("b[0-9][0-9][0-9].tsv")
            for line in p.read_text(encoding="utf-8").splitlines()}
    n = max([int(p.stem[1:]) for p in TL.glob("b[0-9][0-9][0-9].tsv")] or [0])
    box_of, spk = boxes.all_rows(), speakers()
    batch, size, out = [], 0, []

    def flush():
        nonlocal batch, size
        if batch:
            out.append(batch)
        batch, size = [], 0

    for name in files():
        rows = [r for r in load(name) if not r.get("en") and not r.get("same") and r["jp"].strip("　 \n")
                and r["id"] != "MEMCARD" and r["id"] not in done]
        if not rows:
            continue
        if name.startswith("maps/") and batch and size + sum(len(r["jp"]) for r in rows) > chars * 1.15:
            flush()
        if not name.startswith("maps/"):
            flush()  # system text and names: batches of their own
        slot, left = None, sum(len(r["jp"]) for r in rows)
        for r in rows:
            s = r["id"].rsplit("/", 1)[0]
            if size >= chars and s != slot and left > chars * 0.3:  # no stub batch for a map's last few slots
                flush()
            left -= len(r["jp"])
            slot = s
            sp = spk.get(r["id"], "")
            batch.append("\t".join([r["id"], sp, form(name, r["id"], sp), limit(r["id"], box_of.get(r["id"])),
                                    show(r["jp"]) + (" (unused: cut content)" if r.get("dead") else "")]))
            size += len(r["jp"]) if name != "names.json" else len(r["jp"]) * 0.4
    flush()
    gl = glossary()
    for b in out:
        n += 1
        p = TL / f"b{n:03d}.tsv"
        assert not p.exists(), p
        p.write_text("\n".join(b) + "\n", encoding="utf-8")
        jp = "".join(line.split("\t")[4].replace(" / ", "\n") for line in b)
        terms = [f"{j} = {e}" + (f" (not: {', '.join(a)})" if a else "") for j, e, a in gl if has_term(jp, j)]
        (TL / f"terms_b{n:03d}.txt").write_text("\n".join(terms) + "\n", encoding="utf-8")
        print(f"b{n:03d}: {len(b)} rows, {sum(len(x.split(chr(9))[4]) for x in b)} JP chars, {len(terms)} terms,"
              f" {b[0].split(chr(9))[0]} .. {b[-1].split(chr(9))[0]}")


def read_out(b):
    rows = []
    for line in (TL / f"{b}.out.tsv").read_text(encoding="utf-8").splitlines():
        if line.strip():
            rid, _, en = line.partition("\t")
            rows.append((rid.strip(), en.replace("\\n", "\n").replace("\\s", " ")))
    return rows


KEEP = "=JP"  # output value: keep the original bytes (blanking rows, debug printf)
WIDTH = re.compile(r" px in a \d+-px field| lines in a \d+-line field")


def long_rows(errs):
    """Field rows whose only errors are width/lines over the field: deferred to the phase-7 fit (engine) work."""
    by = {}
    for e in errs:
        rid, _, msg = e.partition(": ")
        by.setdefault(rid, []).append(msg)
    return {rid for rid, ms in by.items() if rid.split("/")[0] in ("EXE", "NAME", "CLUB", "ITEM", "MAGIC")
            and all(WIDTH.search(m) for m in ms)}


def rows_by_id():
    out = {}
    for name in files():
        for r in load(name):
            out[r["id"]] = (name, r)
    return out


def check(b, allrows, box_of, gl):
    errs = []
    want = [line.split("\t")[0] for line in (TL / f"{b}.tsv").read_text(encoding="utf-8").splitlines() if line]
    if not (TL / f"{b}.out.tsv").exists():
        return [f"{b}: no {b}.out.tsv"]
    got = read_out(b)
    ids = [i for i, _ in got]
    if ids != want:
        missing, extra = set(want) - set(ids), set(ids) - set(want)
        dup = {i for i in ids if ids.count(i) > 1}
        errs.append(f"{b}: ids differ from the input (missing {sorted(missing)[:5]}, extra {sorted(extra)[:5]},"
                    f" duplicate {sorted(dup)[:5]}, or out of order)")
    for rid, en in got:
        if rid not in allrows:
            continue
        name, r = allrows[rid]
        if en == KEEP:
            continue
        if not en.strip():
            errs.append(f"{rid}: empty")
            continue
        if "\t" in en or re.search(r"\\u[0-9a-fA-F]{4}", en):
            errs.append(f"{rid}: tab or \\uXXXX")
        if sorted(CODE.findall(en)) != sorted(CODE.findall(r["jp"])):
            errs.append(f"{rid}: control codes {CODE.findall(r['jp'])} not kept exactly (got {CODE.findall(en)})")
        if re.search(r"%[hz]", en):
            errs.append(f"{rid}: drop %h/%z (half-width furigana switch): English is half-width already")
        row = dict(r, en=en)
        if not name.startswith("maps/"):
            lint.FIELD_ROWS.add(rid)
        e, _ = lint.check_row(row, box_of.get(rid), fixed=name == "records.json")
        errs += [f"{rid}: {x}" for x in e]
        jp = _bare(r["jp"])
        for j, e_, avoid in gl:
            if j not in jp and j not in r["jp"]:
                continue
            if has_term(r["jp"], j) and e_ and e_.lower() not in en.lower():
                errs.append(f"{rid}: glossary {j} = {e_!r} missing")
            for a in avoid:
                if re.search(rf"\b{re.escape(a)}\b", en):
                    errs.append(f"{rid}: {a!r} is on the glossary's Avoid list for {j}")
            for hj, he in HONORIFIC.items():
                # the suffix may follow the full name (Kaoru Kanzaki-san); 様 may be Lord/Lady X
                ok = he in en.lower() or (he == "-sama" and re.search(r"\b(Lord|Lady)\b", en))
                if e_ and re.search(re.escape(j) + r"\s*" + hj, jp) and not ok:
                    errs.append(f"{rid}: {j}{hj} -> {e_}{he} (honorifics are kept)")
    new = {rid: en for rid, en in got if rid.startswith("NAME/")}
    if new:  # all names share SYSDATA's buffer (lint.NAMES_SLACK)
        grow = sum(len(new.get(r["id"], r.get("en", ""))) - len(r["jp"].encode("cp932"))
                   for r in load("names.json") if r["id"] in new or r.get("en"))
        if grow > lint.NAMES_SLACK:
            errs.append(f"{b}: English names add {grow} bytes to SYSDATA, room {lint.NAMES_SLACK}: report it (LONG), never abbreviate")
    return errs


def merge(bs):
    allrows, box_of, gl = rows_by_id(), boxes.all_rows(), glossary()
    errs = [e for b in bs for e in check(b, allrows, box_of, gl)]
    longs = long_rows(errs)
    errs = [e for e in errs if e.partition(": ")[0] not in longs]
    if errs:
        print("\n".join(errs))
        print(f"merge refused: {len(errs)} errors")
        return 1
    new = {rid: en for b in bs for rid, en in read_out(b)}
    for name in files():
        rows = load(name)
        hit = [r for r in rows if r["id"] in new]
        if hit:
            for r in hit:
                en = "" if new[r["id"]] == KEEP else new[r["id"]]
                r.pop("long", None)
                if r["id"] in longs:  # full English kept for the phase-7 fit; Japanese stays in the build
                    r["long"], en = en, ""
                r["en"] = en
            (SCRIPT / name).write_text(extract.dump(rows), encoding="utf-8", newline="\n")
            print(f"{name}: {len(hit)} rows")
    return 0


def refit():
    """Phase 7: move each `long` row whose English now passes lint (engine work widened its field) into `en`."""
    left = 0
    for name in files():
        rows, moved = load(name), 0
        for r in rows:
            if r.get("long"):
                if not name.startswith("maps/"):
                    lint.FIELD_ROWS.add(r["id"])
                if lint.check_row(dict(r, en=r["long"]), fixed=name == "records.json")[0]:
                    left += 1
                    continue
                r["en"] = r.pop("long")
                moved += 1
        if moved:
            (SCRIPT / name).write_text(extract.dump(rows), encoding="utf-8", newline="\n")
            print(f"{name}: {moved} rows fitted")
    print(f"{left} rows still long")
    return 0


def pairs(out, bs):
    allrows, spk = rows_by_id(), speakers()
    seq = {}  # file -> ordered ids
    for name in files():
        seq[name] = [r["id"] for r in load(name)]
    lines = []
    for b in bs:
        for rid, en in read_out(b):
            name, r = allrows[rid]
            ids = seq[name]
            i = ids.index(rid)
            ctx = [allrows[x][1] for x in ids[max(0, i - 2):i]]
            lines += [f"   {c['id']} | {show(c['jp'])}" + (f" / EN: {show(c['en'])}" if c.get("en") else "")
                      for c in ctx]
            lines += [f">> {rid} [{spk.get(rid, 'field')}] | {show(r['jp'])}", f"   EN: {show(en)}", ""]
    Path(out).write_text("\n".join(lines), encoding="utf-8")
    print(f"{out}: {sum(1 for x in lines if x.startswith('>>'))} entries")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["split", "check", "merge", "pairs", "refit"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--chars", type=int, default=3500)
    a = ap.parse_args()
    if a.cmd == "split":
        return split(a.chars)
    if a.cmd == "merge":
        return merge(a.args)
    if a.cmd == "pairs":
        return pairs(a.args[0], a.args[1:])
    if a.cmd == "refit":
        return refit()
    allrows, box_of, gl, bad = rows_by_id(), boxes.all_rows(), glossary(), 0
    for b in a.args:
        errs = check(b, allrows, box_of, gl)
        longs = long_rows(errs)
        for e in errs:
            print(("LONG  " if e.partition(": ")[0] in longs else "") + e)
        errs = [e for e in errs if e.partition(": ")[0] not in longs]
        print(f"{b}: OK" + (f" ({len(longs)} LONG field rows: merged as `long`, fitted in phase 7)" if longs else "")
              if not errs else f"{b}: {len(errs)} errors")
        bad += len(errs)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
