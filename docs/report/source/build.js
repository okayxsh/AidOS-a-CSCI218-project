// Builds docs/report/AidOS_Final_Group_Report.docx (raw; Word then updates the TOC and exports PDF).
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const d = require('docx');
const JSZip = require('jszip');
const L = require('./lib');
const REFS = require('./refs');

const {
  Document, Packer, Paragraph, TextRun, Header, Footer, AlignmentType, PageNumber, NumberFormat: PageNumberFormat,
  TableOfContents, LevelFormat, Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  TableLayoutType, VerticalAlign, SectionType, TabStopType, PageBreak,
} = d;
const { C, FONT, FONT_LIGHT, CONTENT_W, runs } = L;

const ROOT = process.argv[2];
const OUT = process.argv[3];
const VER = JSON.parse(fs.readFileSync(process.argv[4], 'utf8'));

// ---------- data helpers ----------
const mdCache = {};
function md(rel, marker, nth = 0) {
  const text = (mdCache[rel] ||= fs.readFileSync(path.join(ROOT, rel), 'utf8').replace(/\r/g, ''));
  const lines = text.split('\n');
  const start = lines.findIndex((l) => l.includes(marker));
  if (start < 0) throw new Error(`marker not found in ${rel}: ${marker}`);
  const tables = [];
  let cur = null;
  for (let i = start; i < lines.length && tables.length <= nth; i++) {
    const l = lines[i].trim();
    if (l.startsWith('|')) { (cur ||= []).push(l); } else if (cur) { tables.push(cur); cur = null; }
  }
  if (cur) tables.push(cur);
  const t = tables[nth];
  if (!t) throw new Error(`table ${nth} not found after ${marker} in ${rel}`);
  const parse = (l) => l.replace(/^\||\|$/g, '').split('|').map((c) => clean(c.trim()));
  const rows = t.filter((l) => !/^\|\s*:?-{2,}/.test(l)).map(parse);
  return { header: rows[0], rows: rows.slice(1) };
}
function clean(c) {
  return c.replace(/\\([*_|])/g, '$1').replace(/([A-Za-z)])\*(?!\*)/g, '$1 †').replace(/\*\*\*$/, '').replace(/^\*\*(.*)\*\*$/, '$1');
}

const V = {
  ...VER,
  diag: (n) => path.join(ROOT, 'docs/report/figures/diagrams', n + '.png'),
  shot: (n) => path.join(ROOT, 'docs/report/figures/screenshots', n + '.png'),
  res: (n) => path.join(ROOT, 'docs/report/figures/results', n + '.png'),
};

// run directory integrity, recomputed now
const roles = {
  'extended-': 'Stage 4 main evidence', 'standard-': 'Stage 4 independent re-run',
  'supplementary-greedy': 'Stage 5 equivalence', 'supplementary-floor': 'Stage 5 floor sweep',
  'supplementary-fuzzy': 'Stage 5 fuzzy sensitivity', 'supplementary-dynamic': 'Stage 5 controlled dynamic',
  'supplementary-runtime': 'Stage 5 runtime', 'supplementary-stage4': 'Stage 5 audit of Stage 4',
};
V.runs = fs.readdirSync(path.join(ROOT, 'experiments/results')).filter((n) => !n.startsWith('smoke-') && fs.statSync(path.join(ROOT, 'experiments/results', n)).isDirectory()).sort().map((id) => {
  const dir = path.join(ROOT, 'experiments/results', id);
  const man = JSON.parse(fs.readFileSync(path.join(dir, 'manifest.json'), 'utf8'));
  let sums = man.checksums || man.files || {};
  if (Array.isArray(sums)) sums = Object.fromEntries(sums.map((e) => [e.path || e.file, e.sha256]));
  const entries = Object.entries(sums);
  const bad = entries.filter(([f, h]) => crypto.createHash('sha256').update(fs.readFileSync(path.join(dir, f))).digest('hex') !== (typeof h === 'string' ? h : h.sha256));
  const role = Object.entries(roles).find(([k]) => id.startsWith(k));
  return { id, role: role ? role[1] : '', files: entries.length, ok: bad.length ? `${bad.length} MISMATCH` : `all match (${man.status})` };
});

