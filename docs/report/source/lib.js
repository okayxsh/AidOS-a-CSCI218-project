// Small document builder on top of docx-js for the AidOS report.
// Content is a list of plain block objects; numbering of sections, figures, tables and equations
// and the resolution of {fig:x}/{tab:x}/{eq:x}/{sec:x}/[@ref] markers happen here.
const fs = require('fs');
const path = require('path');
const d = require('docx');
const {
  Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType, BorderStyle, AlignmentType,
  VerticalAlign, ShadingType, HeadingLevel, PageBreak, Math: OMath, MathRun, MathFraction, MathSum,
  MathSubScript, MathSuperScript, MathSubSuperScript, TabStopType, TableLayoutType, HeightRule,
} = d;

const C = {
  navy: '13283B', teal: '087F84', ink: '1E2933', muted: '5B6B7A', rule: 'C9D3DA', light: 'E3E9ED',
  fill: 'EEF4F6', headFill: 'E8EFF2', codeFill: 'F4F6F8', amber: '9A6412', hl: 'FFF2A8',
};
const FONT = 'Calibri';
const FONT_LIGHT = 'Calibri Light';
const MONO = 'Consolas';
const PAGE_W = 11906, MARGIN_LR = 1247;
const CONTENT_W = PAGE_W - 2 * MARGIN_LR; // 9412 DXA

// ---------- inline markup ----------
// **bold**, *italic*, `code`, _{sub}, ^{sup}, [[placeholder]], {fig:id} {tab:id} {eq:id} {sec:id}, [@key,@key]
function makeResolver(ctx) {
  return (s) => s
    .replace(/\{(fig|tab|eq|sec|app):([\w-]+)\}/g, (m, kind, id) => {
      const v = ctx.labels[`${kind}:${id}`];
      if (v === undefined) { ctx.missing.add(m); return `??${id}??`; }
      return kind === 'fig' ? `Figure ${v}` : kind === 'tab' ? `Table ${v}` : kind === 'eq' ? `Equation (${v})` : v;
    })
    .replace(/\[@([\w@,\s-]+)\]/g, (m, keys) => {
      const nums = keys.split(',').map((k) => k.trim().replace(/^@/, '')).map((k) => {
        if (!ctx.refs[k]) { ctx.missing.add('@' + k); return '?'; }
        if (!ctx.citeOrder.includes(k)) ctx.citeOrder.push(k);
        return ctx.citeOrder.indexOf(k) + 1;
      });
      return '[' + compress(nums) + ']';
    });
}
function compress(nums) {
  const n = [...new Set(nums)].sort((a, b) => a - b);
  const out = []; let i = 0;
  while (i < n.length) {
    let j = i; while (j + 1 < n.length && n[j + 1] === n[j] + 1) j++;
    out.push(j - i >= 2 ? `${n[i]}–${n[j]}` : n.slice(i, j + 1).join(', '));
    i = j + 1;
  }
  return out.join(', ');
}

function runs(text, base = {}, ctx) {
  const s = ctx ? ctx.resolve(text) : text;
  const out = [];
  const re = /(\*\*[^*]+\*\*|\*[^*\s][^*]*\*|`[^`]+`|_\{[^}]*\}|\^\{[^}]*\}|\[\[[^\]]+\]\])/g;
  let last = 0; let m;
  const push = (t, o = {}) => { if (t) out.push(new TextRun({ text: t, font: FONT, ...base, ...o })); };
  while ((m = re.exec(s))) {
    push(s.slice(last, m.index));
    const tok = m[0];
    if (tok.startsWith('**')) {
      // allow nested italics/sub inside bold by recursion on simple text
      push(tok.slice(2, -2), { bold: true, color: base.boldColor || base.color });
    } else if (tok.startsWith('`')) push(tok.slice(1, -1), { font: MONO, size: (base.size || 21) - 2, color: base.color || C.ink });
    else if (tok.startsWith('_{')) push(tok.slice(2, -1), { subScript: true });
    else if (tok.startsWith('^{')) push(tok.slice(2, -1), { superScript: true });
    else if (tok.startsWith('[[')) push(tok.slice(2, -2), { highlight: 'yellow', bold: true, color: '7A4B00' });
    else push(tok.slice(1, -1), { italics: true });
    last = m.index + tok.length;
  }
  push(s.slice(last));
  return out;
}

