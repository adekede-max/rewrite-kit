"""Phase 0 helper: candidate character/term names with first-appearance snippets and form hints.

Usage:  python tools/extract_names.py [input/source.txt] [--min 3] [--top 60]
Writes registry_candidates.md (the agent only tidies it into registry.md).
"""
import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import read_paragraphs  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("source", nargs="?", default="input/source.txt")
ap.add_argument("--min", type=int, default=3)
ap.add_argument("--top", type=int, default=60)
args = ap.parse_args()

STOP = set("""The A An He She It They We You I His Her Its Their Our My Your This That These Those There Then
But And Or So Yet If When While As At In On Of To For With From By Not No Yes What Why How Who Where Which
After Before Once Now Just Even Still Only Every Each One Two Three Suddenly Meanwhile However Finally""".split())
FORM_HINTS = re.compile(r"transform|reborn|reincarnat|evolv|armor|armour|beast|monster|disguis|child|young|"
                        r"past life|true form|mode|awaken", re.I)
NAME = re.compile(r"\b([A-Z][a-z]{2,}(?:\s[A-Z][a-z]{2,}){0,2})\b")

paras = read_paragraphs(args.source)
lower_words = Counter(w for p in paras for w in re.findall(r"\b[a-z]{3,}\b", p))
count, first, hints = Counter(), {}, defaultdict(list)
for idx, p in enumerate(paras, 1):
    for m in NAME.finditer(p):
        name = m.group(1)
        head = name.split()[0]
        if head in STOP or lower_words[head.lower()] > 0:   # ordinary word, not a name
            continue
        count[name] += 1
        first.setdefault(name, (idx, p[max(0, m.start() - 50):m.end() + 70]))
        window = p[max(0, m.start() - 120):m.end() + 120]
        if FORM_HINTS.search(window) and len(hints[name]) < 3:
            hints[name].append((idx, window.replace("\n", " ")))

lines = ["# Registry candidates (auto-extracted; verify with grep before trusting)\n"]
for name, c in count.most_common(args.top):
    if c < args.min:
        break
    i, snip = first[name]
    lines.append(f"## {name}  (x{c}, first at paragraph {i})")
    lines.append(f"- first: ...{snip}...")
    for hi, h in hints[name]:
        lines.append(f"- form hint P{hi}: ...{h}...")
    lines.append("")
Path("registry_candidates.md").write_text("\n".join(lines), encoding="utf-8")
print(f"registry_candidates.md written ({min(len(count), args.top)} candidates scanned, {len(paras)} paragraphs)")
