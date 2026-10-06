"""Build the final deliverable folder output/batch_NN/ (rewrite.txt, prompts.txt, report.md).

Pastes the style anchor and the anchors of the characters named in each entry into every
prompt, so each prompt is self-contained for the image tool.

Usage:  python tools/assemble.py batch_01 [--force]
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import load_meta, parse_registry, read_paragraphs  # noqa: E402
from lint_prompts import lint, parse_entries  # noqa: E402
from verify import check  # noqa: E402

if len(sys.argv) < 2:
    sys.exit("usage: assemble.py BATCH_DIR [--force]")
batch = Path(sys.argv[1])
force = "--force" in sys.argv
meta = load_meta(batch)

r = check(batch, final=True)
errors, _ = lint(batch)
if (not r["ok"] or errors) and not force:
    sys.exit("Refusing to assemble: run verify.py --final and lint_prompts.py until both PASS "
             "(or use --force and record the leftovers in report.md).")

style, ents = parse_registry()
out = Path("output") / batch.name
out.mkdir(parents=True, exist_ok=True)

rewrite = read_paragraphs(batch / "rewrite.txt")
(out / "rewrite.txt").write_text("\n\n".join(rewrite) + "\n", encoding="utf-8")

header = ["# CHARACTER & FORM REGISTRY (anchors are also appended to every prompt)",
          f"# STYLE: {style}"]
header += [f"# {k}: {v}" for k, v in ents.items()]
blocks = ["\n".join(header), ""]
for e in parse_entries((batch / "prompts_body.txt").read_text(encoding="utf-8")):
    tag = f"[{e['num']:0{meta['width']}d}]"
    body = "\n".join([f"{tag} {e['head']}".rstrip()] + [f"Panel {n}: {t}" for n, t in sorted(e["panels"].items())])
    low = body.lower()
    used = [f"{k}: {v}" for k, v in ents.items() if k.lower() in low]
    tail = []
    if style:
        tail.append(f"Style: {style}")
    if used:
        tail.append("Character anchors: " + " | ".join(used))
    blocks.append("\n".join([body] + tail) + "\n")
(out / "prompts.txt").write_text("\n".join(blocks), encoding="utf-8")

rep = batch / "report.md"
if rep.exists():
    (out / "report.md").write_text(rep.read_text(encoding="utf-8"), encoding="utf-8")
else:
    print("WARNING: report.md missing in", batch)
print(f"{out}: {len(rewrite)} paragraphs, prompts {meta['start']}-{meta['start'] + len(rewrite) - 1}")