// ---------- content ----------
const ctx = { labels: {}, refs: REFS, citeOrder: [], missing: new Set(), listId: 0 };
ctx.resolve = L.makeResolver(ctx);
const D = {
  ROOT, V, md,
  P: (text, o = {}) => ({ t: 'p', text, ...o }),
  H1: (text, id, o = {}) => ({ t: 'h1', text, id, ...o }),
  H2: (text, id) => ({ t: 'h2', text, id }),
  H3: (text, id) => ({ t: 'h3', text, id }),
  B: (items, numbered) => ({ t: 'bullets', items, numbered }),
  T: (o) => ({ t: 'table', ...o }),
  F: (o) => ({ t: 'figure', ...o }),
  E: (o) => ({ t: 'eq', ...o }),
  CODE: (o) => ({ t: 'code', ...o }),
  NOTE: (title, text) => ({ t: 'callout', title, text }),
};
const blocks = [...require('./content1')(D), ...require('./content2')(D)];
const appendix = require('./content3')(D);
const refsBlocks = [D.H1('References', 'refs', { pageBreak: true })];
const all = [...blocks, ...refsBlocks, ...appendix];
L.assignNumbers(all, ctx);
fs.writeFileSync(path.join(__dirname, 'labels_out.json'), JSON.stringify(all.filter((b) => (b.t === 'figure' || b.t === 'table' || b.t === 'code') && b.caption).map((b) => ({ kind: b.t === 'table' ? 'Table' : 'Figure', id: b.id, num: ctx.labels[(b.t === 'table' ? 'tab:' : 'fig:') + b.id], caption: b.caption, path: b.path ? path.relative(ROOT, b.path).split(path.sep).join('/') : null }))
  .concat(all.filter((b) => /^h[123]$/.test(b.t) && b.num).map((b) => ({ kind: 'Section', id: b.id || null, num: b.num, caption: b.text }))), null, 1));

// Lists of figures/tables need captions in styles; the bibliography needs the citation order,
// which is only known after rendering the body, so render body first, then references.
const bodyParas = L.render(blocks, ctx);
const appParas = L.render(appendix, ctx);
const refParas = [
  ...L.render(refsBlocks, ctx),
  ...ctx.citeOrder.map((k, i) => new Paragraph({
    style: 'Reference',
    children: [new TextRun({ text: `[${i + 1}]\t` }), ...runs(REFS[k], {}, null)],
  })),
];
const unused = Object.keys(REFS).filter((k) => !ctx.citeOrder.includes(k));

// ---------- cover ----------
const cell = (text, o = {}) => new TableCell({
  width: { size: o.w, type: WidthType.DXA },
  borders: { top: L.NONE, left: L.NONE, right: L.NONE, bottom: L.line(C.light, 4) },
  margins: { top: 70, bottom: 70, left: 0, right: 120 },
  children: [new Paragraph({ spacing: { before: 0, after: 0 }, children: runs(text, { size: 19, color: o.color || C.ink, bold: o.bold }, null) })],
});
const detail = (label, value) => new TableRow({ children: [cell(label, { w: 2600, color: C.muted }), cell(value, { w: CONTENT_W - 2600 })] });
const cover = [
  new Paragraph({ spacing: { before: 400, after: 0 }, children: [new TextRun({ text: 'CSCI218 FOUNDATIONS OF ARTIFICIAL INTELLIGENCE  ·  GROUP PROJECT REPORT', font: FONT, size: 18, bold: true, color: C.teal, characterSpacing: 20 })] }),
  new Paragraph({ spacing: { before: 1500, after: 0 }, children: [new TextRun({ text: 'AidOS', font: FONT_LIGHT, size: 104, color: C.navy })] }),
  new Paragraph({ spacing: { before: 60, after: 0 }, children: [new TextRun({ text: 'Explainable AI for Emergency Resource Allocation', font: FONT_LIGHT, size: 40, color: C.navy })] }),
  new Paragraph({ spacing: { before: 120, after: 360 }, border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: C.teal, space: 12 } }, children: [new TextRun({ text: 'Fuzzy urgency inference, constraint optimisation and crisis simulation', font: FONT, size: 24, color: C.muted })] }),
  new Paragraph({ spacing: { before: 240, after: 600 }, alignment: AlignmentType.LEFT, children: runs('A synthetic academic decision-support prototype that scores zone urgency with a zero-order Sugeno fuzzy system, allocates scarce relief supplies with Google OR-Tools CP-SAT under hard stock and demand limits, compares the result with transparent baselines, and replays crisis events through a finite-state simulator.', { size: 21, color: C.ink }, null) }),
  new Table({
    width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: [2600, CONTENT_W - 2600], layout: TableLayoutType.FIXED,
    borders: { top: L.line(C.navy, 8), bottom: L.NONE, left: L.NONE, right: L.NONE, insideHorizontal: L.NONE, insideVertical: L.NONE },
    rows: [
      detail('University', 'University of Wollongong in Dubai'),
      detail('Subject', 'CSCI218 Foundations of Artificial Intelligence, Autumn 2026'),
      detail('Topic', 'Topic 11, Dubai Humanitarian use case: Project C, Emergency Resource Allocation Simulation'),
      detail('Group members', '[[Name, student ID]]  ·  [[Name, student ID]]  ·  [[Name, student ID]]  ·  [[Name, student ID]]  ·  [[Name, student ID, if applicable]]'),
      detail('Lab group / instructor', '[[Lab group]]  ·  [[Instructor name]]'),
      detail('Repository', 'https://github.com/okayxsh/AidOS-a-CSCI218-project'),
      detail('Submission date', '[[As shown on the Moodle/Turnitin submission link]]'),
    ],
  }),
  new Paragraph({ spacing: { before: 700, after: 0 }, alignment: AlignmentType.LEFT, children: runs('**Synthetic data only.** All scenarios are synthetic and all results describe a simulation. AidOS has not been deployed or validated with humanitarian practitioners, and makes no claim about real-world outcomes.', { size: 17, color: C.muted }, null) }),
  new Paragraph({ spacing: { before: 160 }, alignment: AlignmentType.LEFT, children: runs('Text highlighted in [[yellow]] is team-specific information that the group must complete before submission. Everything else is drawn from the project\'s code, documentation and saved experiment artifacts.', { size: 18, color: C.muted }, null) }),
];

