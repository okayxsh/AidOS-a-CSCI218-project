---
name: AidOS
description: An explainable relief-allocation simulator. The landing page is a night sky over a ridge, and the dashboard is a near-black mission-control room in the same world.
colors:
  ink-950: "#04070d"
  ink-900: "#070d18"
  ink-850: "#091120"
  ink-800: "#0c1626"
  ink-750: "#101c2f"
  ink-700: "#15243a"
  ink-600: "#1d304b"
  sky-top: "#071324"
  sky-mid: "#0d2543"
  sky-horizon: "#173f66"
  stage-horizon: "#143a5f"
  line: "rgba(170, 205, 245, 0.1)"
  line-strong: "rgba(170, 205, 245, 0.18)"
  line-focus: "#7fe3dc"
  text: "#e8eef7"
  text-2: "#b4c2d4"
  text-3: "#8b9cb4"
  text-inverse: "#07101c"
  frost-white: "#f4f7fb"
  teal: "#3fd0c9"
  teal-strong: "#23b2ab"
  teal-text: "#8ff0e9"
  teal-soft: "rgba(63, 208, 201, 0.14)"
  accent-mist: "#d4f1ee"
  amber: "#f5b042"
  amber-text: "#f8c46f"
  amber-soft: "rgba(245, 176, 66, 0.13)"
  red: "#f0626a"
  red-text: "#ff8a90"
  red-soft: "rgba(240, 98, 106, 0.14)"
  blue: "#6fb6ff"
  violet: "#b49cff"
  green: "#9bd77a"
  slate: "#50678a"
  dash-ground: "#080b10"
  dash-sidebar: "#0b1017"
  dash-panel: "#111821"
  dash-hover: "#141c26"
  dash-raised: "#17212c"
  dash-checked: "#212c39"
  dash-line: "#1d2631"
  dash-line-strong: "#2a3542"
  dash-focus: "#7fdcd5"
  dash-text: "#eaf0f4"
  dash-text-2: "#a2b0c0"
  dash-text-3: "#7d8a9b"
  dash-teal: "#43c9c1"
  dash-teal-strong: "#2fb0a8"
  dash-teal-soft: "rgba(67, 201, 193, 0.12)"
  dash-amber: "#e9a84a"
  dash-amber-text: "#edb866"
  dash-amber-soft: "rgba(233, 168, 74, 0.12)"
  dash-red: "#e66b70"
  dash-red-text: "#f08e92"
  dash-red-soft: "rgba(230, 107, 112, 0.13)"
  dash-slate: "#556578"
  segment-slate-1: "#3d4e66"
  segment-slate-2: "#34445b"
  segment-slate-3: "#2c3a4f"
  segment-slate-4: "#46586f"
  segment-slate-5: "#394a61"
  segment-slate-6: "#303f55"
  scene-fog: "#0c2138"
  scene-medical: "#4f86c4"
  scene-water: "#2b9c96"
  scene-shelter: "#8774c2"
  scene-route: "#7088a8"
  scene-grid: "#a9c8ee"
  scene-input-2: "#86ade0"
  scene-input-3: "#6690cc"
  scene-zone-disc: "#16304f"
