# AGENTS.md - Script rewrite + 4-panel image prompts

One task = one `batch_NN/` folder (200 paragraphs). Work only inside that folder and `output/batch_NN/`.
Never read the whole source or print whole files; use `python tools/show.py` for slices.
Never edit `tools/`, `plan.tsv`, `source.txt`, or other batches. Counting is done by scripts, not by you.

## Rewrite rules (English output)
- POV: third person only (name / he / she / they), even if the source is first person. No I/me/my outside direct quotes. Keep other characters' pronouns consistent. Keep any narrator-focus shifts at the same points as the source.
- Same number of paragraphs as source. Never merge or split.
- Each paragraph = exactly 4 sentences, 45-55 words. Cadence: S1 setup ~10-14 words, S2-S3 ~13-18, S4 punchy ~6-10.
- Follow `plan.tsv` for each paragraph's `opener` and `closer` type (do not count ratios yourself):
  - opener: `participial` (-ing phrase + comma), `subject` (name/subject first), `time_place`, `dialogue` (opens with a quote), `question_exclaim`.
  - closer (sentence 4): `quip`, `punchline`, `emotion` (pure feeling, no comment), `cliffhanger`, `rhetorical_question`, `action` (short act, no comment).
- Anti-plagiarism is structural: merge/split sentences, reorder clauses, change idea order inside the paragraph. Synonym swaps alone are not enough.
- Style: at most 1 metaphor/hyperbole per sentence; no stacked intensifiers (utterly, completely, absolutely, genuinely...). Vary rhythm. No modern slang/pop-culture (in-world system terms like level, skill, qi are fine). Dialogue stays as blunt as the source.
- Dramatic adjectives (jagged, crimson, molten, phantom, ancient, sharp, cold, deep...): use each at most ~8 times per batch; vary.
- Keep exact numbers, skill names, titles, stats and world terms WITH the context sentence that frames them. Never turn a precise figure into "hundreds of".
- Keep the most iconic/emotional direct quote (max 1 per paragraph, may be shortened); do not convert all dialogue to indirect speech.
- Keep the narrator's tone (sarcastic stays sarcastic). Do not change cause-and-effect order.
- Must read well aloud (voice-over): no nested clauses, no tongue-twisters, one clear visual scene per paragraph.
- Long source paragraphs are compressed (normal, not a failure). Keep in this order: (1) numbers/skills/titles/terms + context, (2) key actions and cause-effect chain, (3) one iconic quote, (4) tone. Drop secondary atmosphere, repetition, transitions, idle inner thoughts. If a priority-1 item does not fit, log it in report.md with the paragraph number. Paragraphs with `flag=long` that shrink >2x: log what was dropped.
- `flag=short` source paragraphs (<45 words): do not invent content; write the closest valid paragraph and log it in report.md.

## Workflow for batch_NN
1. Read `registry.md` once (characters/forms + style anchor). Do not edit it; log new forms in report.md.
2. Rewrite in sub-batches of 25 paragraphs:
   - `python tools/show.py batch_NN A B` (shows source, plan, and previous rewritten context)
   - append to `batch_NN/rewrite.txt`: plain paragraphs, one blank line between, no numbers/headings (`cat >> ... <<'EOF'`)
   - `python tools/verify.py batch_NN` -> fix ONLY the listed P### in place. Max 2 fix rounds per sub-batch; log leftovers in report.md and move on.
3. When all paragraphs are written: `python tools/verify.py batch_NN --final` (same fix rule).
4. Image prompts: write `batch_NN/prompts_body.txt`, one entry per rewritten paragraph, global numbers from `plan.tsv` (`global` column), 25 at a time, then `python tools/lint_prompts.py batch_NN`; fix ERRORs only.
5. Fill `batch_NN/report.md` (template is already there). Spot-check ~10 random paragraphs for: too close to source structure, POV slips, tone drift, voice-over readability.
6. `python tools/assemble.py batch_NN` -> creates `output/batch_NN/{rewrite.txt,prompts.txt,report.md}`. Commit only `batch_NN/` and `output/batch_NN/`.

## Prompt entry format (1 paragraph = 1 entry = 4 panels, panel k = sentence k)
```
[201] 4-panel symmetric grid (2x2),
Panel 1: Kael (Human Form) gripping the rusted gate, rain hammering the courtyard behind him
Panel 2: ...
Panel 3: ...
Panel 4: ...
```
- Use entity names exactly as in registry.md (`Name (Form)`); each panel must be self-contained (never rely on the previous panel).
- No pronoun at the start of a panel. No generic nouns (boy, girl, man, woman, figure, person, student, warrior, sleeper, speaker, silhouette) unless prefixed with `anonymous`/`generic`/`unnamed`.
- Every body part/expression needs a named owner: `Kael (Human Form)'s eyes snapping open`, never `eyes snapping open`.
- One concrete visual action per panel, at most ~30 words. Do NOT write style or character descriptors: `assemble.py` appends the style anchor and the anchors of named characters to each prompt.
- A character with several forms = separate entities; pick the form valid at that point of the story.
- Background extras: `anonymous crowd member`, `generic imperial guard`.

## Stop conditions
Do not loop: after 2 fix rounds, record remaining failures in report.md and continue. Never ask for the whole source to be pasted.