// ---------- math helpers ----------
const M = {
  r: (t) => new MathRun(t),
  sub: (b, s) => new MathSubScript({ children: arr(b), subScript: arr(s) }),
  sup: (b, s) => new MathSuperScript({ children: arr(b), superScript: arr(s) }),
  subsup: (b, s, p) => new MathSubSuperScript({ children: arr(b), subScript: arr(s), superScript: arr(p) }),
  frac: (n, dd) => new MathFraction({ numerator: arr(n), denominator: arr(dd) }),
  sum: (lo, hi, body) => new MathSum({ children: arr(body), subScript: lo ? arr(lo) : [], superScript: hi ? arr(hi) : [] }),
};
function arr(x) { return (Array.isArray(x) ? x : [x]).map((e) => (typeof e === 'string' ? new MathRun(e) : e)); }

// ---------- images ----------
function pngSize(file) {
  const b = fs.readFileSync(file);
  if (b.readUInt32BE(12) !== 0x49484452) throw new Error('not a png: ' + file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20), data: b };
}

// ---------- borders ----------
const NONE = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
const NO_BORDERS = { top: NONE, bottom: NONE, left: NONE, right: NONE };
const line = (color = C.rule, size = 4) => ({ style: BorderStyle.SINGLE, size, color });

// ---------- block renderers ----------
function para(ctx, text, o = {}) {
  return new Paragraph({
    style: o.style,
    alignment: o.align || AlignmentType.JUSTIFIED,
    spacing: o.spacing,
    keepNext: o.keepNext,
    indent: o.indent,
    children: runs(text, o.run || {}, ctx),
  });
}

function heading(ctx, b) {
  const level = { h1: HeadingLevel.HEADING_1, h2: HeadingLevel.HEADING_2, h3: HeadingLevel.HEADING_3 }[b.t];
  const label = b.num ? `${b.num}  ` : '';
  return new Paragraph({
    heading: level,
    pageBreakBefore: b.t === 'h1' && !!b.pageBreak,
    children: [new TextRun({ text: label + b.text })],
  });
}

function bullets(ctx, b) {
  const ref = b.numbered ? `numbers-${ctx.listId++}` : 'bullets';
  return b.items.map((it) => {
    const [text, level] = Array.isArray(it) ? it : [it, 0];
    return new Paragraph({
      numbering: { reference: ref, level },
      alignment: AlignmentType.LEFT,
      spacing: { after: 60, line: 264 },
      children: runs(text, {}, ctx),
    });
  });
}

function cellParas(ctx, content, o) {
  const items = Array.isArray(content) ? content : [content];
  return items.map((t) => new Paragraph({
    alignment: o.align || AlignmentType.LEFT,
    spacing: { before: 0, after: 0, line: 240 },
    keepNext: o.keepNext,
    children: runs(String(t), { size: o.size, color: o.color, bold: o.bold }, ctx),
  }));
}

function table(ctx, b) {
  const W = b.width || CONTENT_W;
  const fr = b.cols || b.header.map(() => 1);
  const tot = fr.reduce((a, c) => a + c, 0);
  const widths = fr.map((f) => Math.round((f / tot) * W));
  widths[widths.length - 1] += W - widths.reduce((a, c) => a + c, 0);
  const size = b.size || 17; // 8.5pt
  const aligns = b.align || [];
  const al = (i) => ({ l: AlignmentType.LEFT, r: AlignmentType.RIGHT, c: AlignmentType.CENTER })[aligns[i] || 'l'];
  const headerRow = new TableRow({
    tableHeader: true,
    cantSplit: true,
    children: b.header.map((h, i) => new TableCell({
      width: { size: widths[i], type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, fill: C.headFill, color: 'auto' },
      borders: { top: line(C.navy, 8), bottom: line(C.navy, 6), left: NONE, right: NONE },
      margins: { top: 50, bottom: 50, left: 80, right: 80 },
      verticalAlign: VerticalAlign.BOTTOM,
      children: cellParas(ctx, h, { size, bold: true, color: C.navy, align: al(i), keepNext: true }),
    })),
  });
  const n = b.rows.length;
  const bodyRows = b.rows.map((row, ri) => {
    const isLast = ri === n - 1;
    const emph = b.emphRows && b.emphRows.includes(ri);
    return new TableRow({
      cantSplit: true,
      children: row.map((c, i) => new TableCell({
        width: { size: widths[i], type: WidthType.DXA },
        shading: emph ? { type: ShadingType.CLEAR, fill: C.fill, color: 'auto' } : undefined,
        borders: { top: NONE, left: NONE, right: NONE, bottom: isLast ? line(C.navy, 6) : line(C.light, 4) },
        margins: { top: 40, bottom: 40, left: 80, right: 80 },
        verticalAlign: VerticalAlign.TOP,
        children: cellParas(ctx, c, { size, color: C.ink, align: al(i), bold: (b.boldFirstCol && i === 0) || undefined, keepNext: b.keepTogether && !isLast }),
      })),
    });
  });
  const out = [];
  if (b.caption) out.push(caption(ctx, 'Table', b, true));
  out.push(new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: widths,
    layout: TableLayoutType.FIXED,
    borders: { top: NONE, bottom: NONE, left: NONE, right: NONE, insideHorizontal: NONE, insideVertical: NONE },
    rows: [headerRow, ...bodyRows],
  }));
  if (b.note) out.push(new Paragraph({ spacing: { before: 60, after: 160 }, alignment: AlignmentType.LEFT, children: runs(b.note, { size: 16, color: C.muted }, ctx) }));
  else out.push(new Paragraph({ spacing: { before: 0, after: 100 }, children: [] }));
  return out;
}

