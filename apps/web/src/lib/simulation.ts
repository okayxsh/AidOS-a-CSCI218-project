import type { PolicyId, SimEventType, SimState } from '../api/types';
import type { BadgeTone } from '../components/ui/StatusBadge';

/** How each engine event type is named in the dashboard. */
export const EVENT_LABEL: Record<SimEventType, string> = {
  urgency_changed: 'Escalate or ease urgency',
  zone_added: 'New emergency zone',
  supply_arrived: 'Supply shipment arrives',
  supply_lost: 'Supply lost or disrupted',
  request_updated: "Change a zone's request",
  zone_resolved: 'Emergency resolved',
  time_advanced: 'Advance the clock',
  plan_committed: 'Dispatch the recommended plan',
};

export const EVENT_ORDER: SimEventType[] = [
  'urgency_changed',
  'zone_added',
  'supply_arrived',
  'supply_lost',
  'request_updated',
  'zone_resolved',
  'time_advanced',
  'plan_committed',
];

export const STATE_INFO: Record<SimState, { tone: BadgeTone; meaning: string }> = {
  READY: { tone: 'neutral', meaning: 'Loaded and scored. Start the session to apply events.' },
  ACTIVE: { tone: 'ok', meaning: 'Accepting events.' },
  PAUSED: { tone: 'warn', meaning: 'Frozen: events are refused until you resume.' },
  COMPLETED: { tone: 'built', meaning: 'Run ended. Read-only until reset.' },
  ERROR: { tone: 'critical', meaning: 'An engine check failed. Read-only until reset.' },
};

export const POLICY_NAME: Record<PolicyId, string> = {
  fcfs: 'FCFS',
  greedy: 'Urgency greedy',
  aidos: 'AidOS',
  aidos_balanced: 'AidOS balanced',
};

export const fmtScore = (value: number | null): string => (value === null ? '—' : value.toFixed(1));
