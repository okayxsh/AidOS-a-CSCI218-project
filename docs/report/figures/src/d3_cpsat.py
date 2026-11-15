from lib import AMBER, NAVY, SVG, TEAL

W, H = 1600, 1848
s = SVG(W, H)
SZ, TS, LH, PAD = 24, 28, 34, 18

MX, MW = 20, 1040
MC = MX + MW / 2
GX, GW = 1100, 480


def box(x, y, w, h, t, items, kind="primary", **kw):
    kw.setdefault("size", SZ)
    kw.setdefault("tsize", TS)
    kw.setdefault("lh", LH)
    kw.setdefault("pad", PAD)
    s.box(x, y, w, h, t, items, kind=kind, **kw)


# ------------------------------------------------------------------ inputs
iy, ih = 20, 172
box(
    20,
    iy,
    500,
    ih,
    "AidosConfig",
    ["ε = 1, every w_r = 1", "floor target τ = 0.25", "5 s, seed 0, 1 worker"],
)
box(
    550, iy, 500, ih, "Snapshot", ["zones, stock S[r],", "requests d[z,r]", "~one immutable object"]
)
box(1080, iy, 500, ih, "Urgency scores u(z)", ["fuzzy, 4 decimals,", "shared by all policies"])
BUS = iy + ih + 22
s.arrow([(270, iy + ih), (270, BUS + 26)], NAVY)
s.arrow([(800, iy + ih), (800, BUS + 26)], TEAL)
s.arrow([(1330, iy + ih), (1330, BUS + 26)], TEAL)
s.line(800, BUS, 1330, BUS, stroke=TEAL, sw=2)

y = BUS + 26
box(
    MX,
    y,
    MW,
    140,
    "1  Integer coefficients",
    [
        "c[z,r] = w_r · (round(10⁴·u) + round(10⁴·ε))",
        "~exact integers; e.g. u = 70.8333 gives 718,333",
    ],
    kind="teal",
)
gy = y
y += 140
s.arrow([(MC, y), (MC, y + 36)], TEAL)
y += 36
box(
    MX,
    y,
    MW,
    140,
    "2  Integer model",
    [
        "x[z,r] ∈ {0, …, d[z,r]};   Σ_z x[z,r] ≤ S[r]",
        "~one constraint per resource: no substitution",
    ],
)
y += 140
s.arrow([(MC, y), (MC, y + 36)], TEAL)
y += 36

# phases
py0, ph = y, 470
s.panel(MX, py0, MW, ph, "3  Lexicographic phases", size=28)
SW, SG = 252, 32
slots = [MX + 210 + i * (SW + SG) for i in range(3)]
PH = 132
lanes = [
    ("aidos", py0 + 60, [None, "urgency", "tie_break"]),
    ("aidos_", py0 + 220, ["coverage_floor", "urgency", "tie_break"]),
]
ptext = {
    "coverage_floor": ["max Σ f_r", "~floor per resource"],
    "urgency": ["max Σ c · x"],
    "tie_break": ["max Σ ρ · x", "~earlier arrival"],
}
for name, ly, seq in lanes:
    if name == "aidos":
        s.text(MX + 20, ly + 74, "aidos", size=26, fill=NAVY, weight=700, mono=True)
    else:
        s.text(MX + 16, ly + 74, "aidos_balanced", size=23, fill=NAVY, weight=700, mono=True)
    prev = None
    for i, ph_name in enumerate(seq):
        if ph_name is None:
            continue
        x = slots[i]
        box(
            x,
            ly,
            SW,
            PH,
            ph_name,
            ptext[ph_name],
            kind="teal" if ph_name == "urgency" else "primary",
            tsize=24,
            title_mono=True,
            pad=16,
        )
        if prev is not None:
            s.arrow([(prev + SW, ly + PH / 2), (x, ly + PH / 2)], TEAL)
        prev = x
s.lines(
    MX + 20,
    py0 + 404,
    [
        "Each phase keeps the previous optimum fixed.",
        "~If stock is short, the floor shrinks (to 0 if needed); never infeasible.",
    ],
    size=24,
    lh=36,
)
y = py0 + ph
s.arrow([(MC, y), (MC, y + 36)], TEAL)
y += 36
box(
    MX,
    y,
    MW,
    140,
    "4  CP-SAT solve, per phase",
    [
        "1 worker, seed 0, one 5 s budget for all phases",
        "~each phase's status is recorded",
    ],
)
y += 140
s.line(MC, y, MC, y + 26, stroke=TEAL, sw=2)
fy = y + 52
s.line(MX + 170, y + 26, MX + MW - 170, y + 26, stroke=TEAL, sw=2)
ow, og = 330, 25
ox = [MX + i * (ow + og) for i in range(3)]
for i, x in enumerate(ox):
    s.arrow([(x + ow / 2, y + 26), (x + ow / 2, fy)], AMBER if i == 2 else TEAL)
fh = 172
box(ox[0], fy, ow, fh, "OPTIMAL", ["every phase", "proven optimal"], kind="teal", title_mono=True)
box(ox[1], fy, ow, fh, "FEASIBLE", ["valid plan;", "optimality not", "proven"], title_mono=True)
box(
    ox[2],
    fy,
    ow,
    fh,
    "No plan",
    ["`INFEASIBLE`, `UNKNOWN`", "or `MODEL_INVALID`:", "no cells shown"],
    kind="amber",
    size=22,
)
VY = fy + fh + 50
for x in ox[:2]:
    s.arrow([(x + ow / 2, fy + fh), (x + ow / 2, VY)], TEAL)

# ------------------------------------------------------------------ greedy column
box(
    GX,
    gy,
    GW,
    268,
    "Urgency greedy",
    [
        "sort zones by urgency,",
        "then arrival, then id;",
        "each gets min(stock left,",
        "its request)",
        "~status COMPLETE, no solver",
    ],
)
ny = gy + 268 + 60
box(
    GX,
    ny,
    GW - 40,
    400,
    "Same plan as aidos",
    [
        "Proven: each resource is",
        "a separate knapsack; c ranks",
        "zones exactly as u does;",
        "tie-breaks match.",
        "Checked on 36,240 exhaustive",
        "and 700 random instances",
        "and all 504 Stage 4 scenarios.",
        "~aidos_balanced can differ.",
    ],
    kind="teal",
)
s.arrow([(slots[2] + SW, py0 + 60 + PH / 2), (GX, py0 + 60 + PH / 2)], NAVY, dash="6 5", both=True)
# greedy plan down the right gutter
s.arrow([(1562, gy + 268), (1562, VY)], TEAL)

# ------------------------------------------------------------------ validator and output
box(
    MX,
    VY,
    W - 40,
    140,
    "5  Independent validator  ·  `invariants.py`",
    [
        "integer, non-negative, ≤ request, ≤ stock, complete",
        "~checked against the scenario, never the policy's claims",
    ],
)
s.arrow([(W / 2, VY + 140), (W / 2, VY + 176)], TEAL)
OY = VY + 176
box(
    MX,
    OY,
    W - 40,
    140,
    "6  Plan, metrics, explanation",
    [
        "units, limit and reason per cell; solver status and phases",
        "~returned by POST /api/allocations/compare",
    ],
    kind="teal",
)
print("height", OY + 160)
print(s.save("d3_cpsat_workflow"))