function caption(ctx, kind, b, above) {
  const num = ctx.labels[`${kind === 'Figure' ? 'fig' : 'tab'}:${b.id}`];
  return new Paragraph({
    style: kind === 'Figure' ? 'FigureCaption' : 'TableCaption',
    keepNext: above,
    keepLines: true,
    children: [
      new TextRun({ text: `${kind} ${num}. `, bold: true, color: C.navy }),
      ...runs(b.caption, {}, ctx),
      ...(b.source ? [new TextRun({ text: '  Source: ', color: C.muted }), ...runs(b.source, { color: C.muted }, ctx)] : []),
    ],
  });
}

function figure(ctx, b) {
  const { w, h, data } = pngSize(b.path);
  const maxWpx = Math.round(((b.widthCm || 16) / 2.54) * 96);
  const maxHpx = Math.round(((b.maxHeightCm || 19) / 2.54) * 96);
  let ww = maxWpx; let hh = Math.round((h / w) * ww);
  if (hh > maxHpx) { hh = maxHpx; ww = Math.round((w / h) * hh); }
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      keepNext: true,
      spacing: { before: 120, after: 60 },
      children: [new ImageRun({ type: 'png', data, transformation: { width: ww, height: hh }, altText: { title: b.alt || b.caption.slice(0, 60), description: b.alt || b.caption, name: path.basename(b.path) } })],
    }),
    caption(ctx, 'Figure', b, false),
  ];
}

function equation(ctx, b) {
  const num = ctx.labels[`eq:${b.id}`];
  const w1 = CONTENT_W - 900;
  return [new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: [w1, 900],
    layout: TableLayoutType.FIXED,
    borders: { top: NONE, bottom: NONE, left: NONE, right: NONE, insideHorizontal: NONE, insideVertical: NONE },
    rows: [new TableRow({
      cantSplit: true,
      children: [
        new TableCell({ width: { size: w1, type: WidthType.DXA }, borders: NO_BORDERS, verticalAlign: VerticalAlign.CENTER, children: [new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60, after: 60 }, children: [new OMath({ children: b.math(M) })] })] }),
        new TableCell({ width: { size: 900, type: WidthType.DXA }, borders: NO_BORDERS, verticalAlign: VerticalAlign.CENTER, children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: `(${num})`, font: FONT, color: C.ink })] })] }),
      ],
    })],
  }), new Paragraph({ spacing: { after: 40 }, children: [] })];
}

function code(ctx, b) {
  const out = [];
  if (b.caption) out.push(caption(ctx, 'Figure', b, true));
  const cell = new TableCell({
    width: { size: CONTENT_W, type: WidthType.DXA },
    shading: { type: ShadingType.CLEAR, fill: C.codeFill, color: 'auto' },
    borders: { top: NONE, bottom: NONE, right: NONE, left: line(C.teal, 18) },
    margins: { top: 100, bottom: 100, left: 180, right: 120 },
    children: b.lines.map((l) => new Paragraph({
      spacing: { before: 0, after: 0, line: 228 },
      keepNext: true,
      children: [new TextRun({ text: l.length ? l : ' ', font: MONO, size: 16, color: C.ink })],
    })),
  });
  out.push(new Table({ width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: [CONTENT_W], layout: TableLayoutType.FIXED, rows: [new TableRow({ children: [cell] })] }));
  out.push(new Paragraph({ spacing: { after: 120 }, children: [] }));
  return out;
}

