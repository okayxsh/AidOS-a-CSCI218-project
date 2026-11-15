"""Membership functions and output constants, drawn from the production fuzzy_rules.json."""

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

root = Path(sys.argv[1])
out = Path(sys.argv[2])
cfg = json.loads((root / "apps/api/aidos/config/fuzzy_rules.json").read_text(encoding="utf-8"))
terms = cfg["inputs"]["severity"]["terms"]
same = all(cfg["inputs"][k]["terms"] == terms for k in cfg["inputs"])
assert same, "inputs differ; the chart assumes shared sets"

plt.rcParams.update(
    {
        "font.family": "Calibri",
        "font.size": 10.5,
        "axes.edgecolor": "#5B6B7A",
        "axes.labelcolor": "#1E2933",
        "xtick.color": "#1E2933",
        "ytick.color": "#1E2933",
    }
)
fig, (ax, ax2) = plt.subplots(1, 2, figsize=(9.2, 2.9), gridspec_kw={"width_ratios": [1.35, 1]})
colors = {"low": "#087F84", "medium": "#13283B", "high": "#B7791F"}
styles = {"low": "-", "medium": "--", "high": "-"}
for name, t in terms.items():
    p = t["points"]
    xs = [p[0], p[1], p[2], p[3]] if t["shape"] == "trapezoid" else [p[0], p[1], p[2]]
    ys = (
        [0 if p[0] != p[1] else 1, 1, 1, 0 if p[2] != p[3] else 1]
        if t["shape"] == "trapezoid"
        else [0, 1, 0]
    )
    ax.plot(xs, ys, styles[name], color=colors[name], lw=2, label=name)
ax.set_xlim(0, 10)
ax.set_ylim(-0.03, 1.08)
ax.set_xlabel("Rating (severity, time criticality or vulnerability), 0–10")
ax.set_ylabel("Membership degree")
ax.set_xticks(range(0, 11))
for x in (2, 5, 8):
    ax.axvline(x, color="#C9D3DA", lw=0.8, zorder=0)
ax.legend(frameon=False, fontsize=9, loc="upper left", bbox_to_anchor=(0.0, 0.88))
ax.set_title("Input sets (identical for all three inputs)", fontsize=10.5, color="#13283B")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)

outs = cfg["output"]["terms"]
for i, (name, t) in enumerate(outs.items()):
    lo, hi = t["band"]
    ax2.axvspan(lo, hi, color=["#EEF4F6", "#E3E9ED", "#EEF4F6", "#E3E9ED"][i], zorder=0)
    ax2.vlines(t["value"], 0, 1, color="#087F84", lw=2.4)
    ax2.text(
        t["value"],
        1.05,
        f"{name}\n{t['value']}",
        ha="center",
        va="bottom",
        fontsize=9,
        color="#13283B",
    )
ax2.set_xlim(0, 100)
ax2.set_ylim(0, 1.45)
ax2.set_yticks([])
ax2.set_xticks([0, 25, 50, 75, 100])
ax2.set_xlabel("Urgency score, 0–100 (category bands shaded)")
ax2.set_title("Output constants (zero-order Sugeno)", fontsize=10.5, color="#13283B", pad=4)
for s in ("top", "right", "left"):
    ax2.spines[s].set_visible(False)
fig.tight_layout()
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=220)
fig.savefig(out.with_suffix(".svg"))
print("wrote", out)
