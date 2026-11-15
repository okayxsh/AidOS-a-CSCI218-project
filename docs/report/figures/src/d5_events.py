from lib import AMBER, INK, MUTED, NAVY, SVG, TEAL

W = 1600
SZ, TS, LH, PAD = 24, 28, 34, 18
MX, MW = 20, 860
RX, RW = 930, 650
GAP = 34

steps = [
    (
        "1  Request",
        ["`POST …/sessions/{id}/events`", "body: `expected_version`, `event`"],
        None,
        "teal",
    ),
    (
        "2  Event schema  ·  `events.py`",
        ["8 event types; unknown fields rejected"],
        ["422 `validation_error`"],
        "primary",
    ),
    (
        "3  Version check  ·  `store.mutate`",
        ["per-session lock;", "`expected_version` must match"],
        ["409 `version_conflict`"],
        "primary",
    ),
    (
        "4  State check  ·  `fsm.py`",
        ["only ACTIVE; at most 200 events"],
        ["409 `invalid_transition`", "422 `too_many_events`"],
        "primary",
    ),
    (
        "5  Reducer on a copy  ·  `reducer.py`",
        [
            "applies the event to a copy,",
            "then re-validates the scenario;",
            "a commit deducts stock and requests",
        ],
        [
            "422 `unknown_zone`  `unknown_resource`",
            "    `duplicate_zone`  `insufficient_stock`",
            "    `no_change`  `last_zone`  `invalid_result`",
            "    `no_plan`  `invalid_plan`",
            "409 `stale_plan` (old snapshot hash)",
        ],
        "teal",
    ),
    (
        "6  Recompute  ·  `pipeline.compare`",
        [
            "fuzzy urgency, all 4 policies,",
            "independent validator",
            "~recommendations consume nothing",
        ],
        ["503 `solver_failed`", "500 `engine_invariant` (stores ERROR)"],
        "teal",
    ),
    (
        "7  Hashes (SHA-256)",
        ["snapshot, event id and outcome", "~outcome: scores, plans, dispatch"],
        None,
        "primary",
    ),
    (
        "8  Store new state",
        ["version + 1, step appended;", "commit: ledger entry appended"],
        None,
        "teal",
    ),
]


def height(items, rej):
    h = 77 + (len(items) - 1) * LH + 22
    if rej:
        h = max(h, 44 + (len(rej) - 1) * LH + 30)
    return h


ys, y = [], 20
for t, items, rej, kind in steps:
    h = height(items, rej)
    ys.append((y, h))
    y += h + GAP
main_end = y - GAP

TY = main_end + 44
TH = 236
RY = TY + TH + 30
RH = 250
H = RY + RH + 20
s = SVG(W, H)

for i, ((t, items, rej, kind), (y, h)) in enumerate(zip(steps, ys, strict=False)):
    s.box(MX, y, MW, h, t, items, kind=kind, size=SZ, tsize=TS, lh=LH, pad=PAD)
    if i < len(steps) - 1:
        s.arrow([(MX + 90, y + h), (MX + 90, y + h + GAP)], TEAL)
    if rej:
        cy = y + 44
        s.rect(RX, y, RW, h, stroke=AMBER, sw=1.5)
        for j, line in enumerate(rej):
            s.text(
                RX + 18,
                y + 44 + j * LH,
                line,
                size=24 if j == 0 or line[0] != " " else 24,
                fill=INK,
            )
        s.arrow([(MX + MW, y + h / 2), (RX, y + h / 2)], AMBER)
s.text(RX, 52, "Rejected: event not applied,", size=27, fill=AMBER, weight=700)
s.text(RX, 88, "stored session unchanged", size=27, fill=AMBER, weight=700)
s.text(RX, 122, "(except engine_invariant, which stores ERROR)", size=21, fill=MUTED)

# event types
s.panel(20, TY, W - 40, TH, "The eight event types", size=28)
ev = [
    ("zone_added", "add a zone"),
    ("urgency_changed", "set ratings"),
    ("supply_arrived", "stock up"),
    ("supply_lost", "stock down"),
    ("request_updated", "set a request"),
    ("zone_resolved", "remove a zone"),
    ("time_advanced", "clock + 1"),
    ("plan_committed", "dispatch a plan"),
]
cw = (W - 80) / 4
for i, (n, d) in enumerate(ev):
    x = 44 + (i % 4) * cw
    yy = TY + 88 + (i // 4) * 76
    s.text(x, yy, n, size=24, fill=TEAL if n == "plan_committed" else NAVY, weight=700, mono=True)
    s.text(x, yy + 30, d, size=22, fill=MUTED)

# replay strip
s.panel(20, RY, W - 40, RH, "Replay, export and import  ·  `session.py`", size=28)
bw, bg = 350, 40
bx = [40 + i * (bw + bg) for i in range(4)]
by, bh = RY + 60, 170
boxes = [
    ("Export", ["scenario, config,", "events, hashes"]),
    ("Import", ["POST /import", "~checks the snapshot hash"]),
    ("Replay", ["reset, start, re-apply", "~all or nothing (422)"]),
    ("Verify", ["recomputed hashes", "match the recorded ones"]),
]
for i, (t, items) in enumerate(boxes):
    s.box(
        bx[i],
        by,
        bw,
        bh,
        t,
        items,
        kind="teal" if i == 3 else "primary",
        size=SZ,
        tsize=TS,
        lh=LH,
        pad=PAD,
    )
    if i < 3:
        s.arrow([(bx[i] + bw, by + bh / 2), (bx[i + 1], by + bh / 2)], TEAL)

print("H", H)
print(s.save("d5_event_pipeline"))