// ---------- front matter ----------
const frontTitle = (t, newPage = false) =>
  new Paragraph({ style: 'FrontTitle', pageBreakBefore: newPage, children: [new TextRun(t)] });
const front = [
  frontTitle('Contents'),
  new TableOfContents('Contents', { hyperlink: true, headingStyleRange: '1-2' }),
  frontTitle('List of Figures', true),
  new TableOfContents('List of Figures', { hyperlink: true, stylesWithLevels: [{ styleName: 'Figure Caption', level: 3 }] }),
  frontTitle('List of Tables', true),
  new TableOfContents('List of Tables', { hyperlink: true, stylesWithLevels: [{ styleName: 'Table Caption', level: 3 }] }),
];

// ---------- styles ----------
const styles = {
  default: { document: { run: { font: FONT, size: 21, color: C.ink }, paragraph: { spacing: { after: 120, line: 276 } } } },
  paragraphStyles: [
    { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: FONT_LIGHT, size: 40, color: C.navy }, paragraph: { spacing: { before: 480, after: 240 }, keepNext: true, keepLines: true, outlineLevel: 0, border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: C.teal, space: 6 } } } },
    { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: FONT, size: 27, bold: true, color: C.navy }, paragraph: { spacing: { before: 320, after: 120 }, keepNext: true, keepLines: true, outlineLevel: 1 } },
    { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: FONT, size: 22, bold: true, color: C.teal }, paragraph: { spacing: { before: 220, after: 80 }, keepNext: true, keepLines: true, outlineLevel: 2 } },
    { id: 'FigureCaption', name: 'Figure Caption', basedOn: 'Normal', next: 'Normal', run: { font: FONT, size: 18, color: C.ink }, paragraph: { spacing: { before: 60, after: 220, line: 252 }, alignment: AlignmentType.LEFT } },
    { id: 'TableCaption', name: 'Table Caption', basedOn: 'Normal', next: 'Normal', run: { font: FONT, size: 18, color: C.ink }, paragraph: { spacing: { before: 200, after: 80, line: 252 }, keepNext: true, alignment: AlignmentType.LEFT } },
    { id: 'Reference', name: 'Reference', basedOn: 'Normal', run: { font: FONT, size: 19 }, paragraph: { spacing: { after: 90, line: 252 }, indent: { left: 560, hanging: 560 }, tabStops: [{ type: TabStopType.LEFT, position: 560 }], alignment: AlignmentType.LEFT } },
    { id: 'FrontTitle', name: 'Front Title', basedOn: 'Normal', run: { font: FONT_LIGHT, size: 40, color: C.navy }, paragraph: { spacing: { before: 0, after: 240 }, border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: C.teal, space: 6 } } } },
    { id: 'TOC1', name: 'toc 1', basedOn: 'Normal', next: 'Normal', run: { font: FONT, size: 19, bold: true, color: C.navy }, paragraph: { spacing: { before: 20, after: 0, line: 240 } } },
    { id: 'TOC2', name: 'toc 2', basedOn: 'Normal', next: 'Normal', run: { font: FONT, size: 18 }, paragraph: { spacing: { before: 0, after: 0, line: 240 }, indent: { left: 360 } } },
    { id: 'TOC3', name: 'toc 3', basedOn: 'Normal', next: 'Normal', run: { font: FONT, size: 19, color: C.ink }, paragraph: { spacing: { before: 0, after: 30, line: 240 }, indent: { left: 0, hanging: 0 } } },
    { id: 'TableofFigures', name: 'table of figures', basedOn: 'Normal', next: 'Normal', run: { font: FONT, size: 19 }, paragraph: { spacing: { after: 50 }, indent: { left: 0 } } },
  ],
};

