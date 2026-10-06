"""Split the big source into batch folders and build each batch's plan.tsv.

Usage:  python tools/split.py [input/source.txt] [--size 200]
Creates batch_01/, batch_02/, ... each with source.txt, meta.json, plan.tsv, report.md.
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import read_paragraphs  # noqa: E402
from plan import write_plan  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("source", nargs="?", default="input/source.txt")
ap.add_argument("--size", type=int, default=200)
args = ap.parse_args()

paras = read_paragraphs(args.source)
# a downloaded title block ("Title ====" or "# Title") is not a paragraph
if paras and len(paras[0].split()) < 20 and (re.search(r"\s={3,}$", paras[0]) or paras[0].startswith("# ")):
    print("Dropped title header:", paras[0][:60])
    paras = paras[1:]
total = len(paras)
if total == 0:
    sys.exit(f"No paragraphs found in {args.source}")
width = max(3, len(str(total)))
template = Path(__file__).parent / "report_template.md"

for b, off in enumerate(range(0, total, args.size), 1):
    chunk = paras[off:off + args.size]
    d = Path(f"batch_{b:02d}")
    d.mkdir(exist_ok=True)
    (d / "source.txt").write_text("\n\n".join(chunk) + "\n", encoding="utf-8")
    (d / "meta.json").write_text(json.dumps(
        {"batch": b, "start": off + 1, "count": len(chunk), "total": total, "width": width}), encoding="utf-8")
    write_plan(d)
    if template.exists() and not (d / "report.md").exists():
        shutil.copy(template, d / "report.md")
    print(f"{d}: paragraphs {off + 1}-{off + len(chunk)} of {total}")
