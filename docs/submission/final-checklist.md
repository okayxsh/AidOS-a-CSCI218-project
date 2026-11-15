# Final submission checklist

Status at the end of Stage 6 (13 Nov 2026). It covers every deliverable in the CSCI218 guidelines (sections 4–6), plus the items that sit outside the rubric but affect submission.

**Statuses:**
- **COMPLETE:** done and checked.
- **PARTIAL:** exists, but something required is missing.
- **BLOCKED:** needs a team or instructor action that this documentation stage cannot perform.
- **NOT APPLICABLE**

**Done by:**
- **Stage 6:** work done in this documentation session.
- **Team:** must be done by the students themselves.
- **Instructor:** needs the lab instructor.

No due date is recorded here. Check the Turnitin/Moodle links for the real deadlines.

## Group deliverables

| Item | Status | Evidence location | Done by | Remaining action |
|---|---|---|---|---|
| Group report: sections A–J in the required order | PARTIAL | `docs/report/AidOS_Final_Group_Report.docx` (editable) and `.pdf` (preview) | Stage 6 (draft); Team (completion) | Fill every highlighted `[[…]]` placeholder: names, IDs, lab group, instructor, repository URL, submission date. Each member reviews the sections they will present. Update fields in Word (right-click the contents → Update Field) after any edit. |
| Report: figures, tables, captions | COMPLETE | `docs/report/figures/` (diagrams, screenshots, results) | Stage 6 | Replace screenshots only with genuine captures if the UI changes. |
| Report: references | COMPLETE | Section 9 of the report; verification log in `docs/report/report-evidence-map.md` | Stage 6 | The team should cite only sources they agree with. Add any course texts actually used, verified the same way. |
| Report: scientific accuracy | COMPLETE | `docs/report/report-evidence-map.md` (every number traced to an artifact) | Stage 6 | Re-run `experiments/verify_results.py` if any result file is touched. |
| Appendix A: Git link and contribution table | BLOCKED | Report Appendix A (template with placeholders) | Team | Create the shared repository and commit genuine work under your own identities (`docs/submission/git-and-reproducibility.md`, "Stage 6 update"). Then fill the table from that evidence. |
| Appendix B: industry meeting log and mentor form | NOT APPLICABLE | Report Appendix B states it is not applicable | — | Do not claim the bonus. No partner was approved or engaged. |
| Code: shared Git repository whose history shows all members | BLOCKED | Local repository: `main`, no commits, no remote | Team | As for Appendix A. **This is the largest open risk.** |
| Code: README with install and run | COMPLETE | `README.md`; report Appendix C.4 | — | Add the repository URL once it exists. |
| Experiment artifacts and replication materials | COMPLETE | `experiments/results/` (8 runs; SHA-256 checksums re-verified 13 Nov 2026); `experiments/*.py` | — | Commit them (about 7 MB). Never edit the frozen runs. |
| Live online demonstration | PARTIAL | `docs/submission/final-demo-runbook.md` (pre-flight checks run 13 Nov 2026) | Team | Rehearse end to end at least twice. Assign speakers. Record a fallback screen capture. |
| Demo fallback material | PARTIAL | `docs/report/figures/screenshots/` (9 genuine captures) | Team | Also capture: a replay result, a dispatched ledger, and the Evaluate paired-comparison and limitations panels (listed in the runbook). |

## Individual deliverables

| Item | Status | Evidence location | Done by | Remaining action |
|---|---|---|---|---|
| Viva preparation (every member, every part) | PARTIAL | `docs/submission/viva-question-bank.md` (49 questions); `docs/submission/viva-preparation.md` | Team | Each member practises every question aloud, especially parts they did not build (cap rule: 55/80). |
| Contribution and reflection statement (1–2 pages each) | BLOCKED | Template: `docs/submission/reflection-template.md` | Team (each student) | Write truthfully, with evidence from the repository. Never write one for another member. |

## Confirmations and policy

| Item | Status | Evidence location | Done by | Remaining action |
|---|---|---|---|---|
| Sugeno instead of Mamdani | BLOCKED (pending) | `docs/submission/instructor-confirmation-request.md` §1; report §4.3.5 | Instructor | Ask early. A "no" would mean substantial rework. |
| Topic registration and technique combination | BLOCKED (pending) | Same document, §2 | Instructor | Confirm the registration is on record. |
| AI-tool use rules (subject descriptor) | BLOCKED (pending) | Same document, §3; report Appendix E (placeholder) | Team and Instructor | Read the descriptor, then complete Appendix E and the disclosure in each reflection. |
| Moodle/Turnitin submission | BLOCKED | — | Team | Submit the report, the repository link and the individual statements by the deadlines shown on Moodle. **Not done by this session.** |

## Done in Stage 6 (for reference)

- **Report:** editable Word report with an updatable contents page, lists of figures and tables, numbered headings, real Word equations, and a PDF preview.
- **Figures:** 6 technical diagrams and a membership-function chart drawn from the production configuration. 9 genuine screenshots of the running system, all with synthetic-data labels. The selected experiment figures.
- **References:** 24 references, each checked against Crossref, arXiv, zbMATH, publisher or library records, or official documentation. Course documents are cited as supplied.
- **Submission documents:**
  - the final demo runbook, with pre-flight checks actually run;
  - a 49-question viva bank;
  - a reflection template;
  - an instructor confirmation request;
  - this checklist;
  - the report evidence map.
- **Documentation fixes:**
  - outdated version numbers in `docs/api-contract.md`;
  - an untraceable "600 scenarios" claim in `docs/algorithms/allocation-formulation.md`;
  - a misattributed sensitivity range in `docs/submission/viva-preparation.md`.
- **Final verification (13 Nov 2026):**
  - backend: 288 tests passed, Ruff clean;
  - frontend: typecheck, lint, format, 81 tests and the build all passed;
  - smoke test passed;
  - `verify_results.py` passed;
  - all 8 result folders match their checksums.
