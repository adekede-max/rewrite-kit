"""Lint batch_NN/prompts_body.txt against the anti-ambiguity rules.

Usage:  python tools/lint_prompts.py batch_01 [--registry registry.md]
Entry format (one per paragraph):
  [001] 4-panel symmetric grid (2x2),
  Panel 1: ...
  Panel 2: ...
  Panel 3: ...
  Panel 4: ...
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import load_meta, parse_registry, read_paragraphs  # noqa: E402

BANNED = r"boy|girl|teenager|man|woman|figure|person|student|warrior|sleeper|speaker|silhouette"
BODY = (r"eyes?|mouth|lips?|fists?|hands?|fingers?|knuckles|face|gaze|jaw|teeth|"
        r"shoulders?|chest|arms?|legs?|foot|feet|head|brow|throat|heart")
ALLOW_PREFIX = {"anonymous", "generic", "unnamed", "nameless"}


def parse_entries(text):
    entries, cur = [], None
    for ln in text.split("\n"):
        m = re.match(r"^\[(\d+)\]\s*(.*)$", ln.strip())
        if m:
            cur = {"num": int(m.group(1)), "head": m.group(2), "panels": {}}
            entries.append(cur)
            continue
        m = re.match(r"^Panel\s*(\d+)\s*:\s*(.*)$", ln.strip(), re.I)
        if m and cur is not None:
            cur["panels"][int(m.group(1))] = m.group(2).strip()
    return entries


def lint(batch, registry="registry.md"):
    batch = Path(batch)
    meta = load_meta(batch)
    errors, warns = [], []
    f = batch / "prompts_body.txt"
    if not f.exists():
        return [f"{f} not found"], []
    entries = parse_entries(f.read_text(encoding="utf-8"))
    _, ents = parse_registry(registry)
    keys = [k.lower() for k in ents]
    if not keys:
        warns.append("registry.md has no entities; name checks skipped")

    rw = batch / "rewrite.txt"
    expected = len(read_paragraphs(rw)) if rw.exists() else meta["count"]
    if len(entries) != expected:
        errors.append(f"entries={len(entries)} but rewrite paragraphs={expected}")
    for i, e in enumerate(entries):
        want = meta["start"] + i
        tag = f"[{e['num']:0{meta['width']}d}]"
        if e["num"] != want:
            errors.append(f"{tag} numbering: expected {want}")
        if sorted(e["panels"]) != [1, 2, 3, 4]:
            errors.append(f"{tag} needs exactly Panel 1-4, got {sorted(e['panels'])}")
        if "4-panel" not in e["head"].lower() and "4-panel" not in e["head"]:
            warns.append(f"{tag} header should say '4-panel symmetric grid (2x2),'")
        for n, txt in sorted(e["panels"].items()):
            where = f"{tag} Panel {n}"
            low = txt.lower()
            if len(txt.split()) < 5:
                errors.append(f"{where}: too short")
                continue
            has_entity = any(k in low for k in keys) or re.search(r"\b(anonymous|generic|unnamed)\b", low)
            if keys and not has_entity:
                warns.append(f"{where}: no registry entity named (ok only for pure environment shots)")
            if re.match(r"^(he|she|they|his|her|their)\b", low):
                errors.append(f"{where}: starts with a pronoun")
            for m in re.finditer(rf"\b({BANNED})s?\b", low):
                before = low[:m.start()].split()[-3:]
                if not ALLOW_PREFIX.intersection(before):
                    errors.append(f"{where}: generic noun '{m.group(0)}' (use a name or 'anonymous ...')")
            for m in re.finditer(rf"\b({BODY})\b", low):
                pre = low[max(0, m.start() - 3):m.start()]
                post = low[m.end():m.end() + 80]
                owned = pre.endswith("'s ") or pre.endswith("’s ") or re.match(
                    r"\s+of\s+(" + "|".join(re.escape(k) for k in keys) + ")" if keys else r"$^", post)
                if not owned:
                    errors.append(f"{where}: body part '{m.group(0)}' without named owner")
    return errors, warns


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: lint_prompts.py BATCH_DIR [--registry registry.md]")
    reg = sys.argv[sys.argv.index("--registry") + 1] if "--registry" in sys.argv else "registry.md"
    errors, warns = lint(sys.argv[1], reg)
    for e in errors:
        print("ERROR", e)
    for w in warns[:40]:
        print("WARN ", w)
    if len(warns) > 40:
        print(f"WARN  ... {len(warns) - 40} more warnings")
    print("RESULT:", "FAIL" if errors else "PASS")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