function callout(ctx, b) {
  const cell = new TableCell({
    width: { size: CONTENT_W, type: WidthType.DXA },
    shading: { type: ShadingType.CLEAR, fill: C.fill, color: 'auto' },
    borders: { top: NONE, bottom: NONE, right: NONE, left: line(C.teal, 24) },
    margins: { top: 110, bottom: 110, left: 200, right: 200 },
    children: [
      ...(b.title ? [new Paragraph({ spacing: { after: 40 }, keepNext: true, children: [new TextRun({ text: b.title, bold: true, color: C.navy, font: FONT, size: 20 })] })] : []),
      ...(Array.isArray(b.text) ? b.text : [b.text]).map((t) => new Paragraph({ spacing: { after: 40, line: 264 }, alignment: AlignmentType.LEFT, children: runs(t, { size: 20 }, ctx) })),
    ],
  });
  return [new Table({ width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: [CONTENT_W], layout: TableLayoutType.FIXED, rows: [new TableRow({ cantSplit: true, children: [cell] })] }), new Paragraph({ spacing: { after: 120 }, children: [] })];
}

// ---------- numbering pass ----------
function assignNumbers(blocks, ctx) {
  let h1 = 0, h2 = 0, h3 = 0, fig = 0, tab = 0, eq = 0;
  let appendix = false, app = 0;
  for (const b of blocks) {
    if (b.t === 'appendixStart') { appendix = true; continue; }
    if (b.t === 'h1') {
      if (b.unnumbered) continue;
      if (appendix) { app++; b.num = `Appendix ${String.fromCharCode(64 + app)}`; h1 = String.fromCharCode(64 + app); }
      else { h1++; b.num = String(h1); }
      h2 = 0; h3 = 0;
      if (b.id) ctx.labels[`sec:${b.id}`] = appendix ? `Appendix ${h1}` : `Section ${h1}`;
    } else if (b.t === 'h2') {
      h2++; h3 = 0; b.num = `${h1}.${h2}`;
      if (b.id) ctx.labels[`sec:${b.id}`] = `Section ${b.num}`;
    } else if (b.t === 'h3') {
      h3++; b.num = `${h1}.${h2}.${h3}`;
      if (b.id) ctx.labels[`sec:${b.id}`] = `Section ${b.num}`;
    } else if (b.t === 'figure' || (b.t === 'code' && b.caption)) {
      fig++; ctx.labels[`fig:${b.id}`] = String(fig);
    } else if (b.t === 'table' && b.caption) {
      tab++; ctx.labels[`tab:${b.id}`] = String(tab);
    } else if (b.t === 'eq') {
      eq++; ctx.labels[`eq:${b.id}`] = String(eq);
    }
  }
}

function render(blocks, ctx) {
  const out = [];
  for (const b of blocks) {
    switch (b.t) {
      case 'h1': case 'h2': case 'h3': out.push(heading(ctx, b)); break;
      case 'p': out.push(para(ctx, b.text, b)); break;
      case 'bullets': out.push(...bullets(ctx, b)); break;
      case 'table': out.push(...table(ctx, b)); break;
      case 'figure': out.push(...figure(ctx, b)); break;
      case 'eq': out.push(...equation(ctx, b)); break;
      case 'code': out.push(...code(ctx, b)); break;
      case 'callout': out.push(...callout(ctx, b)); break;
      case 'pagebreak': out.push(new Paragraph({ children: [new PageBreak()] })); break;
      case 'raw': out.push(...b.items); break;
      case 'appendixStart': break;
      default: throw new Error('unknown block ' + b.t);
    }
  }
  return out;
}

module.exports = { C, FONT, FONT_LIGHT, MONO, CONTENT_W, PAGE_W, MARGIN_LR, runs, makeResolver, assignNumbers, render, M, NONE, NO_BORDERS, line, pngSize };