typography:
  display:
    fontFamily: "'Mona Sans Variable', 'Segoe UI', system-ui, sans-serif"
    fontSize: "clamp(2.5rem, 1.1rem + 4.4vw, 4.6rem)"
    fontWeight: 600
    lineHeight: 1.03
    letterSpacing: "-0.035em"
  display-accent:
    fontFamily: "'Instrument Serif', Georgia, serif"
    fontSize: "1.17em"
    fontWeight: 400
    lineHeight: 1
    letterSpacing: "-0.012em"
  headline:
    fontFamily: "'Mona Sans Variable', 'Segoe UI', system-ui, sans-serif"
    fontSize: "clamp(2rem, 1.2rem + 2.6vw, 3rem)"
    fontWeight: 600
    lineHeight: 1.08
    letterSpacing: "-0.03em"
  title:
    fontFamily: "'Mona Sans Variable', 'Segoe UI', system-ui, sans-serif"
    fontSize: "1.75rem"
    fontWeight: 600
    lineHeight: 1.12
    letterSpacing: "-0.025em"
  story-title:
    fontFamily: "'Mona Sans Variable', 'Segoe UI', system-ui, sans-serif"
    fontSize: "clamp(1.375rem, 1.1rem + 0.8vw, 1.75rem)"
    fontWeight: 600
    lineHeight: 1.12
    letterSpacing: "-0.025em"
  metric-value:
    fontFamily: "'Mona Sans Variable', 'Segoe UI', system-ui, sans-serif"
    fontSize: "1.875rem"
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: "-0.02em"
  title-sm:
    fontFamily: "'Mona Sans Variable', 'Segoe UI', system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 600
    lineHeight: 1.12
    letterSpacing: "-0.01em"
  body:
    fontFamily: "'Mona Sans Variable', 'Segoe UI', system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.55
  body-sm:
    fontFamily: "'Mona Sans Variable', 'Segoe UI', system-ui, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.55
  label:
    fontFamily: "'Mona Sans Variable', 'Segoe UI', system-ui, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 500
    lineHeight: 1
  mono:
    fontFamily: "'JetBrains Mono Variable', ui-monospace, 'Cascadia Mono', monospace"
    fontSize: "0.92em"
    fontWeight: 400
rounded:
  bar: "5px"
  sm: "8px"
  md: "12px"
  panel: "14px"
  lg: "18px"
  xl: "28px"
  pill: "999px"
spacing:
  sp-1: "4px"
  sp-2: "8px"
  sp-3: "12px"
  sp-4: "16px"
  sp-5: "20px"
  sp-6: "24px"
  sp-8: "32px"
  sp-10: "40px"
  sp-12: "48px"
  sp-16: "64px"
  sp-20: "80px"
  sp-28: "112px"
  frame-inset: "20px"
  container: "1200px"
  gutter: "clamp(16px, 4vw, 40px)"
components:
  button-primary:
    backgroundColor: "{colors.frost-white}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.pill}"
    padding: "0 6px 0 20px"
    height: "44px"
  button-primary-hover:
    backgroundColor: "#ffffff"
  button-secondary:
    backgroundColor: "rgba(7, 13, 24, 0.72)"
    textColor: "{colors.text}"
    rounded: "{rounded.pill}"
    padding: "0 20px"
    height: "44px"
  button-secondary-hover:
    backgroundColor: "{colors.ink-750}"
  button-quiet:
    backgroundColor: "transparent"
    textColor: "{colors.text}"
    rounded: "{rounded.pill}"
    padding: "0 16px"
    height: "40px"
  button-accent:
    backgroundColor: "{colors.dash-teal}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.pill}"
    padding: "0 20px"
    height: "44px"
  badge:
    textColor: "{colors.text-2}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "0 10px"
    height: "24px"
  badge-built:
    backgroundColor: "{colors.teal-soft}"
    textColor: "{colors.teal-text}"
  badge-warn:
    backgroundColor: "{colors.amber-soft}"
    textColor: "{colors.amber-text}"
  badge-critical:
    backgroundColor: "{colors.red-soft}"
    textColor: "{colors.red-text}"
  panel:
    backgroundColor: "{colors.dash-panel}"
    rounded: "{rounded.panel}"
    padding: "20px 22px"
  metric:
    backgroundColor: "{colors.dash-panel}"
    textColor: "{colors.dash-text}"
    typography: "{typography.metric-value}"
    rounded: "{rounded.panel}"
    padding: "16px 18px"
  nav-link-active:
    backgroundColor: "{colors.dash-raised}"
    textColor: "{colors.dash-text}"
    height: "42px"
  story-panel:
    backgroundColor: "rgba(7, 13, 24, 0.92)"
    textColor: "{colors.text-2}"
    rounded: "{rounded.lg}"
    padding: "26px 28px 28px"
    width: "min(430px, 36vw)"
  story-label:
    backgroundColor: "rgba(6, 12, 23, 0.84)"
    textColor: "{colors.text-2}"
    rounded: "{rounded.pill}"
    padding: "5px 10px"
  request-bar:
    textColor: "{colors.text}"
    rounded: "{rounded.bar}"
    height: "34px"
