"""Crop the report screenshots from full-page dashboard captures.

Captures: Microsoft Edge (headless), device scale factor 2, live engine and dev server.
- Landing page at 1440 x 900.
- Dashboard pages at 1040 px wide, so the sidebar stays docked and each panel is about
  714 CSS px wide, which keeps the text legible at about 13.5 cm in print.
- Each capture follows the scripted steps in the comments below.

Boxes are CSS pixels (left, top, right, bottom); the captures are 2x, so they are doubled.

Usage: python crop_report_shots.py <capture_dir> <out_dir>
"""

import sys
from pathlib import Path

from PIL import Image

SCALE = 2
CROPS = {
    # "/" first viewport.
    "sc1_landing": ("r_landing", None),
    # /dashboard/allocate?scenario=triage-demo-001 -> Run allocation (AidOS tab):
    # summary tiles and the allocation matrix.
    "sc2_allocation": ("r_alloc_1040", (288, 380, 1016, 1092)),
    # Same page: the explanation panel for the default cell (Zone B, medical kits).
    "sc3_explanation": ("r_alloc_1040", (288, 1095, 1016, 1712)),
    # Same page: the baseline comparison table.
    "sc4_comparison": ("r_alloc_1040", (288, 3884, 1016, 4556)),
    # /dashboard/simulate -> Load into simulator -> Start -> Zone B severity 6 -> 9:
    # the before/after panel (urgency, rank and AidOS vs FCFS on the same state).
    "sc5_simulation": ("r_sim_1040", (288, 2035, 1016, 2606)),
    # /dashboard/evaluate (default run extended-20261112T100136Z): summary tiles and the
    # start of the policy comparison table.
    "sc6_evaluation": ("r_eval_1040", (288, 458, 1016, 1000)),
}


def main(capture_dir: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, (source, box) in CROPS.items():
        image = Image.open(capture_dir / f"{source}.png")
        if box is not None:
            image = image.crop(tuple(v * SCALE for v in box))
        image.save(out_dir / f"{name}.png", optimize=True)
        print(name, image.size)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
