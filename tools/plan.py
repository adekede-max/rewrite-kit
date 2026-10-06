"""Deterministic opener/closer schedule per paragraph (replaces ratio counting by the agent).

Usage:  python tools/plan.py batch_01 [batch_02 ...]   (split.py already calls this)
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import QUOTE_RE, count_words, load_meta, read_paragraphs  # noqa: E402

PARTICIPIAL_SHARE = 0.11
OTHER_OPENERS = {"subject": 45, "time_place": 22, "dialogue": 17, "question_exclaim": 5}
CLOSERS = {"quip": 20, "punchline": 15, "emotion": 18, "cliffhanger": 17,
           "rhetorical_question": 10, "action": 20}
QUIP_CLASS = {"quip", "punchline"}      # together = 35% (limit is 40-50%)


def alloc(n, weights):
    total = sum(weights.values())
    raw = {k: n * v / total for k, v in weights.items()}
    out = {k: int(v) for k, v in raw.items()}
    left = n - sum(out.values())
    for k in sorted(raw, key=lambda k: raw[k] - out[k], reverse=True)[:left]:
        out[k] += 1
    return out


def spread(seq, key=lambda x: x):
    """Swap later items forward so equal neighbours (by key) are separated."""
    seq = list(seq)
    for i in range(1, len(seq)):
        if key(seq[i]) == key(seq[i - 1]):
            for j in range(i + 1, len(seq)):
                if key(seq[j]) != key(seq[i - 1]) and (i + 1 >= len(seq) or key(seq[j]) != key(seq[i])):
                    seq[i], seq[j] = seq[j], seq[i]
                    break
    return seq


def no_triple_quip(seq):
    seq = list(seq)
    for i in range(2, len(seq)):
        if seq[i] in QUIP_CLASS and seq[i - 1] in QUIP_CLASS and seq[i - 2] in QUIP_CLASS:
            for j in range(i + 1, len(seq)):
                if seq[j] not in QUIP_CLASS:
                    seq[i], seq[j] = seq[j], seq[i]
                    break
    return seq


def make_plan(paras, batch_no):
    n = len(paras)
    rng = random.Random(batch_no * 1009 + 7)
    has_quote = [bool(QUOTE_RE.search(p)) for p in paras]

    n_part = round(n * PARTICIPIAL_SHARE)
    counts = alloc(n - n_part, OTHER_OPENERS)
    openers = [None] * n

    # dialogue openers only where the source actually has a quote
    quoted = [i for i in range(n) if has_quote[i]]
    rng.shuffle(quoted)
    take = min(counts["dialogue"], len(quoted))
    for i in quoted[:take]:
        openers[i] = "dialogue"
    counts["subject"] += counts["dialogue"] - take
    counts["dialogue"] = 0

    # participial openers, never adjacent
    free = [i for i in range(n) if openers[i] is None]
    rng.shuffle(free)
    chosen = []
    for i in free:
        if len(chosen) == n_part:
            break
        if all(abs(i - c) > 1 for c in chosen):
            chosen.append(i)
    for i in chosen:
        openers[i] = "participial"

    rest = [k for k, v in counts.items() for _ in range(v)]
    rng.shuffle(rest)
    rest = spread(rest)
    it = iter(rest)
    for i in range(n):
        if openers[i] is None:
            openers[i] = next(it, "subject")

    closers = [k for k, v in alloc(n, CLOSERS).items() for _ in range(v)]
    rng.shuffle(closers)
    closers = no_triple_quip(spread(closers))

    rows = []
    for i, p in enumerate(paras):
        w = count_words(p)
        flag = "long" if w >= 110 else ("short" if w < 45 else "")
        rows.append((openers[i], closers[i], w, flag))
    return rows


def write_plan(batch):
    meta = load_meta(batch)
    paras = read_paragraphs(Path(batch) / "source.txt")
    rows = make_plan(paras, meta["batch"])
    lines = ["local\tglobal\topener\tcloser\tsrc_words\tflag"]
    for i, (o, c, w, f) in enumerate(rows, 1):
        lines.append(f"{i}\t{meta['start'] + i - 1}\t{o}\t{c}\t{w}\t{f}")
    (Path(batch) / "plan.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(rows)


if __name__ == "__main__":
    for b in sys.argv[1:]:
        print(f"{b}: planned {write_plan(b)} paragraphs")