---

# Design System: AidOS

## Overview

**Creative North Star: "The Night Watch Over the Ridge"**

AidOS lives in one dark world with two rooms. The landing page (Persuade) is the Aurora Ridge: a fictional relief landscape at night, under a navy sky that brightens toward the horizon, with faint aurora bands and a ridge holding a depot, tents, a water tower and sparse zone lights. Below the hero, the same night sky becomes a framed stage where a single resource network (one depot, three zones, supply routes) is built chapter by chapter as the visitor scrolls. The dashboard (Operate) is the mission-control room inside that world. It uses a near-black palette (`.dash-palette`) where hierarchy comes from surface steps rather than brighter borders. The landing page's picture of the dashboard uses that same palette, so the preview and the real product match.

The mood is calm emergency-operations tooling. It is quiet and exact, and it never dramatises a catastrophe. Colour carries meaning, never decoration: teal is stock, amber is shortfall, red is critical. Honesty is part of the visual system. Planned work gets a dashed outline and a "Planned · Stage N" label. Uncommitted results say "Candidate plan · not committed". Every story chapter that is not plain scenario data carries a status badge: Synthetic data, Concept, Partly built or Illustration.

Motion is native and measured. The scroll story and hero parallax are driven by native scroll with no scroll-jacking, and the dashboard settles in once and then stays still. Under reduced motion all of it falls back to a static state that is still complete. Rejected in the build: the split hero (copy beside a screenshot), the feature-card wall, spinners for data loading, counting-number animations, and gamified disaster imagery.

**Key Characteristics:**
- One dark world with two palettes: navy for the landing atmosphere, near-black for the dashboard. There is no light mode (`color-scheme: dark`).
- Semantic signal colours, always paired with a text label.
- A white and a near-black pill as the two button voices.
- Flat in-flow panels. Shadows are reserved for layers that float above the page or the stage.
- Dashed outlines mean "planned" or "not yet real".
- One persistent 3D scene, conducted by native scroll and backed by an SVG poster.
- Short, single-play dashboard motion with no spinners on data loads, and none of it under reduced motion.

## Colors

The landing page uses a cold, low-chroma navy ground. The dashboard is a near-black instrument panel. Both use the same three signal hues, and they appear only when they mean something.

### Primary
- **Depot Teal** (teal on the landing page, dash-teal on the dashboard): stock and availability. It marks the stock marker on request bars, constraint caps in the 3D scene, the active nav icon, the engine-online dot and the accent action button. Its soft forms are **Teal Soft** (teal-soft / dash-teal-soft), used as a badge fill and for the value-changed flash, and **Mint Readout** (teal-text) for text on that fill and for OK metrics.
- **Deep Teal** (teal-strong / dash-teal-strong): the pressed or darker shade of the teal signal.

### Secondary
- **Shortfall Amber** (amber / dash-amber): shortfall and caution. It marks shortfall metrics, "N short" gaps, the request bar's over-stock outline, the ghost outlines of unmet demand and the stale dashed routes in the 3D scene, and the "Synthetic data" badge. Use **Amber Readout** (amber-text / dash-amber-text) for amber text on a dark ground.

### Tertiary
- **Critical Red** (red / red-text / red-soft, and their dash- versions): critical states only, such as "Depot empty" and the engine-offline dot. Critical metric tiles get a 6% red wash and a 30% red border mix.
- **Resource identities**: Medical Blue (blue), Shelter Violet (violet) and Nutrition Green (green), plus teal for water, are flat UI series colours. They are always printed next to the resource name.
- **Scene resource colours** (scene-medical, scene-water, scene-shelter): muted versions of the resource identities. They are used only for lit Lambert bars in the 3D network, where full-strength UI hues would glare. Zone input stems for severity, vulnerability and time-criticality use the blue ramp scene-grid → scene-input-2 → scene-input-3. Supply routes are scene-route, and zone discs are scene-zone-disc.
- **Segment Slates** (segment-slate-1 … 6): request-bar zone segments, cycled in order. They are low-luminance slates, so the teal stock marker and the amber over-stock outline are the only colours that speak on the bar.

