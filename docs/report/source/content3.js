// Appendices of the AidOS final report.
const fs = require('fs');
const path = require('path');

module.exports = function part3(D) {
  const { P, H1, H2, B, T, F, V, md, ROOT } = D;
  const cfg = JSON.parse(fs.readFileSync(path.join(ROOT, 'apps/api/aidos/config/fuzzy_rules.json'), 'utf8'));
  const ruleRows = cfg.rules.map((r) => [r.id, r.if.severity, r.if.time_criticality, r.if.vulnerability, r.then]);
  const scaling = md('docs/evaluation/results-tables.md', '## 9. Runtime scaling', 0);
  const runs = V.runs; // [{id, kind, files, ok, status}]

  return [
    { t: 'appendixStart' },
    H1('Git Repository and Team Contribution Table', 'appA', { pageBreak: true }),
    P('Git repository link: [[INSERT the shared GitHub/GitLab repository URL]]'),
    P('The guidelines require that the repository history shows contributions from all members and that this table reflects actual work. **At the time this report was prepared, the local repository had been initialised but contained no commits and no remote.** No history has been created on any member\'s behalf. Each member must commit their own genuine work under their own identity, and the table below must be completed from that evidence (commits, specific functions or modules, experiments, report sections). Contribution shares must be agreed by the team and must be consistent with the repository.'),
    T({
      id: 'contrib', caption: 'Team contribution table (template from the CSCI218 guidelines, Appendix A).',
      cols: [1.7, 3.0, 0.8, 1.0],
      header: ['Student name & ID', 'Main contributions (code, report sections, experiments)', 'Est. share (%)', 'Signature'],
      rows: [
        ['[[Student 1 name]] [[ID]]', '[[Specific work with evidence: commits, files, sections]]', '[[ ]]', ''],
        ['[[Student 2 name]] [[ID]]', '[[Specific work with evidence]]', '[[ ]]', ''],
        ['[[Student 3 name]] [[ID]]', '[[Specific work with evidence]]', '[[ ]]', ''],
        ['[[Student 4 name]] [[ID]]', '[[Specific work with evidence]]', '[[ ]]', ''],
        ['[[Student 5 name, if applicable]] [[ID]]', '[[Specific work with evidence]]', '[[ ]]', ''],
      ],
    }),
    P('Open items for the team, also tracked in `docs/submission/final-checklist.md`: (1) instructor confirmation that a documented zero-order Sugeno system satisfies the fuzzy-logic component (the specification preferred Mamdani); (2) confirmation of topic registration and the technique combination; (3) the subject descriptor\'s rules on AI-tool use (Appendix E). None of these has been confirmed at the time of writing.'),

    H1('Industry Engagement', 'appB'),
    P('**Not applicable.** No industry partner was approved for this project, and no meetings with a partner mentor took place. The guidelines\' industry meeting log and mentor feedback form are therefore not included, and no bonus marks are claimed. Choosing a Dubai Humanitarian use case does not by itself constitute industry engagement; the project uses only the published use-case description [@dhproj].'),

    H1('Supplementary Technical Material', 'appC'),
    H2('Complete rule base (configuration version 1.0)'),
    T({ id: 'allrules', caption: 'The 27 rules of the production fuzzy configuration (apps/api/aidos/config/fuzzy_rules.json).', cols: [0.6, 1.2, 1.4, 1.2, 1.2], header: ['Rule', 'Severity', 'Time criticality', 'Vulnerability', 'Urgency'], rows: ruleRows, size: 15 }),
    H2('API endpoints'),
    T({
      id: 'endpoints', caption: 'Complete list of API endpoints.',
      cols: [0.8, 3.3, 2.4], size: 15,
      header: ['Method', 'Path', 'Purpose'],
      rows: [
        ['GET', '`/api/health`', 'Version, engine stage, policies'],
        ['GET', '`/api/scenarios`', 'List the scenario fixtures'],
        ['GET', '`/api/scenarios/{scenario_id}`', 'Load and validate one scenario; returns its snapshot hash'],
        ['POST', '`/api/urgency/evaluate`', 'Fuzzy scores with full traces'],
        ['GET', '`/api/urgency/config`', 'The published fuzzy configuration'],
        ['POST', '`/api/allocations/compare`', 'Run selected policies on one snapshot, with validation and metrics'],
        ['POST', '`/api/simulation/sessions`', 'Create a session from a scenario'],
        ['POST', '`/api/simulation/sessions/{id}/start|pause|resume|complete|reset`', 'State-machine actions (with expected_version)'],
        ['POST', '`/api/simulation/sessions/{id}/events`', 'Apply one event'],
        ['POST', '`/api/simulation/sessions/{id}/replay`', 'Replay and compare outcome hashes'],
        ['GET', '`/api/simulation/sessions/{id}`, `/history`, `/steps/{seq}`, `/diff`, `/export`', 'Read the session, its history, a step, a diff or an export'],
        ['POST', '`/api/simulation/import`', 'Import an exported session and verify it'],
        ['GET', '`/api/evaluation/runs`, `/runs/{run_id}`, `/runs/{run_id}/tables/{table}`', 'Read finished experiment artifacts'],
      ],
    }),
    H2('Demonstration scenarios'),
    P('Nine synthetic fixtures are provided in `data/scenarios/`: `triage-demo-001` (three-zone shortage, the default), `late-critical-arrival`, `medical-escalation-006`, `supply-arrival-007`, `severe-shortage-008`, `competing-emergency-009`, `coastal-storm-005`, `no-scarcity` and `zero-stock`. `data/simulations/triage-demo-escalation.json` is a replayable event script with recorded outcome hashes.', { align: 'left' }),
    H2('Reproducing the system and the results'),
    T({
      id: 'commands', caption: 'Commands to install, run, test and reproduce (from the repository root unless stated).',
      cols: [1.6, 4.6], size: 15,
      header: ['Task', 'Command'],
      rows: [
        ['Install backend', '`cd apps/api && uv sync`'],
        ['Run backend', '`cd apps/api && uv run uvicorn aidos.main:app --port 8000`'],
        ['Install and run frontend', '`cd apps/web && npm ci && npm run dev`'],
        ['Backend tests and lint', '`cd apps/api && uv run pytest && uv run ruff check ../..`'],
        ['Frontend checks', '`cd apps/web && npm run typecheck && npm run lint && npm run test && npm run build`'],
        ['Smoke test (engine running)', '`python scripts/smoke_test.py`'],
        ['Re-run the benchmark', '`cd apps/api && uv run python ../../experiments/run_benchmarks.py --preset extended`'],
        ['Verify a run', '`uv run python ../../experiments/verify_results.py extended-20261112T100136Z --against standard-20261112T100617Z`'],
        ['Figures and tables', '`uv run --group analysis python ../../experiments/plot_results.py <run_id>` and `report_results.py <run_id>`'],
        ['Supplementary experiments', '`uv run python ../../experiments/{greedy_equivalence,floor_sweep,fuzzy_sensitivity,dynamic_controlled,runtime_benchmark}.py`'],
      ],
    }),

    H1('Supplementary Experiment Evidence', 'appD'),
    H2('Run identifiers and integrity'),
    P(`Every run directory under \`experiments/results/\` holds its configuration, raw CSV, a summary and a \`manifest.json\` with a SHA-256 checksum of every output file. Runs are never overwritten. On ${V.verifDate} every checksum was recomputed and compared with its manifest ({tab:runs}). The Stage 4 runs record their source revision as "unavailable" because the folder was not yet a git repository when they were produced.`),
    T({ id: 'runs', caption: 'Result directories and checksum verification.', cols: [3.4, 1.6, 0.6, 1.2], size: 15, header: ['Run directory', 'Role', 'Files', 'Checksums'], rows: runs.map((r) => [`\`${r.id}\``, r.role, String(r.files), r.ok]) }),
    H2('Stage 4 scaling study'),
    P('Measured under heavier background load than the Stage 5 benchmark; kept for completeness and not comparable with {tab:runtime}.'),
    T({ id: 'scaling', caption: 'Stage 4 scaling study: median runtime (ms) by number of zones.', cols: [0.8, 1, 1.3, 1, 1.3, 1.4], align: ['r', 'r', 'r', 'r', 'r', 'r'], header: scaling.header, rows: scaling.rows }),
    H2('Additional figures'),
    F({ id: 'r_scarcity', path: V.res('fig3_scarcity'), widthCm: 15, caption: 'Stage 4: metrics by scarcity family (A low, B moderate, C severe).' }),
    F({ id: 'r_tradeoff', path: V.res('fig4_tradeoff'), widthCm: 11.5, caption: 'Stage 4: urgency-weighted coverage against lowest-zone coverage, family means. Greedy is hidden under AidOS because their plans are identical.' }),
    F({ id: 'r_runtime4', path: V.res('fig5_runtime'), widthCm: 13, caption: 'Stage 4 scaling study (heavier background load; see {sec:runtime}).' }),
    F({ id: 'r_realloc', path: V.res('fig6_dynamic_reallocation'), widthCm: 15, caption: 'Stage 4 recommendation mode: units reallocated per event type.' }),
    F({ id: 'r_dispatch', path: V.res('fig7_dispatch'), widthCm: 15, caption: 'Stage 4 dispatch mode: outcomes per policy. The equity advantage shown here is driven by the late, urgent zone ({sec:dynamic}).' }),

    H1('Declaration on the Use of AI Tools', 'appE'),
    P('[[TEAM TO COMPLETE according to the CSCI218 subject descriptor\'s rules on AI-tool use, which the project guidelines defer to.]] For accuracy, the project\'s contribution log records that the prototype (engine, simulator, evaluation, dashboard and documentation) was produced in AI-assisted development sessions using Claude Code, directed by a team member, and that this report was drafted with the same assistance from the project\'s own documentation and artifacts. The team must state here how AI tools were used, which parts each member reviewed and can explain, and confirm that the declaration complies with the descriptor.'),
  ];
};
