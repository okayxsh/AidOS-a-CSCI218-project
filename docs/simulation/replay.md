# Replay, export and import

Code: `apps/api/aidos/simulation/session.py` (`replay`, `export_session`, `import_session`).

## Replay inside a session

`POST /api/simulation/sessions/{id}/replay {expected_version, events: [...]}` resets the session, starts it and applies the events in order.

- **All or nothing.** If any event is rejected (or the solver fails), the call returns 422 `replay_failed` with the index of the failing event (`details[0].path = "events.<i>"`), and the session stays exactly as it was before the call.
- **Order is preserved.** Events are applied in the order given; the same events in a different order are a different run (tested).
- **No duplication.** Replay always starts from the initial snapshot after a reset, so a supply arrival replayed twice is counted once per replay, never on top of the previous run (tested).

## Export format (`aidos-simulation` 1.0)

`GET /api/simulation/sessions/{id}/export` returns a self-contained JSON document:

```json
{
  "format": "aidos-simulation",
  "format_version": "1.0",
  "engine_version": "0.3.0",
  "fuzzy_version": "1.0",
  "scenario_id": "triage-demo-001",
  "initial_snapshot_hash": "f24844f5…",
  "initial_scenario": { "...": "the full validated scenario at step 0" },
  "config": { "policy": "aidos", "epsilon": 1.0, "resource_weights": {}, "min_coverage": 0.25, "time_limit_s": 5.0 },
  "events": [
    { "seq": 1, "event_id": "e001-6cc0a746", "event": { "type": "urgency_changed", "zone_id": "zone-b", "severity": 9.0, "vulnerability": null, "time_criticality": null } }
  ],
  "outcomes": [
    { "seq": 0, "snapshot_hash": "…", "outcome_hash": "4913474…" },
    { "seq": 1, "snapshot_hash": "…", "outcome_hash": "5cbedce…" }
  ]
}
```

- The initial scenario is embedded, so a file replays even if the built-in fixture later changes.
- Each event is stored in its validated, normalised form with its sequence number. Event IDs are content-addressed (sequence number + hash of the event and the snapshot it applied to), so they do not depend on timestamps or memory.
- `outcomes` records, for every step, the snapshot hash and the outcome hash (scores, every policy's plan and status, dispatched units; no timings).

## Import and verification

`POST /api/simulation/import <document>` creates a new session from a document and replays it. The import:

1. checks `format` and `format_version`;
2. validates `initial_scenario` with the normal scenario validation, and checks it hashes to `initial_snapshot_hash` (a tampered or mismatched scenario is rejected);
3. validates the configuration and each event against the event schema, in order, with consecutive `seq` numbers;
4. replays every event (all or nothing, as above);
5. compares each replayed step's snapshot hash and outcome hash with `outcomes`.

The response is `{session, verification}` where `verification` is `{checked, matches, first_mismatch_seq, engine_version_recorded}`. A mismatch does not reject the import: it reports the first step whose logical outcome differs, for example after an engine change. A document without `outcomes` is replayed with `checked: false`.

Malformed documents (wrong format, missing or invalid scenario, unknown event type, out-of-order events, events that cannot be applied) are rejected with 422 `replay_failed` and create no session.

## What "deterministic replay" means here

Given the same document and the same engine version, a replay produces the same snapshot hashes, scores, plans, statuses, event IDs and outcome hashes at every step. This is checked:

- in unit tests (replay, export → import round trip, tampered outcome detected);
- in `tests/unit/test_simulation.py::test_the_recorded_demo_script_still_reproduces`, which replays the committed demo file and requires every recorded outcome to match. If an engine change alters any decision, this test fails and the demo file must be regenerated deliberately;
- in `scripts/smoke_test.py` over HTTP: run the demo events, reset, replay, compare every outcome hash, export and re-import.

Runtimes are excluded from every comparison, because they vary between runs and machines.