### Neutral
- **Night Ink** (ink-950 → ink-600): the landing ground, the hero frame, the story-panel glass, the mobile nav and the landing boards.
- **Sky Gradient** (sky-top → sky-mid → sky-horizon): the hero frame atmosphere. The story stage repeats it with **Stage Horizon** (stage-horizon) as the glow where the polar grid recedes, then falls through **Scene Fog** (scene-fog) to a dark ground. The 3D fog uses the same scene-fog value, so geometry dissolves into the painted sky.
- **Mission Ground** (dash-ground): the dashboard application ground. **Sidebar Ink** (dash-sidebar) is the sidebar. **Panel Ink** (dash-panel) is every panel and metric tile. **Hover Ink** (dash-hover), **Raised Ink** (dash-raised: active nav row, tray) and **Checked Ink** (dash-checked: checked tab, scrollbar) are the raised steps.
- **Hairline** (line / dash-line) and **Strong Hairline** (line-strong / dash-line-strong): panel borders and row dividers, then interactive outlines and badges. On the dashboard these are opaque hexes, not translucent washes.
- **Focus Mint** (line-focus / dash-focus): the 2px focus ring.
- **Ice Text** (text / dash-text), **Mist Text** (text-2 / dash-text-2) and **Dusk Text** (text-3 / dash-text-3): primary, secondary and tertiary text. **Inverse Ink** (text-inverse) is text on white or teal pills.
- **Frost White** (frost-white): the fill of the primary pill.
- **Accent Mist** (accent-mist): the tint of the serif accent phrase in section headings.

### Measured contrast (dashboard palette, WCAG 2.x, computed from the hexes)
| Text | on dash-panel #111821 | on dash-raised #17212c | on dash-ground #080b10 | on dash-checked #212c39 |
|---|---|---|---|---|
| dash-text #eaf0f4 | 15.53:1 | 14.16:1 | 17.14:1 | 12.31:1 |
| dash-text-2 #a2b0c0 | 8.08:1 | 7.37:1 | 8.92:1 | 6.41:1 |
| dash-text-3 #7d8a9b | 5.08:1 | 4.63:1 | 5.61:1 | **4.03:1** |

