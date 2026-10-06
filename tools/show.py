"""Show a slice of source paragraphs with their plan, plus previous rewrite context.

Usage:  python tools/show.py batch_01 1 25
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import load_meta, load_plan, read_paragraphs  # noqa: E402

if len(sys.argv) != 4:
    sys.exit("usage: show.py BATCH_DIR START END   (local paragraph numbers, 1-based)")
batch, a, b = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
meta = load_meta(batch)
src = read_paragraphs(Path(batch) / "source.txt")
plan = load_plan(batch)
rw_path = Path(batch) / "rewrite.txt"
rw = read_paragraphs(rw_path) if rw_path.exists() else []

ctx = rw[max(0, a - 3):a - 1] if a > 1 else []
if a == 1 and meta["batch"] > 1:
    prev = Path(f"batch_{meta['batch'] - 1:02d}") / "rewrite.txt"
    if prev.exists():
        ctx = read_paragraphs(prev)[-2:]
if ctx:
    print("=== CONTEXT (previous rewritten paragraphs, do not repeat) ===")
    for c in ctx:
        print("-", c)
    print()

print(f"=== SOURCE {batch} P{a:03d}-P{b:03d} ===")
for i in range(a, min(b, len(src)) + 1):
    row = plan[i - 1] if i - 1 < len(plan) else {}
    flag = f" flag={row['flag']}" if row.get("flag") else ""
    print(f"\nP{i:03d} (global {row.get('global', '?')}) opener={row.get('opener')} "
          f"closer={row.get('closer')} src_words={row.get('src_words')}{flag}")
    print(src[i - 1])
