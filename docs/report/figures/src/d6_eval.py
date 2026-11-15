import json

from lib import INK, MUTED, NAVY, REPO, RULE, SVG, TEAL

run = REPO / "experiments/results/extended-20261112T100136Z"
man = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
cfg = json.loads((run / "config.json").read_text(encoding="utf-8"))
c = man["counts"]
assert c["static_scenarios"] == 504 and c["static_records"] == 2016
assert c["dynamic_scripts"] == 60 and c["dynamic_steps"] == 420 and c["dispatch_runs"] == 240
assert c["scaling_records"] == 600 and c["failures"] == 0
assert cfg["preset"]["bootstrap_resamples"] == 5000

SZ, TS, LH, PAD = 24, 28, 34, 18
W = 1600
s = SVG(W, 2000)

# ------------------------------------------------------------------ inputs
TY, TH = 20, 400
s.panel(20, TY, 1000, TH, "Static families A–G  ·  `families.py`", size=28)
cols = [44, 100, 600, 880]
heads = ["", "purpose", "stock / requests", "seed base"]
for x, h in zip(cols, heads, strict=False):
    s.text(x, TY + 80, h, size=22, fill=MUTED, weight=700)
fam = [
    ("A", "Low scarcity", "85–110%", "100000"),
    ("B", "Moderate scarcity", "60–85%", "200000"),
    ("C", "Severe scarcity", "25–50%", "300000"),
    ("D", "Unequal urgency", "50–80%", "400000"),
    ("E", "Equal or near-equal urgency", "50–80%", "500000"),
    ("F", "Unequal demand", "50–80%", "600000"),
    ("G", "Multiple shortages", "3 short, 1 ample", "700000"),
]
for i, row in enumerate(fam):
    y = TY + 116 + i * 33
    for j, (x, v) in enumerate(zip(cols, row, strict=False)):
        s.text(
            x,
            y,
            v,
            size=24,
            fill=NAVY if j == 0 else INK,
            weight=700 if j == 0 else 400,
            mono=(j == 3),
        )
s.line(44, TY + 350, 996, TY + 350, stroke=RULE)
s.text(44, TY + 384, "*72 scenarios each = 504*;  seed = base + i", size=24)

s.box(
    1050,
    TY,
    530,
    TH,
    "Dynamic family H",
    [
        "60 scripts (family-B base)",
        "*recommendation:* 7 events,",
        "shared state, 420 steps",
        "*dispatch:* 11 events with",
        "4 dispatches; 240 runs",
        "*scaling:* 5–50 zones,",
        "600 timed rows",
    ],
    size=SZ,
    tsize=TS,
    lh=LH,
    pad=PAD,
)

# ------------------------------------------------------------------ main flow
MX, MW = 20, 1040
MC = 300
BUS = TY + TH + 24
s.line(520, TY + TH, 520, BUS, stroke=TEAL, sw=2)
s.line(1315, TY + TH, 1315, BUS, stroke=TEAL, sw=2)
s.line(MC, BUS, 1315, BUS, stroke=TEAL, sw=2)
s.arrow([(MC, BUS), (MC, BUS + 30)], TEAL)

rows = [
    (
        "1  Four policies, identical inputs",
        [
            "`fcfs`, `greedy`, `aidos`, `aidos_balanced`",
            "same snapshot, same fuzzy scores, frozen config",
        ],
        "teal",
    ),
    (
        "2  Independent validator",
        [
            "all plans valid: 2,016 static, 1,680 step plans",
        ],
        "primary",
    ),
    (
        "3  Metrics",
        [
            "urgency-weighted coverage, lowest zone",
            "coverage, starved zones, Jain index, runtime",
        ],
        "primary",
    ),
    (
        "4  Raw CSV rows",
        [
            "static 2,016  ·  dynamic 1,680 + 240  ·  scaling 600",
        ],
        "primary",
    ),
    (
        "5  Paired statistics  →  `summary.json`",
        [
            "differences per scenario or script",
            "95% bootstrap CI (5,000 resamples), d_z",
            "4 primary tests, AidOS vs FCFS:",
            "exact sign test, Holm-adjusted",
        ],
        "teal",
    ),
    (
        "6  Manifest",
        [
            "versions, counts, SHA-256 of every file",
        ],
        "primary",
    ),
    (
        "7  Verify, then report",
        [
            "`verify_results.py`, then figures and tables",
        ],
        "teal",
    ),
]
GAP = 32
y = BUS + 30
first_y = y
for i, (t, items, kind) in enumerate(rows):
    h = 77 + (len(items) - 1) * LH + 24
    s.box(MX, y, MW, h, t, items, kind=kind, size=SZ, tsize=TS, lh=LH, pad=PAD)
    if i < len(rows) - 1:
        s.arrow([(MC, y + h), (MC, y + h + GAP)], TEAL)
    last_y, last_h = y, h
    y += h + GAP
end = y - GAP

# ------------------------------------------------------------------ supplementary branch
SX, SW = 1100, 480
s.panel(SX, first_y, SW, end - first_y, "Stage 5 supplementary", size=28)
s.text(SX + 20, first_y + 66, "exploratory, new seeds", size=22, fill=MUTED)
sup = [
    ("Greedy equivalence", "36,240 + 700 instances"),
    ("Floor sweep", "280 scenarios × 6 floors"),
    ("Fuzzy sensitivity", "280 scenarios × 11 variants"),
    ("Controlled dynamic", "120 scripts"),
    ("Runtime benchmark", "2,100 timed runs"),
    ("Stage 4 audit", "21 checks"),
]
by = first_y + 92
bh = 104
for t, d in sup:
    s.box(SX + 20, by, SW - 40, bh, t, [d], size=24, tsize=26, lh=LH, pad=16)
    by += bh + 14
s.text(SX + 20, by + 26, "own runs, fig9–fig12", size=22, fill=MUTED)
s.arrow([(MX + MW, first_y + 60), (SX, first_y + 60)], NAVY, dash="6 5")
s.arrow([(SX, last_y + last_h / 2), (MX + MW, last_y + last_h / 2)], NAVY, dash="6 5")

s.h = end + 20
print("end", end, "sup", by + 26)
print(s.save("d6_evaluation_method"))