Signal text on dash-panel: dash-teal 8.81:1, dash-amber 8.64:1, dash-red 5.70:1, dash-red-text 7.64:1. On the landing palette, text-2 and text-3 measure 10.02:1 and 6.49:1 on ink-800 (#0c1626).

**Tokens in code (Stage 5).** Colours that were literals in the stylesheets are now custom properties in `tokens.css`, with identical rendered values:

- `--teal-text` (#8ff0e9, used for teal text and links on dark grounds);
- `--stage-horizon`, `--scene-fog`, `--stage-floor` (#060c17) and `--sky-top` / `--ink-950` (the story-stage gradient stops);
- `--ground-deep` (#050b14, the hero ground below the ridge);
- `--surface-window` (rgba(7, 13, 24, 0.95), the preview window).

Translucent tints of existing hues (for example rgba(63, 208, 201, 0.4)) stay inline beside the hue they tint. A reading measure, `--measure: 62ch` (about 75–80 characters in Mona Sans), caps dashboard descriptions and notes.

### Named Rules
**The Signal Grammar Rule.** Teal means stock, amber means shortfall, and red means critical, and nothing else. If an element is not stating one of those facts, it uses neutrals. This includes the 3D scene: caps are teal, unmet demand and stale routes are amber.

**The Spoken Colour Rule.** Colour never carries meaning alone. Every dot, bar or tinted value sits beside text that says the same thing ("60 short", "Depot empty", "Engine online").

**The Two Rooms Rule.** Anything that depicts or is the dashboard (`.dash`, `.preview__window`) takes the `.dash-palette` overrides. Landing atmosphere, story panels and section boards stay on the navy palette. Never mix the two inside one surface.

**The Dusk Floor Rule.** Dusk Text stops at Raised Ink (4.63:1). It never sits on Checked Ink (4.03:1) or anything brighter.

## Typography

**Display Font:** Mona Sans Variable (with Segoe UI, system-ui)
**Body Font:** Mona Sans Variable
**Accent Font:** Instrument Serif italic (with Georgia)
**Label/Mono Font:** JetBrains Mono Variable (with ui-monospace, Cascadia Mono)

**Character:** A tight, confident grotesque carries everything, and a single soft italic serif phrase gives each major heading its human voice. All fonts are self-hosted because the demo must run offline.

### Hierarchy
- **Display** (600, fluid 40–74px, 1.03, -0.035em): the hero headline only. Its second line is the serif accent.
- **Headline** (600, fluid 32–48px, 1.08, -0.03em): landing section headings, including the story intro ("How a shortage becomes *a decision.*") and the closing reveal. The accent phrase is set at 1.12em in Accent Mist.
- **Title** (600, 28px, -0.025em): dashboard page titles.
- **Story Title** (600, fluid 22–28px, -0.025em): chapter headings in the story reading panels. They drop to 19px under 900px.
- **Metric Value** (600, 30px, 1.1, -0.02em): dashboard figures. Word values (a status) step down to 22px so they never wrap a tile.
- **Title Small** (600, 16px, -0.01em): panel titles. Feature panels use 22px.
- **Body** (400, 16px, 1.55): running text, including story chapter bodies in Mist Text. Landing ledes are 17px with a 62ch measure.
- **Body Small** (400, 13px): panel descriptions, metric labels, story status lines, 3D scene labels and captions.
- **Label** (500, 12px, sentence case): badges, legends, nav group labels, stage tags and request-bar figures.
- **Mono** (0.92em): scenario ids, seeds, snapshot hashes, versions, formulas, constraint rules, FSM state names and the ridge's place labels.
- **Numbers**: use Mona Sans with `tabular-nums`, not mono, in tables, metrics, 3D labels and request bars.

### Named Rules
**The One Accent Phrase Rule.** Each heading gets at most one italic serif phrase, and it always comes last. The serif never appears in body, UI, buttons, numbers or the 3D labels.

**The Machine Voice Rule.** Mono is for things a machine produced or reads: ids, hashes, formulas, constraint expressions and state names. The ridge's map labels are the world's one mono exception. Quantities stay in the sans.

**The No Eyebrow Rule.** A heading carries its own weight. No small label or kicker sits above it. Story status badges sit below the chapter title, never above it.

## Layout

**Landing narrative order:** hero frame → resource story → how it works (workflow) → feature explorer → methodology → about → dashboard reveal → footer.

The landing page sits inside framed windows inset 20px (`--frame-inset`) from the viewport. The hero frame has a 76px header overlaid at its top, centred copy (the subcopy is capped at 660px), and the dashboard preview window (at most 1040px wide) rising in front of the ridge to meet the frame's bottom edge. The ridge is drawn at a fixed 1440×360 and never scales. Below 1180px its markers and labels hide.

**The resource story** is a sticky stage: a second framed window (28px radius, Strong Hairline border) that is one viewport tall minus the frame inset on each side. It is pinned with CSS `position: sticky`, not a JavaScript pin. Nine chapter slots (86svh each, and 100svh for the last) scroll over it. Each holds a reading panel at most 430px wide (36vw), set at the left on desktop. The 3D camera lens shifts the network into the space to the right of that column. Under 900px the panel goes full width and sits at the bottom of a stage-tall slot, and the camera shifts the network up above it. HTML labels are never placed under the reading card or below the top of the phone panel.

Content sections use a 1200px container with a fluid 16–40px gutter and 80–136px vertical rhythm. Two-column sections use asymmetric fractions (5fr/7fr). Lists of points sit in plain columns divided by space or hairlines, not in cards.

The dashboard is a 264px sticky sidebar plus a body with a sticky 64px top bar, and the main column is capped at 1480px. Pages stack at a 24px gap. Grids are asymmetric (7fr/5fr, and 8fr plus a sticky aside on Allocate). Metrics run in a five-across row at a 12px gap.

Spacing follows a 4px base (4–112px). Landing breakpoints are 1180, 1080, 900 (story stacks, the phone camera takes over), 720 and 480px. Dashboard breakpoints are 1280, 1024 (the sidebar becomes an off-canvas drawer with a scrim) and 720px.

**The Hairline Column Rule.** Inside a panel, structure comes from hairline-divided rows and columns. A panel never contains another card.

**The Native Scroll Rule.** Scroll position is the only conductor. GSAP ScrollTrigger measures it and turns it into a fractional chapter value, a `--focus` value per step and scrubbed tweens. Nothing intercepts the wheel, snaps the page or hides content before the script runs.

## Elevation & Depth

At rest, the system is flat and tonal. Landing depth comes from the ink ramp, the sky gradient, blurred aurora bands at low opacity and a masked grid. Dashboard depth comes from surface steps (ground #080b10 → panel #111821 → raised #17212c). In-flow dashboard panels and metric tiles carry only `--surface-lift`, a 1px inset top highlight, never a cast shadow. Selected states use an inset 1px hairline ring, not a lift. Only layers that genuinely float cast shadows: the mobile nav, tooltips, the off-canvas sidebar, the hero window and the story reading panels that float over the 3D stage.

The 3D scene gets its depth from perspective, distance fog (13–30 world units on desktop, 26–64 on phones) and one ambient light (0.6) plus one directional light (1.1). It has no shadow maps and no post-processing.

### Shadow Vocabulary
- **Raised** (`box-shadow: 0 18px 50px -20px rgba(0,0,0,0.6), 0 2px 6px rgba(0,0,0,0.25)`): floating layers only, such as the mobile nav, chart tooltips, the off-canvas sidebar and story reading panels.
- **Window** (`box-shadow: 0 -24px 80px -10px rgba(0,0,0,0.55)`): the hero dashboard window, which casts upward onto the ridge.
- **Surface lift** (`box-shadow: inset 0 1px 0 rgba(255,255,255,0.03)`): every dashboard panel and metric tile.
- **Hairline ring** (`box-shadow: inset 0 0 0 1px var(--line-strong)`): the active nav row and the checked policy tab.

### Named Rules
**The Flat Panel Rule.** In-flow panels, metrics and boards never cast a shadow. Their edge is a hairline, and the only addition is the inset top highlight from Surface lift.

**The Lit-Not-Shadowed Rule.** The 3D world has no shadows, no bloom and no glow. Fog and two lights are its whole lighting kit.

## Shapes

The form language is soft and rounded. Pills (999px) are for every button, badge, nav link, stage tag and 3D scene label. Containers step up a radius scale: 8px for small rows, 12px for preview tiles and tab groups, 14px (`--radius-panel`) for every dashboard panel, metric tile and skeleton, 18px for story panels, boards and the preview window, 22px for the feature panel, and 28px for the hero, story-stage and reveal frames (20px under 720px). Circles are used for status dots, workflow nodes and the primary button's icon disc. Data bars stay nearly square (2–5px). The depot in the 3D scene is a hexagonal ring and zones are circular rings, which echo the circles in the UI.

**The Dashed Promise Rule.** A dashed hairline means "planned" or "nothing here yet". Use it for planned-stage badges and tags, planned workflow nodes and connectors, empty request bars, unbuilt parts of the preview, and stale routes in the 3D adapt chapter. A solid border never means planned, and a dashed border is never decorative.

## Components

### Buttons
Tactile pills with two voices: frost white and night glass.
- **Shape:** fully round pill (999px), 44px tall (40px for the quiet and header variants).
- **Primary:** Frost White fill with Inverse Ink text, 15px/500. A 32px dark disc on the right holds an arrow, and the disc rotates 45° on hover. Hover fills pure white.
- **Secondary:** translucent night glass (rgba(7,13,24,0.72)) with a Strong Hairline border. Hover moves to ink-750.
- **Quiet:** transparent with a Strong Hairline border, used for dashboard actions.
- **Accent:** a teal fill with Inverse Ink text at 600, reserved for running an engine action on a snapshot. While the engine runs, a 16px loader icon turns inside the button next to the text "Running FCFS on the engine…". This is the only spinning element in the product.
- **States:** press nudges the button down 1px. Disabled sets 0.5 opacity and a not-allowed cursor. Focus shows a 2px Focus Mint ring offset 3px.

### Badges
- **Style:** 24px pill, 12px/500, a 6px currentColor dot, and a Strong Hairline border.
- **Variants:** built (teal-soft fill, Mint Readout), partial (blue tint, #b9d9ff text), synthetic or warn (amber-soft, Amber Readout), critical (red-soft, red-text), ok (teal outline) and neutral. **Planned** is Mist Text with a dashed border and reads "Planned · Stage N".
- **Story status vocabulary:** Synthetic data (synthetic tone), Concept (planned tone), Partly built (partial tone) and Illustration (planned tone). Each badge is followed by a Dusk Text line naming exactly what is and is not built.

### Cards / Containers
- **Dashboard panel:** Panel Ink, 1px Hairline, 14px radius, Surface lift, 20px 22px padding. The head has a 16px title over a 13px Dusk description, with actions at the right.
- **Metric tile:** the same material at 16px 18px padding. Warn tiles mix 5% amber into the fill and 24% into the border. Critical tiles mix 6% red into the fill and 30% into the border.
- **Landing board / feature panel:** a faint navy vertical gradient with a Strong Hairline border, at an 18–22px radius.
- **Story reading panel:** rgba(7,13,24,0.92) glass with a Strong Hairline border, an 18px radius and the Raised shadow. Its opacity is `0.28 + 0.72 × --focus`, so the chapter in view reads fully and its neighbours recede.

### Inputs / Fields
- **Style:** 40px Panel Ink select with a Strong Hairline border, about 10px radius, and a custom chevron.
- **Focus:** the global 2px Focus Mint ring.
- **Policy tabs:** a segmented radio group in a 4px-padded tray. The checked tab fills with Checked Ink and gets a hairline ring. Unavailable policies stay visible but disabled, with a dashed "Stage N" tag.

### Navigation
- **Landing header:** centred pill links in Mist Text at 15px that brighten with a 5% white wash on hover. The CTA pill sits at the right. Below the breakpoint it becomes a 44px menu button that opens a raised sheet.
- **Dashboard sidebar:** 42px rows on Sidebar Ink at 14px Mist Text with icons. The active row is Raised Ink with a hairline ring and a teal icon. Planned routes sit under "Later stages" with a dashed stage tag.

### Request Bar (signature)
This shows demand against stock on one line, on both the landing page and the dashboard. A 34px row (24px in the phone story) of Segment Slate blocks shows per-zone requests, each labelled with its zone letter and a 12px/600 tabular figure. A 2px teal stock marker with a "N in stock" label cuts across it, and the label hugs the inside edge when the marker is within 18% of either end. Everything past the marker gets a 1px amber outline (75% alpha) with square left corners, marking the part no plan can serve. An empty request is a dashed "No requests" placeholder.

### Resource Network Story (signature)
One persistent Three.js scene (React Three Fiber, lazy loaded only when the section is within 900px of the viewport and WebGL exists) is conducted across nine chapters: depot, zones, routes, requests, shortage, fuzzy, constraints, oversight, adapt. Each chapter maps to a world state (0–1 per layer) and a camera pose, and the scene interpolates between neighbouring chapters on the fractional scroll value with frame-rate-independent damping (λ 4.2).
- **Rendering:** `frameloop="demand"`, so a frame is drawn only when progress changes or the camera is still settling. DPR is capped at 1.5 (1.25 on phones). Antialiasing is on, with no shadows. Geometry is generated from the synthetic fixture at one scale (1/60 world unit per supply unit).
- **Text:** never in WebGL. Labels are 13px HTML pills (12px on phones) projected from 3D anchors and placed in priority order. Each tries above its anchor, then below its base. It must stay inside the stage, to the right of the reading card and clear of earlier labels. Optional labels hide, and required ones never do.
- **Fallback:** a static SVG poster of the same layout, seen from above. It shows while the chunk loads, and permanently if WebGL is missing, the chunk fails, or the context is lost.
- **Evidence:** chapters that need numbers render real HTML inside the reading panel: request bars (shortage), a ratings table with a "Stage 2" priority column (fuzzy), and mono constraint lines (constraints).

### Dashboard Motion
- **Entrance:** page sections rise 6px and fade in over 320ms on the ease-out curve, staggered 30ms in reading order and capped at 120ms from the fifth child on. Pages are keyed by snapshot hash, so switching scenario replays this crossfade instead of mutating in place.
- **Value changed:** a metric figure that differs from the previous scenario flashes a Teal Soft wash and a 4px ring for 350ms, then settles.
- **Stale gate:** while the next scenario loads, the previous one stays readable at 0.55 opacity with pointer events off and `aria-busy`.
- **Not used:** spinners for data loads (first loads use 14px-radius skeletons that pulse at 1.6s) and counting-up numbers.

### Hero Dashboard Window (signature)
A browser-style window on the `.dash-palette` with three ink dots, a breadcrumb with a mono scenario id and an amber "Preview · synthetic scenario" tag. Inside is a sidebar with dashed planned tags, a KPI row and resource tiles. It rises 36px over 1100ms after a 120ms delay, using transform only. It is reused in the closing reveal, where its CSS rise is off and GSAP squares it up from a rotateX tilt (16° wide, 8° narrow) and a 0.94 scale as it reaches the centre.

## Do's and Don'ts

### Do:
- **Do** keep both rooms in one world: the navy palette for the landing atmosphere and story, and the `.dash-palette` near-black for anything that is or depicts the dashboard.
- **Do** pair every signal colour with words: teal for stock, amber for shortfall, red only for critical states such as "Depot empty".
- **Do** label unbuilt work as "Planned · Stage N" with a dashed outline, mark uncommitted results "Candidate plan · not committed", and give every non-data story chapter a Synthetic data, Concept, Partly built or Illustration badge with a line saying what is real.
- **Do** show numbers only when the backend or the synthetic fixture supplied them, in tabular sans figures.
- **Do** limit each heading to one italic Instrument Serif phrase, placed last.
- **Do** use mono only for ids, hashes, seeds, formulas, constraint expressions and state names.
- **Do** drive landing motion from native scroll through one shared GSAP setup (`lib/motion.ts`, `expo.out`), guarded by `gsap.matchMedia` with a `prefers-reduced-motion: no-preference` condition.
- **Do** make reduced motion complete, not empty: the 3D scene snaps to the nearest chapter, story panels stay fully opaque, and CSS animations collapse to 0.01ms.
- **Do** keep text out of WebGL and keep the SVG poster as a working fallback for every 3D state.
- **Do** keep dashboard motion to single-play transform and opacity at 320–350ms on the ease-out curve (cubic-bezier(0.16, 1, 0.3, 1)).

### Don't:
- **Don't** put copy beside a screenshot in a split hero, or build a wall of feature cards.
- **Don't** nest cards inside panels or cast shadows from in-flow panels.
- **Don't** use red for emphasis, branding or anything short of critical.
- **Don't** put a small label or kicker above a heading, or use uppercase tracked labels.
- **Don't** scroll-jack: no wheel interception, scroll snapping, smooth-scroll libraries or JavaScript pinning. The story stage is pinned with CSS sticky.
- **Don't** add a second 3D canvas, shadow maps, bloom or a DPR above 1.5.
- **Don't** use spinners for data loading or animate numbers counting up.
- **Don't** put Dusk Text on Checked Ink or brighter (4.03:1).
- **Don't** scale the ridge with the viewport, or show its markers and labels below 1180px.
- **Don't** use a dashed border for decoration. It means "planned".
- **Don't** show placeholder metrics as if they were real.
