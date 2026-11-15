# Report builder (first draft only)

These scripts generated the first draft of `../AidOS_Final_Group_Report.docx` on 13 Nov 2026 from the project's documentation and saved artifacts. **Once the team edits the Word file, the Word file is the master.** Re-running the builder would overwrite those edits.

What is here:
- `content1.js`–`content3.js`: the report text.
- `refs.js`: the verified references (log: `../references-verification.md`).
- `build.js` and `lib.js`: the docx-js builder.
- `word_finalize.ps1`: opens the file in Word, updates the contents and figure/table lists, and exports the PDF.
- `evidence_map.py`: writes `../report-evidence-map.md`.

The numeric tables are read at build time from `docs/evaluation/results-tables.md` and `docs/evaluation/stage5-supplementary.md`, which are generated from the run artifacts. The checksum table is recomputed from `experiments/results/*/manifest.json`.

```bash
cd docs/report/source && npm install
node build.js ../../.. raw.docx ver.json
powershell -File word_finalize.ps1 -InDocx <abs>\raw.docx -OutDocx <abs>\..\AidOS_Final_Group_Report.docx -OutPdf <abs>\..\AidOS_Final_Group_Report.pdf
```

`ver.json` holds the final verification results quoted in the report (Table 19). Update it only from commands actually run.