const bulletLevels = [0, 1].map((lvl) => ({ level: lvl, format: LevelFormat.BULLET, text: lvl ? '–' : '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 400 + lvl * 360, hanging: 280 } }, run: { color: C.teal } } }));
const numbering = {
  config: [
    { reference: 'bullets', levels: bulletLevels },
    ...Array.from({ length: 30 }, (_, i) => ({ reference: `numbers-${i}`, levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 400, hanging: 300 } }, run: { color: C.navy, bold: true } } }] })),
  ],
};

// ---------- header / footer ----------
const header = new Header({ children: [new Paragraph({ border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: C.rule, space: 4 } }, tabStops: [{ type: TabStopType.RIGHT, position: CONTENT_W }], children: [new TextRun({ text: 'AidOS  ·  CSCI218 Group Project Report', size: 16, color: C.muted }), new TextRun({ text: '\tAutumn 2026', size: 16, color: C.muted })] })] });
const footer = (fmt) => new Footer({ children: [new Paragraph({ tabStops: [{ type: TabStopType.RIGHT, position: CONTENT_W }], children: [new TextRun({ text: 'University of Wollongong in Dubai  ·  synthetic academic prototype', size: 16, color: C.muted }), new TextRun({ children: ['\t', PageNumber.CURRENT], size: 17, color: C.navy })] })] });
const page = (fmt, start) => ({ size: { width: 11906, height: 16838 }, margin: { top: 1300, bottom: 1250, left: L.MARGIN_LR, right: L.MARGIN_LR, header: 600, footer: 600 }, pageNumbers: { start, formatType: fmt } });

const doc = new Document({
  creator: '[[CSCI218 group]]',
  title: 'AidOS: Explainable AI for Emergency Resource Allocation',
  description: 'CSCI218 group project report (synthetic academic prototype)',
  styles, numbering,
  features: { updateFields: true },
  sections: [
    { properties: { page: page(PageNumberFormat.LOWER_ROMAN, 1) }, children: cover },
    { properties: { type: SectionType.NEXT_PAGE, page: page(PageNumberFormat.LOWER_ROMAN, 1) }, headers: { default: header }, footers: { default: footer() }, children: front },
    { properties: { type: SectionType.NEXT_PAGE, page: page(PageNumberFormat.DECIMAL, 1) }, headers: { default: header }, footers: { default: footer() }, children: [...bodyParas, ...refParas, ...appParas] },
  ],
});

Packer.toBuffer(doc).then(async (buf) => {
  // Function names in equations upright (OMML m:sty p) rather than italic variables.
  const zip = await JSZip.loadAsync(buf);
  let xml = await zip.file('word/document.xml').async('string');
  const words = ['max', 'min', 'round', 'arrivals', 'losses', 'dispatched', 'ledger', 'initial', 'final', 'with', 'and'];
  xml = xml.replace(/<m:r>(<w:rPr>[\s\S]*?<\/w:rPr>)?<m:t([^>]*)>([^<]*)<\/m:t><\/m:r>/g, (m, rpr, attrs, text) => {
    const plain = words.some((w) => new RegExp(`(^|[^A-Za-z])${w}([^A-Za-z]|$)`).test(text));
    return plain ? `<m:r><m:rPr><m:sty m:val="p"/></m:rPr>${rpr || ''}<m:t${attrs}>${text}</m:t></m:r>` : m;
  });
  zip.file('word/document.xml', xml);
  const out = await zip.generateAsync({ type: 'nodebuffer', compression: 'DEFLATE' });
  fs.writeFileSync(OUT, out);
  console.log('wrote', OUT, 'figures', Object.keys(ctx.labels).filter((k) => k.startsWith('fig:')).length, 'tables', Object.keys(ctx.labels).filter((k) => k.startsWith('tab:')).length, 'refs cited', ctx.citeOrder.length);
  if (unused.length) console.log('UNCITED refs:', unused.join(', '));
  if (ctx.missing.size) { console.log('MISSING labels:', [...ctx.missing].join(', ')); process.exitCode = 2; }
  console.log('runs', JSON.stringify(V.runs.map((r) => [r.id, r.ok])));
});
