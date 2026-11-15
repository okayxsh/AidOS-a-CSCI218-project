from lib import MUTED, NAVY, SVG, TEAL, WHITE

W = 1600
s = SVG(W, 1800)
SZ, TS, LH = 24, 28, 34

L0, L1 = 20, 470
C0, C1 = 500, 1100
R0, R1 = 1130, 1580


def box(x, y, w, h, t, items=(), kind="primary", **kw):
    kw.setdefault("size", SZ)
    kw.setdefault("tsize", TS)
    kw.setdefault("lh", LH)
    kw.setdefault("pad", 16)
    s.box(x, y, w, h, t, items, kind=kind, **kw)


def cbox(x, y, w, h, label, kind="primary", sub=None):
    """Centred single-label box."""
    col = {"teal": TEAL}.get(kind, NAVY)
    s.rect(x, y, w, h, fill=WHITE, stroke=col, sw=2 if kind == "teal" else 1.5)
    ty = y + h / 2 + 9 if not sub else y + h / 2 - 4
    s.text(x + w / 2, ty, label, size=26, fill=col, weight=700, anchor="middle")
    if sub:
        s.text(x + w / 2, ty + 32, sub, size=22, fill=MUTED, anchor="middle")


# ================================================================== A: frontend
AY = 20
s.panel(20, AY, W - 40, 248, "Frontend  ·  React, TypeScript, Vite", size=28)
py, ph = AY + 58, 64
cbox(36, py, 200, 166, "Landing", sub="no API calls")
cbox(252, py, 202, ph, "Simulate")
pw = (C1 - C0 - 3 * 12) / 4
for i, p in enumerate(["Overview", "Scenarios", "Inventory", "Allocate"]):
    cbox(C0 + i * (pw + 12), py, pw, ph, p, kind="teal" if p == "Allocate" else "primary")
cbox(R0 + 16, py, R1 - R0 - 32, ph, "Evaluate")
sy, sh = py + ph + 40, 62
s.rect(252, sy, R1 - 16 - 252, sh, fill=WHITE, stroke=NAVY)
s.text(272, sy + 40, "`api/client.ts`: typed fetch, JSON over HTTP", size=24)
xs_pages = [353] + [C0 + i * (pw + 12) + pw / 2 for i in range(4)] + [(R0 + R1) / 2]
for x in xs_pages:
    s.line(x, py + ph, x, sy, stroke=NAVY, sw=1.5)

# ================================================================== B: API
BY = AY + 248 + 46
BH = 244
s.panel(20, BY, W - 40, BH, "HTTP JSON API", size=28)
s.text(1022, BY + 30, "FastAPI; all paths under /api", size=22, fill=MUTED)
ry, rh = BY + 56, 172
box(36, ry, 418, rh, "simulation", ["`/simulation`", "sessions, events,", "replay, import"])
cw = (C1 - C0 - 2 * 12) / 3
routes = [
    ("scenarios", "`/scenarios`"),
    ("urgency", "`/urgency`"),
    ("allocations", "`/allocations`"),
]
for i, (t, p) in enumerate(routes):
    box(C0 + i * (cw + 12), ry, cw, rh, t, [p], kind="teal" if i == 2 else "primary")
box(R0 + 16, ry, R1 - R0 - 32, rh, "evaluation", ["`/evaluation`", "read-only runs"])
xr = [353, C0 + cw / 2, C0 + 1.5 * cw + 12, C0 + 2.5 * cw + 24, (R0 + R1) / 2]
for i, x in enumerate(xr):
    s.arrow([(x, sy + sh), (x, ry)], TEAL if i == 3 else NAVY, both=True)

