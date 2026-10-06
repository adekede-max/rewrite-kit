# Cara pakai dengan Jules

## Persiapan (sekali)
1. Taruh seluruh isi folder ini di repo GitHub, lalu hubungkan repo itu ke Jules.
2. Simpan transkrip mentah (YouTube, .srt, .vtt, atau .txt) sebagai `raw.txt`, lalu bersihkan dan potong
   jadi paragraf ~50 kata (tanpa aplikasi HTML, tanpa batas panjang, tanpa API key):
   ```
   python tools/prepare.py raw.txt                  # tulis input/source.txt
   python tools/prepare.py raw.txt --target 60      # kalau mau paragraf sumber lebih panjang
   ```
   Perhatikan baris `mode:`. Kalau tertulis UNPUNCTUATED, transkripmu hampir tanpa tanda baca, jadi
   paragraf dipotong per jumlah kata dan bisa mulai di tengah kalimat. Kalau naskahmu sudah rapi
   per paragraf (dipisah baris kosong), lewati langkah ini dan taruh langsung di `input/source.txt`.
3. Di lokal (atau lewat Task 0 di bawah) jalankan:
   ```
   python tools/split.py            # buat batch_01..batch_NN @200 paragraf + plan.tsv
   python tools/extract_names.py    # buat registry_candidates.md
   ```
4. Commit dan push.

## Task 0 - Registry (satu kali, copy-paste ke Jules)
```
Read AGENTS.md and registry_candidates.md. Using grep on input/source.txt to confirm each
candidate, replace registry.md with the real Character & Form Registry: every character, every
physical form/phase (e.g. human, beast, battle armor, past life), a fixed visual descriptor for
each (face, hair, clothing, body proportions or non-human anatomy), and one Style paragraph
(manhwa/anime style name, rendering, lighting, palette). Format exactly like the current
registry.md: entities as "- Name (Form): descriptor". Do not read input/source.txt in full; use
registry_candidates.md plus targeted grep only. Commit registry.md only.
```

## Task per batch (ganti NN dengan 01, 02, ...; satu task per folder)
```
Follow AGENTS.md exactly for batch_NN. Rewrite all paragraphs, write the image prompts, run
verify.py --final and lint_prompts.py until PASS (max 2 fix rounds, log leftovers in
batch_NN/report.md), then run python tools/assemble.py batch_NN. Commit only batch_NN/ and
output/batch_NN/.
```

## Hasil
`output/batch_NN/` masing-masing berisi `rewrite.txt` (200 paragraf), `prompts.txt` (200 prompt,
penomoran global `[001]`-`[2000]`), dan `report.md`.

## Tips hemat resource
- Jalankan Task 0 dulu dan merge sebelum task batch, supaya semua batch membaca registry yang sama.
- Task batch bisa dijalankan paralel, tapi batch pertama sebaiknya dicek dulu (baca `report.md` dan
  beberapa paragraf) sebelum sisanya dijalankan, supaya kalau ada kebiasaan gaya yang kurang pas,
  cukup `AGENTS.md` yang diperbaiki satu kali.
- Konteks 2 paragraf terakhir untuk paragraf pertama batch N diambil dari `batch_(N-1)/rewrite.txt`;
  kalau batch dijalankan paralel, file itu belum ada dan konteksnya kosong. Jalankan berurutan kalau
  POV/nada antar-batch harus mulus.
