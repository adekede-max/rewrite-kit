"""Quantitative check of batch_NN/rewrite.txt. Prints only what failed.

Usage:
  python tools/verify.py batch_01            # partial check while writing (sub-batches)
  python tools/verify.py batch_01 --final    # full check incl. paragraph count and ratios
Exit code 1 on FAIL. Paragraph numbers (P###) are local to the batch (1-200).
"""
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (DRAMATIC, DRAMATIC_FAIL, DRAMATIC_WARN, FIRST_PERSON_RE, INTENSIFIERS,  # noqa: E402
                    OPENER_WORD_WARN, PARA_MAX, PARA_MIN, PARTICIPIAL_FAIL, PARTICIPIAL_WARN,
                    SENT_REQUIRED, SLANG, count_words, is_participial, load_plan,
                    read_paragraphs, split_sentences, strip_quotes)


def check(batch, final=False):
    batch = Path(batch)
    src = read_paragraphs(batch / "source.txt")
    rw_file = batch / "rewrite.txt"
    rw = read_paragraphs(rw_file) if rw_file.exists() else []
    plan = load_plan(batch)
    n = len(rw)
    fails, warns, gfail, gwarn = {}, {}, [], []

    if n > len(src):
        gfail.append(f"rewrite has {n} paragraphs but source has {len(src)}")
    if final and n != len(src):
        gfail.append(f"paragraph count: rewrite {n} != source {len(src)}")

    part = 0
    for i, p in enumerate(rw, 1):
        f, w = [], []
        wc = count_words(p)
        if not PARA_MIN <= wc <= PARA_MAX:
            f.append(f"words={wc} (need {PARA_MIN}-{PARA_MAX})")
        sents = split_sentences(p)
        if len(sents) != SENT_REQUIRED:
            f.append(f"sentences={len(sents)} (need {SENT_REQUIRED}): " + " || ".join(s[:40] for s in sents))
        fp = FIRST_PERSON_RE.findall(strip_quotes(p))
        if fp:
            f.append(f"first-person outside quotes: {sorted(set(fp))}")
        low = p.lower()
        for s in SLANG:
            if re.search(rf"\b{re.escape(s)}\b", low):
                f.append(f"modern slang: '{s}'")
        ints = [x for x in INTENSIFIERS if re.search(rf"\b{x}\b", low)]
        if len(ints) >= 2 or any(len(re.findall(rf"\b{x}\b", low)) >= 2 for x in ints):
            f.append(f"stacked intensifiers: {ints}")
        part_here = is_participial(p)
        part += part_here
        if i - 1 < len(plan):
            planned = plan[i - 1]["opener"]
            if part_here and planned != "participial":
                f.append(f"opens with -ing phrase but plan says '{planned}'")
            elif planned == "participial" and not part_here:
                w.append("plan says participial opener, text differs (ok if ratio stays low)")
        if f:
            fails[i] = f
        if w:
            warns[i] = w

    if n >= 40 or final:
        ratio = part / n if n else 0
        msg = f"participial openers {part}/{n} = {ratio:.1%}"
        if ratio > PARTICIPIAL_FAIL:
            gfail.append(msg + f" > {PARTICIPIAL_FAIL:.0%}")
        elif ratio > PARTICIPIAL_WARN:
            gwarn.append(msg + f" > {PARTICIPIAL_WARN:.0%} (target 10-12%)")
        firsts = Counter(re.sub(r"\W", "", p.split()[0]).lower() for p in rw if p.split())
        for word, c in firsts.most_common(3):
            if c / n > OPENER_WORD_WARN:
                gwarn.append(f"first word '{word}' opens {c}/{n} paragraphs")

    blob = " ".join(rw).lower()
    for word in DRAMATIC:
        c = len(re.findall(rf"\b{word}\b", blob))
        if c > DRAMATIC_FAIL:
            gfail.append(f"dramatic word '{word}' used {c}x (max {DRAMATIC_FAIL})")
        elif c > DRAMATIC_WARN:
            gwarn.append(f"dramatic word '{word}' used {c}x (try <= {DRAMATIC_WARN})")

    ok = not fails and not gfail
    return dict(ok=ok, n=n, src=len(src), fails=fails, warns=warns, gfail=gfail, gwarn=gwarn,
                participial=part)


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: verify.py BATCH_DIR [--final]")
    r = check(sys.argv[1], final="--final" in sys.argv)
    print(f"{sys.argv[1]}: source {r['src']} / rewrite {r['n']} paragraphs")
    if r["fails"]:
        print(f"FAIL paragraphs ({len(r['fails'])}): " + ", ".join(f"P{i:03d}" for i in r["fails"]))
        for i, msgs in r["fails"].items():
            for m in msgs:
                print(f"  P{i:03d} {m}")
    for g in r["gfail"]:
        print("FAIL global:", g)
    for g in r["gwarn"]:
        print("WARN global:", g)
    if r["warns"]:
        print(f"WARN {len(r['warns'])} paragraphs differ from plan opener (informational)")
    print("RESULT:", "PASS" if r["ok"] else "FAIL")
    sys.exit(0 if r["ok"] else 1)


if __name__ == "__main__":
    main()
