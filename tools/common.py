"""Shared helpers for the rewrite kit. Run every tool from the repo root."""
import json
import re
from pathlib import Path

# ---- thresholds (edit here if the guide changes) ----
PARA_MIN, PARA_MAX, SENT_REQUIRED = 45, 55, 4
PARTICIPIAL_WARN, PARTICIPIAL_FAIL = 0.12, 0.15
DRAMATIC_WARN, DRAMATIC_FAIL = 8, 10          # uses per batch (~200 paragraphs)
OPENER_WORD_WARN = 0.30                        # same first word in >30% of paragraphs

DRAMATIC = ["jagged", "crimson", "molten", "phantom", "ancient", "sharp", "cold",
            "deep", "shattered", "blazing", "ethereal", "savage", "abyssal", "unholy"]
INTENSIFIERS = ["utterly", "completely", "absolutely", "genuinely", "totally",
                "entirely", "truly", "incredibly", "unbelievably"]
SLANG = ["wall hack", "wall hacks", "peak comedy", "five-star", "no cap",
         "built different", "lowkey", "highkey", "goated", "yeet", "bruh", "cringe"]
ING_EXCEPT = {"during", "morning", "evening", "nothing", "something", "anything",
              "everything", "string", "spring", "building", "ceiling", "wedding",
              "painting", "feeling", "meeting", "training", "clothing"}

QUOTE_RE = re.compile(r'[“"](.*?)[”"]', re.S)
FIRST_PERSON_RE = re.compile(r"\b(?:I|I['’](?:m|ll|ve|d)|[Mm]e|[Mm]y|[Mm]ine|[Mm]yself)\b")
SPEECH = {"said", "says", "shouted", "whispered", "asked", "replied", "muttered", "cried", "yelled",
          "snapped", "growled", "laughed", "answered", "added", "called", "hissed", "murmured",
          "sneered", "declared", "roared", "screamed", "sighed", "demanded", "warned", "groaned",
          "barked", "continued", "echoed", "stammered", "gasped", "scoffed", "retorted"}
ABBR_RE = re.compile(r"\b(Mr|Mrs|Ms|Dr|St|Jr|Sr|vs)\.")


def read_paragraphs(path):
    """Paragraphs are separated by blank lines; if there are none, one per line."""
    text = Path(path).read_text(encoding="utf-8").replace("\r\n", "\n").strip()
    if not text:
        return []
    chunks = re.split(r"\n\s*\n", text) if re.search(r"\n\s*\n", text) else text.split("\n")
    return [" ".join(c.split()) for c in chunks if c.strip()]


def count_words(text):
    return len(text.split())


def strip_quotes(text):
    return QUOTE_RE.sub(" ", text)


def split_sentences(text):
    """Sentence splitter that does not break inside direct quotes."""
    t = " ".join(text.split())
    t = ABBR_RE.sub(lambda m: m.group(1) + "\x02", t)

    def mask(m):
        inner = m.group(1)
        rest = m.string[m.end():].lstrip()
        ended = bool(re.search(r"[.!?…]\s*$", inner))
        tag = any(w.strip(".,!?\"'").lower() in SPEECH for w in rest.split()[:3])
        boundary = ended and not tag and (rest == "" or rest[0].isupper() or rest[0] in "\"“")
        return '"' + re.sub(r"[.!?…]+", "", inner) + '"' + ("." if boundary else "")

    t = QUOTE_RE.sub(mask, t)
    parts = re.split(r"(?<=[.!?])[\"'”’)\]]*\s+(?=[\"“'‘(\[]?[A-Z0-9])", t)
    return [p.replace("\x02", ".").strip() for p in parts if p.strip()]


def is_participial(text):
    """True if the paragraph opens with an -ing phrase followed by a comma."""
    t = text.lstrip()
    if not t or t[0] in "\"“'‘":
        return False
    words = t.split()
    w0 = re.sub(r"[^A-Za-z]", "", words[0]).lower()
    if len(w0) < 5 or not w0.endswith("ing") or w0 in ING_EXCEPT:
        return False
    return "," in " ".join(words[:12])


def batch_path(batch):
    return Path(batch)


def load_meta(batch):
    return json.loads((Path(batch) / "meta.json").read_text(encoding="utf-8"))


def load_plan(batch):
    p = Path(batch) / "plan.tsv"
    if not p.exists():
        return []
    rows = []
    lines = p.read_text(encoding="utf-8").strip().split("\n")
    head = lines[0].split("\t")
    for ln in lines[1:]:
        rows.append(dict(zip(head, ln.split("\t"))))
    return rows


def parse_registry(path="registry.md"):
    """Returns (style_text, {entity_key: descriptor})."""
    p = Path(path)
    if not p.exists():
        return "", {}
    text = p.read_text(encoding="utf-8")
    style, entities, section = [], {}, None
    for ln in text.split("\n"):
        if ln.startswith("## "):
            section = ln[3:].strip().lower()
            continue
        if section == "style" and ln.strip():
            style.append(ln.strip())
        elif section == "entities":
            m = re.match(r"^-\s+(.+?):\s*(.+)$", ln.strip())
            if m:
                entities[m.group(1).strip()] = m.group(2).strip()
    return " ".join(style), entities
