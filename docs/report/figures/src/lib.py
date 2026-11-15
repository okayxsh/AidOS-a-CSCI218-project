"""Tiny SVG authoring helpers for the AidOS report diagrams (report tooling, not engine code)."""

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
OUT = REPO / "docs" / "report" / "figures" / "diagrams"
SCRATCH = Path(tempfile.gettempdir()) / "aidos-diagrams"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

NAVY = "#13283B"
TEAL = "#087F84"
INK = "#182B3D"
MUTED = "#5B6B7A"
RULE = "#D5DDE3"
SOFT = "#EEF4F6"
AMBER = "#B7791F"
WHITE = "#FFFFFF"

FONT = "Calibri, 'Segoe UI', Arial, sans-serif"
MONO = "Consolas, 'Courier New', monospace"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def rich(s: str) -> str:
    """`code` -> Consolas tspan, *bold* -> bold tspan."""
    out = []
    for part in re.split(r"(`[^`]*`|\*[^*]+\*)", s):
        if not part:
            continue
        if part.startswith("`"):
            out.append(f'<tspan font-family="{MONO}">{esc(part[1:-1])}</tspan>')
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            out.append(f'<tspan font-weight="700">{esc(part[1:-1])}</tspan>')
        else:
            out.append(esc(part))
    return "".join(out)


