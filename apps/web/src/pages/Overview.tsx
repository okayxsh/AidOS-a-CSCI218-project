import { AllocationPreview } from '../components/AllocationPreview';
import { InventoryPanel } from '../components/InventoryPanel';
import { ScenarioGate, ScenarioHeader } from '../components/ScenarioGate';
import { StockDemandChart } from '../components/StockDemandChart';
import { Metric } from '../components/ui/Metric';
import { ZoneTable } from '../components/ZoneTable';
import type { ScenarioDetail } from '../api/types';
import { SUPPLY_STATUS } from '../lib/display';
import { formatInt } from '../lib/format';
import { useDashboard } from '../state/dashboard';

/** Keeps "step 0" on one line in narrow metric tiles. */
const NBSP = String.fromCharCode(160);

function Summary({ detail }: { detail: ScenarioDetail }) {
  const { totals, resources } = detail.summary;
  const shortResources = resources.filter((r) => r.shortfall > 0).length;
  const status = SUPPLY_STATUS[detail.summary.supply_status];
  // Cross-check order: who is asking, what we hold, what is asked, the gap, then the verdict.
  // Every value, including the status, comes from the backend summary.
  return (
    <dl className="metrics" aria-label="Scenario summary">
      <Metric
        label="Active zones"
        value={totals.active_zones}
        detail={
          totals.zones === totals.active_zones ? 'All zones active' : `${totals.zones} in scenario`
        }
      />
      <Metric
        label="Units in stock"
        value={formatInt(totals.stock)}
        detail={`${resources.length} resource types`}
      />
      <Metric
        label="Units requested"
        value={formatInt(totals.requested)}
        detail="By active zones"
      />
      <Metric
        label="Shortfall"
        value={totals.shortfall > 0 ? formatInt(totals.shortfall) : 'None'}
        tone={totals.shortfall > 0 ? 'warn' : 'ok'}
        detail={
          totals.shortfall > 0
            ? `${shortResources} of ${resources.length} resources short`
            : 'No resource is short'
        }
      />
      <Metric
        label="Supply status"
        value={status.label}
        tone={status.tone}
        detail={`${status.detail} · step${NBSP}${detail.scenario.step}`}
      />
    </dl>
  );
}

export default function Overview() {
  const { detail } = useDashboard();
  return (
    <ScenarioGate detail={detail}>
      {(d) => (
        <div className="page" key={d.snapshot_hash}>
          <ScenarioHeader detail={d} />
          <Summary detail={d} />
          <div className="grid-2">
            <StockDemandChart detail={d} />
            <InventoryPanel detail={d} />
          </div>
          <ZoneTable detail={d} />
          <AllocationPreview detail={d} />
        </div>
      )}
    </ScenarioGate>
  );
}
