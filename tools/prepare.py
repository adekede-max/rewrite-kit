"""Clean a raw YouTube transcript (or .srt/.vtt) and cut it into ~50-word paragraphs.
No length limit, no API key. Output goes to input/source.txt (blank-line separated).

Usage:
  python tools/prepare.py raw.txt [-o input/source.txt] [--target 50]

Punctuated text: paragraphs end at sentence boundaries (50-62 words, closest to target).
Unpunctuated text (typical auto-captions): cut every ~50 words, preferring a nearby comma
or conjunction; the tool warns because paragraphs may start mid-sentence.
"""
import argparse
import re
import statistics
import sys
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("raw")
ap.add_argument("-o", "--output", default="input/source.txt")
ap.add_argument("--target", type=int, default=50)
args = ap.parse_args()

TARGET = args.target
LO, HI = round(TARGET * 0.8), round(TARGET * 1.25)
CONJ = {"and", "but", "so", "then", "because", "while", "when", "until", "although", "though",
        "however", "meanwhile", "after", "before", "as", "once", "if"}
ABBR = re.compile(r"\b(Mr|Mrs|Ms|Dr|St|Jr|Sr|vs|etc)\.")
AUDIO = (r"music|musik|applause|laughter|laughs|tawa|tertawa|cheering|tepuk tangan|"
         r"instrumental|inaudible|background (?:music|noise)")


def clean(raw):
    t = raw.replace("\r\n", "\n")
    for a, b in (("&amp;", "&"), ("&quot;", '"'), ("&#39;", "'"), ("&lt;", "<"), ("&gt;", ">"), ("&nbsp;", " ")):
        t = t.replace(a, b)
    t = re.sub(r"</?[a-zA-Z][^>]*>|<\d{2}:\d{2}[^>]*>", "", t)             # VTT inline tags
    t = re.sub(r"^(WEBVTT|NOTE|Kind:|Language:).*$", "", t, flags=re.M)
    t = re.sub(r"\d{1,2}:\d{2}:\d{2}[.,]\d{3}\s*-->\s*\d{1,2}:\d{2}:\d{2}[.,]\d{3}[^\n]*", "", t)
    t = re.sub(r"^\s*\d+\s*$", "", t, flags=re.M)                           # SRT cue numbers
    t = re.sub(r"^\s*\[?\d{1,2}:\d{2}(?::\d{2})?\]?[ \t]*", "", t, flags=re.M)   # timestamps at line start only
    t = re.sub(r"^\s*\d+\s+(?:hours?|minutes?|seconds?)(?:,?\s*\d+\s+(?:minutes?|seconds?))*\s*$", "",
               t, flags=re.M | re.I)
    # only known audio tags: system windows like [Skill: Fireball] are story text and stay
    t = re.sub(rf"[\[\(]\s*(?:{AUDIO})\b[^\]\)]*[\]\)]", "", t, flags=re.I)
    t = re.sub(r"[♪♩♫♬]", "", t).replace(">>", " ")
    lines = []
    for ln in (x.strip() for x in t.split("\n")):
        if ln and (not lines or ln != lines[-1]):
            lines.append(ln)
    return re.sub(r"\s{2,}", " ", " ".join(lines)).strip()


def split_long(w):
    """Cut a long word list into pieces near TARGET, preferring commas/conjunctions."""
    out = []
    while len(w) > HI:
        best = None
        for i in range(LO, min(HI, len(w) - 1) + 1):
            if w[i - 1].endswith((",", ";", ":", "—")) or w[i].lower() in CONJ:
                if best is None or abs(i - TARGET) < abs(best - TARGET):
                    best = i
        cut = best or TARGET
        out.append(w[:cut])
        w = w[cut:]
    if w:
        out.append(w)
    return out


def sentences(text):
    t = ABBR.sub(lambda m: m.group(1) + "\x02", text)
    t = re.sub(r"\.{2,}", lambda m: "\x03" * len(m.group(0)), t)             # ellipsis is not a boundary
    parts = re.split(r"(?<=[.!?])[\"'”’)\]]*\s+(?=[\"“'‘(\[]?[A-Z0-9])", t)
    return [p.replace("\x02", ".").replace("\x03", ".") for p in parts if p.strip()]


text = clean(Path(args.raw).read_text(encoding="utf-8", errors="replace"))
words = text.split()
if not words:
    sys.exit("Nothing left after cleaning.")
ends = len(re.findall(r"[.!?]+(?=\s|$)", text))
punctuated = ends >= len(words) / 40

if punctuated:
    units = []
    for s in sentences(text):
        w = s.split()
        units.extend(split_long(w) if len(w) > HI else [w])
    paras, cur = [], []
    for u in units:
        if not cur:
            cur = list(u)
        elif len(cur) + len(u) <= HI and abs(len(cur) + len(u) - TARGET) <= abs(len(cur) - TARGET):
            cur += u
        else:
            paras.append(cur)
            cur = list(u)
    if cur:
        paras.append(cur)
else:
    paras = split_long(words)

if len(paras) > 1 and len(paras[-1]) < LO and len(paras[-2]) + len(paras[-1]) <= round(TARGET * 1.5):
    paras[-2] += paras.pop()

out = []
for p in paras:
    s = " ".join(p)
    out.append(s[0].upper() + s[1:])
Path(args.output).parent.mkdir(parents=True, exist_ok=True)
Path(args.output).write_text("\n\n".join(out) + "\n", encoding="utf-8")

sizes = [len(p) for p in paras]
off = sum(1 for s in sizes if s < 40 or s > 65)
print(f"mode: {'punctuated (cut at sentence ends)' if punctuated else 'UNPUNCTUATED (cut by word count)'}")
print(f"{len(words)} words -> {len(paras)} paragraphs | min {min(sizes)}, avg {statistics.mean(sizes):.0f}, "
      f"max {max(sizes)} | outside 40-65 words: {off}")
if not punctuated:
    print("WARNING: almost no punctuation found; paragraphs can start mid-sentence. The rewrite still "
          "works, but check the first batch's report.md for POV/sense problems.")
print(f"written: {args.output}")
