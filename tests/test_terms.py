"""Glossary terms, Avoid spellings and kept honorifics hold for every translated row in script/ (not only for the
batch files a translator returned)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import batches  # noqa: E402

# rows ruled to differ from the glossary form
RULED = {"EXE/013E0": "D11: 'Council President' in the battle bar",
         "NAME/467": "大木 here is the surname Oki, not the Great Tree route"}


def test_terms_hold_in_script():
    gl, errs = batches.glossary(), []
    for name in batches.files():
        for r in batches.load(name):
            if r.get("en") and r["id"] not in RULED:
                errs += [f"{r['id']}: {e}" for e in batches.terms(r["jp"], r["en"], gl)]
    assert not errs, "\n".join(errs)


def test_honorific_on_a_noun():
    gl = batches.glossary()
    assert batches.terms("ブタさん、そこ通して。", "Mister Pig, let us through.", gl)
    assert not batches.terms("ブタさん、そこ通して。", "Pig-san, let us through.", gl)
    assert not batches.terms("みなさん、ありがとう。", "Thank you, everyone.", gl)
    assert not batches.terms("ねーちゃん", "the girl", gl)
