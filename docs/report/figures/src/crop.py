import sys
from pathlib import Path

from PIL import Image

d = Path(sys.argv[1])
crops = {
    "s02_overview": (264, 0, 1440, 1160),
    "s03_urgency": (264, 0, 1440, None),
    "s04_allocation": (264, 0, 1440, 1250),
    "s05_comparison": (264, 0, 1440, None),
    "s06_simulation": (264, 0, 1440, 1590),
    "s07_sim_before_after": (264, 0, 1440, 1100),
    "s08_evaluation": (264, 0, 1440, 1310),
    "s09_inventory": (264, 0, 1440, None),
}
for name, (x0, y0, x1, y1) in crops.items():
    im = Image.open(d / f"{name}.png")
    box = (x0, y0, min(x1, im.width), im.height if y1 is None else min(y1, im.height))
    im.crop(box).save(d / f"{name}_report.png", optimize=True)
    print(name, im.size, "->", box)
