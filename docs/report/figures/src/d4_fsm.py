from lib import AMBER, INK, MUTED, NAVY, SVG, TEAL, WHITE

W, H = 1600, 1010
s = SVG(W, H)

BW, BH = 270, 116
R = (190, 250)
A = (700, 250)
P = (1300, 250)
C = (700, 600)
E = (1300, 600)
meaning = {
    "READY": "step 0 scored",
    "ACTIVE": "accepts events",
    "PAUSED": "events refused",
    "COMPLETED": "read-only",
    "ERROR": "read-only",
}
pos = {"READY": R, "ACTIVE": A, "PAUSED": P, "COMPLETED": C, "ERROR": E}

# transitions first (states drawn on top)
# create
s.add(f'<circle cx="46" cy="{R[1] + 58}" r="13" fill="{NAVY}"/>')
s.arrow([(59, R[1] + 58), (R[0], R[1] + 58)], NAVY)
s.text(124, R[1] + 44, "create", size=24, fill=INK, anchor="middle", mono=True)
s.text(124, R[1] + 88, "version 1", size=21, fill=MUTED, anchor="middle")

# start / reset (READY <-> ACTIVE)
mid = (R[0] + BW + A[0]) / 2
s.arrow([(R[0] + BW, R[1] + 36), (A[0], A[1] + 36)], TEAL)
s.text(mid, R[1] + 24, "start", size=26, fill=TEAL, weight=700, anchor="middle", mono=True)
s.arrow([(A[0], A[1] + 82), (R[0] + BW, R[1] + 82)], NAVY)
s.text(mid, R[1] + 114, "reset", size=26, fill=NAVY, anchor="middle", mono=True)

# pause / resume (ACTIVE <-> PAUSED)
mid2 = (A[0] + BW + P[0]) / 2
s.arrow([(A[0] + BW, A[1] + 36), (P[0], P[1] + 36)], NAVY)
s.text(mid2, A[1] + 24, "pause", size=26, fill=NAVY, anchor="middle", mono=True)
s.arrow([(P[0], P[1] + 82), (A[0] + BW, A[1] + 82)], NAVY)
s.text(mid2, A[1] + 114, "resume", size=26, fill=NAVY, anchor="middle", mono=True)

# apply_event self loop on ACTIVE
ax = A[0]
s.curve(f"M{ax + 80},{A[1]} C{ax + 80},{A[1] - 92} {ax + 190},{A[1] - 92} {ax + 190},{A[1]}", TEAL)
s.text(
    ax + 135, A[1] - 100, "apply_event", size=26, fill=TEAL, weight=700, anchor="middle", mono=True
)

# complete
s.arrow([(A[0] + BW / 2, A[1] + BH), (C[0] + BW / 2, C[1])], TEAL)
s.text(A[0] + BW / 2 + 16, 480, "complete", size=26, fill=TEAL, weight=700, mono=True)

# fail (diagonal)
s.arrow([(A[0] + BW - 10, A[1] + BH), (E[0] + 30, E[1])], AMBER)
s.text(1190, 418, "fail", size=26, fill=AMBER, weight=700, mono=True)
s.text(1190, 446, "internal: a plan failed", size=21, fill=MUTED)
s.text(1190, 471, "the validator", size=21, fill=MUTED)

# reset PAUSED -> READY over the top
s.arrow([(P[0] + BW / 2, P[1]), (P[0] + BW / 2, 60), (R[0] + 200, 60), (R[0] + 200, R[1])], NAVY)
s.label(1000, 66, "reset", size=26, fill=NAVY, mono=True)

# READY self loop
s.curve(
    f"M{R[0] + 40},{R[1]} C{R[0] + 40},{R[1] - 84} {R[0] + 140},{R[1] - 84} {R[0] + 140},{R[1]}",
    NAVY,
)
s.text(R[0] + 90, R[1] - 92, "reset", size=26, fill=NAVY, anchor="middle", mono=True)

# reset COMPLETED -> READY
s.arrow([(C[0], C[1] + 58), (R[0] + 200, C[1] + 58), (R[0] + 200, R[1] + BH)], NAVY)
s.label(500, C[1] + 66, "reset", size=26, fill=NAVY, mono=True)

# reset ERROR -> READY along the bottom
s.arrow(
    [(E[0] + BW / 2, E[1] + BH), (E[0] + BW / 2, 790), (R[0] + 70, 790), (R[0] + 70, R[1] + BH)],
    NAVY,
)
s.label(1000, 798, "reset", size=26, fill=NAVY, mono=True)

for name, (x, y) in pos.items():
    col = AMBER if name == "ERROR" else NAVY
    s.rect(x, y, BW, BH, fill=WHITE, stroke=col, sw=2.5)
    s.text(x + BW / 2, y + 48, name, size=28, fill=col, weight=700, anchor="middle", mono=True)
    s.text(x + BW / 2, y + 88, meaning[name], size=22, fill=MUTED, anchor="middle")

# notes
s.panel(20, 838, W - 40, 156)
s.lines(
    48,
    884,
    [
        "Each accepted action stores `version + 1`.",
        "Any pair not drawn: 409 `invalid_transition`.",
        "Reads are allowed in every state.",
    ],
    size=24,
    lh=40,
)
s.lines(
    830,
    884,
    [
        "Actions: POST `…/sessions/{id}/{action}`",
        "`reset` restores step 0 and clears history.",
        "At most 200 events per session.",
    ],
    size=24,
    lh=40,
)

print(s.save("d4_fsm"))