# ================================================================== C: orchestration
CY = BY + BH + 46
CH = 360
s.panel(L0, CY, L1 - L0, CH, "`simulation/`", size=28)
box(36, CY + 56, 418, 112, "store", ["in-memory sessions"], pad=14)
box(36, CY + 186, 418, 112, "session", ["apply, replay, export"], pad=14)
s.text(36, CY + 334, "`fsm` · `events` · `reducer`", size=24)
s.arrow([(245, CY + 168), (245, CY + 186)], NAVY)
s.arrow([(245, ry + rh), (245, CY + 56)], NAVY)

PX0, PW = 540, 520
box(
    PX0,
    CY + 30,
    PW,
    290,
    "`pipeline.compare`",
    [
        "1  validate scenario",
        "2  fuzzy urgency (once)",
        "3  run 4 policies",
        "4  independent validator",
        "5  metrics",
    ],
    kind="teal",
    lh=36,
)
s.arrow([(L1 - 16, CY + 240), (PX0, CY + 240)], NAVY)
s.arrow([(C0 + 2.5 * cw + 24, ry + rh), (C0 + 2.5 * cw + 24, CY + 30)], TEAL, both=True)
s.arrow([(C0 + 1.5 * cw + 12, ry + rh), (C0 + 1.5 * cw + 12, CY + 30)], NAVY)

s.panel(R0, CY, R1 - R0, CH, "`evaluation/`", size=28)
box(R0 + 16, CY + 56, 418, 112, "artifacts", ["reads finished runs"], pad=14)
box(R0 + 16, CY + 186, 418, 112, "campaign", ["offline benchmark runs"], pad=14)
s.text(R0 + 16, CY + 334, "`families` · `dynamic` · `stats`", size=24)
s.arrow([((R0 + R1) / 2, ry + rh), ((R0 + R1) / 2, CY + 56)], NAVY)
s.arrow([(R0 + 16, CY + 240), (PX0 + PW, CY + 240)], NAVY)

# ================================================================== D: engine core
DY = CY + CH + 46
DH = 224
DX1 = 1540
s.panel(20, DY, DX1 - 20, DH, "Engine core  ·  pure Python, no FastAPI", size=28)
ey, eh = DY + 56, 150
cols = [(36, 500), (552, 220), (788, 330), (1134, 196), (1346, 178)]
eng = [
    ("`domain/`", ["models, validation,", "snapshot hash"], "primary"),
    ("fuzzy", ["Sugeno,", "27 rules"], "teal"),
    ("policies", ["FCFS, greedy,", "2 × CP-SAT"], "teal"),
    ("validator", ["`invariants`"], "teal"),
    ("metrics", ["coverage,", "fairness"], "teal"),
]
for (x, w), (t, items, kind) in zip(cols, eng, strict=False):
    box(x, ey, w, eh, t, items, kind=kind, pad=16)
for i in range(4):
    (x, w), (nx, _) = cols[i], cols[i + 1]
    s.arrow([(x + w, ey + eh / 2), (nx, ey + eh / 2)], TEAL)
s.arrow([(PX0 + PW / 2, CY + 320), (PX0 + PW / 2, ey)], TEAL)
s.arrow([(C0 + 20, ry + rh), (C0 + 20, ey)], NAVY)

# ================================================================== E: files on disk
EY = DY + DH + 46
EH = 184
s.panel(20, EY, W - 40, EH, "Files on disk", size=28)
box(36, EY + 56, 500, 112, "`data/scenarios/`", ["9 synthetic fixtures"], pad=16)
box(552, EY + 56, 220, 112, "`fuzzy_rules`", ["`.json` v1.0"], pad=16, tsize=24, title_mono=False)
box(
    788,
    EY + 56,
    752,
    112,
    "`experiments/results/`",
    ["CSV, summary, manifest with SHA-256"],
    pad=16,
)
s.arrow([(420, EY + 56), (420, ey + eh)], NAVY)
s.arrow([(662, EY + 56), (662, ey + eh)], NAVY)
s.arrow([(1540, EY + 112), (1562, EY + 112), (1562, CY + CH)], NAVY, both=True)

s.h = EY + EH + 20
print("H", s.h)
print(s.save("d1_architecture"))
