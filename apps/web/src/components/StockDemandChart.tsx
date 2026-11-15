import {
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { ScenarioDetail } from '../api/types';
import { formatInt, resourceById } from '../lib/format';
import { useReducedMotion } from '../lib/useMediaQuery';
import { Panel } from './ui/Panel';

const COLOURS = { requested: '#556578', stock: '#43c9c1' };
const CHART_HEIGHT = 290;

interface Row {
  label: string;
  requested: number;
  stock: number;
}

function ChartTooltip({ active, payload }: { active?: boolean; payload?: { payload: Row }[] }) {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload;
  const gap = row.requested - row.stock;
  return (
    <div className="chart-tooltip">
      <p className="chart-tooltip__title">{row.label}</p>
      <p>
        <i style={{ background: COLOURS.requested }} /> Requested{' '}
        <b className="num">{formatInt(row.requested)}</b>
      </p>
      <p>
        <i style={{ background: COLOURS.stock }} /> In stock{' '}
        <b className="num">{formatInt(row.stock)}</b>
      </p>
      <p className={gap > 0 ? 'is-short' : 'is-ok'}>
        {gap > 0 ? `${formatInt(gap)} short` : 'Covered by stock'}
      </p>
    </div>
  );
}

interface TickProps {
  x?: number | string;
  y?: number | string;
  width?: number | string;
  visibleTicksCount?: number;
  payload?: { value: string };
}

/**
 * Every resource keeps its label: Recharts would otherwise drop overlapping ticks on
 * narrow screens. Labels wrap onto two lines when one line would not fit its bar group.
 */
function ResourceTick({ x = 0, y = 0, width = 0, visibleTicksCount = 1, payload }: TickProps) {
  const label = payload?.value ?? '';
  const band = Number(width) / Math.max(visibleTicksCount, 1);
  const lines = label.length * 7.4 > band - 8 ? label.split(' ') : [label];
  return (
    <text x={Number(x)} y={Number(y)} textAnchor="middle" fill="#a2b0c0" fontSize={13}>
      {lines.map((line, i) => (
        <tspan key={`${i}-${line}`} x={Number(x)} dy={i === 0 ? 14 : 15}>
          {line}
        </tspan>
      ))}
    </text>
  );
}

/** Grouped bars per resource. The inventory table beside it carries the same numbers as text. */
export function StockDemandChart({ detail }: { detail: ScenarioDetail }) {
  const reduced = useReducedMotion();
  const resources = resourceById(detail.scenario);
  const rows: Row[] = detail.summary.resources.map((r) => ({
    label: resources.get(r.resource_id)?.label ?? r.resource_id,
    requested: r.requested,
    stock: r.stock,
  }));

  return (
    <Panel
      title="Stock against requests"
      description="Units per resource. Resources never substitute for one another."
      actions={
        <ul className="chart-legend" aria-hidden="true">
          <li>
            <i style={{ background: COLOURS.requested }} /> Requested
          </li>
          <li>
            <i style={{ background: COLOURS.stock }} /> In stock
          </li>
        </ul>
      }
    >
      <div className="chart-frame" aria-hidden="true">
        {/* A fixed pixel height leaves only the width to measure, so the chart cannot
            collapse if the container is measured before layout settles. */}
        <ResponsiveContainer width="100%" height={CHART_HEIGHT} minWidth={0} debounce={50}>
          <BarChart
            data={rows}
            margin={{ top: 24, right: 8, bottom: 0, left: -12 }}
            barGap={4}
            barCategoryGap="26%"
          >
            <CartesianGrid vertical={false} stroke="#1d2631" />
            <XAxis
              dataKey="label"
              interval={0}
              height={40}
              tickLine={false}
              axisLine={{ stroke: '#2a3542' }}
              tick={<ResourceTick />}
            />
            <YAxis
              tickLine={false}
              axisLine={false}
              tick={{ fill: '#7d8a9b', fontSize: 12 }}
              width={52}
            />
            <Tooltip cursor={{ fill: 'rgba(255,255,255,0.04)' }} content={<ChartTooltip />} />
            <Bar
              dataKey="requested"
              name="Requested"
              fill={COLOURS.requested}
              radius={[5, 5, 0, 0]}
              maxBarSize={56}
              isAnimationActive={!reduced}
              animationDuration={480}
              animationEasing="ease-out"
            >
              <LabelList dataKey="requested" position="top" fill="#a2b0c0" fontSize={12} />
            </Bar>
            <Bar
              dataKey="stock"
              name="In stock"
              fill={COLOURS.stock}
              radius={[5, 5, 0, 0]}
              maxBarSize={56}
              isAnimationActive={!reduced}
              animationBegin={90}
              animationDuration={480}
              animationEasing="ease-out"
            >
              <LabelList dataKey="stock" position="top" fill="#8ee3dc" fontSize={12} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="visually-hidden">
        {rows.map((r) => `${r.label}: ${r.requested} requested, ${r.stock} in stock.`).join(' ')}
      </p>
    </Panel>
  );
}