class SVG:
    def __init__(self, w: int, h: int):
        self.w, self.h = w, h
        self.parts: list[str] = []

    # -------------------------------------------------- primitives
    def add(self, s: str) -> None:
        self.parts.append(s)

    def rect(self, x, y, w, h, fill=WHITE, stroke=NAVY, sw=1.5, rx=6, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" ry="{rx}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>'
        )

    def text(
        self, x, y, s, size=16, fill=INK, weight=400, anchor="start", mono=False, italic=False
    ):
        fam = MONO if mono else FONT
        it = ' font-style="italic"' if italic else ""
        body = esc(s) if mono else rich(s)
        self.add(
            f'<text x="{x}" y="{y}" font-family="{fam}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{anchor}" style="white-space:pre"{it}>{body}</text>'
        )

    def lines(self, x, y, items, size=16, lh=None, **kw):
        lh = lh or round(size * 1.32)
        for i, s in enumerate(items):
            if s.startswith("~"):
                self.text(x, y + i * lh, s[1:], size=size, **{**kw, "fill": MUTED})
            else:
                self.text(x, y + i * lh, s, size=size, **kw)
        return y + len(items) * lh

    def line(self, x1, y1, x2, y2, stroke=RULE, sw=1.5, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" '
            f'stroke-width="{sw}"{d}/>'
        )

    def path(self, d, stroke=NAVY, sw=1.5, fill="none", dash=None, marker=None, start=None):
        da = f' stroke-dasharray="{dash}"' if dash else ""
        me = f' marker-end="url(#{marker})"' if marker else ""
        ms = f' marker-start="url(#{start})"' if start else ""
        self.add(
            f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" '
            f'stroke-linejoin="round"{da}{me}{ms}/>'
        )

    def arrow(self, pts, color=TEAL, sw=None, dash=None, both=False):
        """Orthogonal polyline arrow through points [(x,y),...]."""
        sw = sw or (2 if color == TEAL else 1.5)
        mk = {TEAL: "ah-teal", NAVY: "ah-navy", AMBER: "ah-amber", MUTED: "ah-muted"}[color]
        d = "M" + " L".join(f"{x},{y}" for x, y in pts)
        self.path(d, stroke=color, sw=sw, dash=dash, marker=mk, start=(mk + "-s") if both else None)

    def curve(self, d, color=TEAL, sw=None, dash=None):
        sw = sw or (2 if color == TEAL else 1.5)
        mk = {TEAL: "ah-teal", NAVY: "ah-navy", AMBER: "ah-amber", MUTED: "ah-muted"}[color]
        self.path(d, stroke=color, sw=sw, dash=dash, marker=mk)

    # -------------------------------------------------- composites
    def panel(self, x, y, w, h, label=None, sub=None, size=17):
        self.rect(x, y, w, h, fill=SOFT, stroke=RULE, sw=1.5)
        if label:
            self.text(x + 16, y + 28, label, size=size, fill=NAVY, weight=700)
        if sub:
            self.text(x + w - 16, y + 28, sub, size=15, fill=MUTED, anchor="end")

    def box(
        self,
        x,
        y,
        w,
        h,
        title=None,
        items=(),
        kind="primary",
        size=15,
        tsize=17,
        align="start",
        pad=14,
        lh=None,
        title_mono=False,
    ):
        stroke = {"primary": NAVY, "teal": TEAL, "amber": AMBER, "muted": RULE}[kind]
        sw = 2 if kind in ("teal",) else 1.5
        self.rect(x, y, w, h, fill=WHITE, stroke=stroke, sw=sw)
        tx = x + pad if align == "start" else x + w / 2
        cy = y + pad + tsize - 2
        tcol = {"amber": AMBER, "teal": TEAL}.get(kind, NAVY)
        if title:
            self.text(
                tx, cy, title, size=tsize, fill=tcol, weight=700, anchor=align, mono=title_mono
            )
            cy += round(tsize * 0.45) + size + 2
        else:
            cy = y + pad + size - 1
        lh = lh or round(size * 1.32)
        for s in items:
            col, sz = INK, size
            if s.startswith("~"):
                s, col, sz = s[1:], MUTED, max(21, size - 2)
            self.text(tx, cy, s, size=sz, fill=col, anchor=align)
            cy += lh
        return cy

    def label(self, x, y, s, size=15, fill=MUTED, anchor="middle", weight=400, bg=True, mono=False):
        """A small label, optionally on a white knock-out background."""
        if bg:
            cw = 0.56 if mono else 0.47
            w = len(re.sub(r"[`*]", "", s)) * size * cw + 10
            x0 = x - w / 2 if anchor == "middle" else (x - 5 if anchor == "start" else x - w + 5)
            self.add(
                f'<rect x="{x0:.1f}" y="{y - size + 1}" width="{w:.1f}" '
                f'height="{size + 6}" fill="{WHITE}" opacity="0.92"/>'
            )
        self.text(x, y + 1, s, size=size, fill=fill, anchor=anchor, weight=weight, mono=mono)

    # -------------------------------------------------- output
    def render(self) -> str:
        defs = []
        for name, col in (("teal", TEAL), ("navy", NAVY), ("amber", AMBER), ("muted", MUTED)):
            defs.append(
                f'<marker id="ah-{name}" viewBox="0 0 10 10" refX="9.5" refY="5" '
                f'markerWidth="14" markerHeight="14" markerUnits="userSpaceOnUse" '
                f'orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{col}"/></marker>'
            )
            defs.append(
                f'<marker id="ah-{name}-s" viewBox="0 0 10 10" refX="0.5" refY="5" '
                f'markerWidth="14" markerHeight="14" markerUnits="userSpaceOnUse" '
                f'orient="auto"><path d="M10,0 L0,5 L10,10 z" fill="{col}"/></marker>'
            )
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
            f'viewBox="0 0 {self.w} {self.h}" font-family="{FONT}">\n'
            f"<defs>{''.join(defs)}</defs>\n"
            f'<rect x="0" y="0" width="{self.w}" height="{self.h}" fill="{WHITE}"/>\n'
            + "\n".join(self.parts)
            + "\n</svg>\n"
        )

    def save(self, name: str) -> Path:
        OUT.mkdir(parents=True, exist_ok=True)
        svg_path = OUT / f"{name}.svg"
        svg = self.render()
        svg_path.write_text(svg, encoding="utf-8")
        SCRATCH.mkdir(parents=True, exist_ok=True)
        html = SCRATCH / f"{name}.html"
        html.write_text(
            "<!doctype html><html><head><meta charset='utf-8'><style>"
            "html,body{margin:0;padding:0;background:#fff;overflow:hidden}"
            "svg{display:block}</style></head><body>" + svg + "</body></html>",
            encoding="utf-8",
        )
        png = OUT / f"{name}.png"
        subprocess.run(
            [
                EDGE,
                "--headless=new",
                "--disable-gpu",
                "--hide-scrollbars",
                "--force-device-scale-factor=2",
                f"--window-size={self.w},{self.h}",
                f"--screenshot={png}",
                html.as_uri(),
            ],
            check=False,
            capture_output=True,
            timeout=120,
        )
        return png
