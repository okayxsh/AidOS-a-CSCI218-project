import json

from lib import MUTED, REPO, RULE, SVG, TEAL

cfg = json.loads((REPO / "apps/api/aidos/config/fuzzy_rules.json").read_text(encoding="utf-8"))
terms = cfg["inputs"]["severity"]["terms"]
for name in ("time_criticality", "vulnerability"):
    assert cfg["inputs"][name]["terms"] == terms
assert terms["low"]["points"] == [0, 0, 2, 5] and terms["medium"]["points"] == [2, 5, 8]
assert terms["high"]["points"] == [5, 8, 10, 10]
assert {k: v["value"] for k, v in cfg["output"]["terms"].items()} == {
    "low": 12.5,
    "moderate": 37.5,
    "high": 62.5,
    "critical": 87.5,
}
assert len(cfg["rules"]) == 27

W, H = 1600, 872
s = SVG(W, H)

BW, GX = 480, 60
xs = [20 + i * (BW + GX) for i in range(3)]
BH = 212
Y1, Y2 = 20, 20 + BH + 70
stages = [
    (
        "1  Crisp ratings",
        [
            "severity, time criticality,",
            "vulnerability: each 0–10",
            "~checked: finite and in range",
        ],
        "teal",
    ),
    (
        "2  Fuzzify",
        [
            "low (0, 0, 2, 5)  trapezoid",
            "medium (2, 5, 8)  triangle",
            "high (5, 8, 10, 10)  trapezoid",
            "~degrees sum to 1 (Ruspini)",
        ],
        "primary",
    ),
    (
        "3  Fire 27 rules",
        [
            "complete 3 × 3 × 3 rule base",
            "strength α = μ(s) · μ(t) · μ(v)",
            "(product t-norm)",
        ],
        "primary",
    ),
    (
        "4  Sugeno average",
        [
            "score = Σ α·c / Σ α",
            "constant outputs c: low 12.5,",
            "moderate 37.5, high 62.5,",
            "critical 87.5",
        ],
        "primary",
    ),
    (
        "5  Urgency score",
        [
            "0–100, rounded to 4 decimals",
            "low [0, 25), moderate [25, 50),",
            "high [50, 75), critical [75, 100]",
        ],
        "teal",
    ),
    (
        "6  Explanation",
        [
            "memberships and fired rules",
            "contribution = (α / Σ α) · c",
            "contributions sum to the score",
            "~(before rounding)",
        ],
        "primary",
    ),
]
for i, (t, items, kind) in enumerate(stages):
    x = xs[i % 3]
    y = Y1 if i < 3 else Y2
    s.box(x, y, BW, BH, t, items, kind=kind, size=24, tsize=28, lh=34, pad=20)
for i in (0, 1):
    s.arrow([(xs[i] + BW, Y1 + BH / 2), (xs[i + 1], Y1 + BH / 2)], TEAL)
    s.arrow([(xs[i] + BW, Y2 + BH / 2), (xs[i + 1], Y2 + BH / 2)], TEAL)
# 3 -> 4: down, left, down
my = Y1 + BH + 35
s.arrow(
    [(xs[2] + BW / 2, Y1 + BH), (xs[2] + BW / 2, my), (xs[0] + BW / 2, my), (xs[0] + BW / 2, Y2)],
    TEAL,
)

# worked example strip
EY = Y2 + BH + 40
s.panel(
    20,
    EY,
    W - 40,
    H - EY - 20,
    "Worked example: Zone C of triage-demo-001, ratings s = 7, t = 7, v = 5",
    size=27,
)
cx = [48, 150, 690, 820, 1100]
hy = EY + 84
heads = [
    ("rule", "start"),
    ("antecedent (s, t, v) → term", "start"),
    ("α", "end"),
    ("c", "end"),
    ("contribution", "end"),
]
offs = [0, 0, 60, 60, 0]
for (h, a), x, o in zip(heads, cx, offs, strict=False):
    s.text(x + o, hy, h, size=24, fill=MUTED, weight=700, anchor=a)
rows = [
    ("R26", "high, high, medium → critical", "4/9", "87.5", "38.889"),
    ("R17", "medium, high, medium → high", "2/9", "62.5", "13.889"),
    ("R23", "high, medium, medium → high", "2/9", "62.5", "13.889"),
    ("R14", "medium, medium, medium → moderate", "1/9", "37.5", "4.167"),
]
for i, r in enumerate(rows):
    y = hy + 38 * (i + 1)
    s.text(cx[0], y, r[0], size=24, mono=True)
    s.text(cx[1], y, r[1], size=24)
    s.text(cx[2] + 60, y, r[2], size=24, anchor="end")
    s.text(cx[3] + 60, y, r[3], size=24, anchor="end")
    s.text(cx[4], y, r[4], size=24, anchor="end")
s.line(cx[0], hy + 38 * 4 + 14, cx[4], hy + 38 * 4 + 14, stroke=RULE)
s.text(cx[4], hy + 38 * 5 + 6, "Σ = 637.5 / 9 = 70.8333", size=24, weight=700, anchor="end")

rx = 1170
s.arrow([(cx[4] + 14, hy + 95), (rx, hy + 95)], TEAL)
s.box(
    rx,
    hy - 30,
    390,
    200,
    "Urgency 70.8333",
    [
        "category: high",
        "~4 of 27 rules fired",
        "~μ: s and t medium 1/3,",
        "~high 2/3; v medium 1",
    ],
    kind="teal",
    size=24,
    tsize=28,
    lh=34,
    pad=20,
)

print(s.save("d2_fuzzy_pipeline"))
