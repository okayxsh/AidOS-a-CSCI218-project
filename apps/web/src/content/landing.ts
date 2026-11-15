/**
 * Landing-page copy that describes the build status of each capability.
 * Status must stay truthful: update it when a stage actually lands.
 */

export type BuildStatus = 'built' | 'partial' | 'planned';

export const STATUS_LABEL: Record<BuildStatus, string> = {
  built: 'Built',
  partial: 'Partly built',
  planned: 'Planned',
};

export interface WorkflowStep {
  title: string;
  technique: string;
  body: string;
  status: BuildStatus;
  statusNote: string;
}

export const WORKFLOW: WorkflowStep[] = [
  {
    title: 'Define an emergency scenario',
    technique: 'Validated JSON schema',
    body: 'Load a synthetic scenario: one depot, its stock, and crisis zones with their requests and ratings.',
    status: 'built',
    statusNote: 'Stage 1',
  },
  {
    title: 'Assess urgency',
    technique: 'Fuzzy logic',
    body: 'Severity, vulnerability and time-criticality become a 0–100 urgency score with a readable rule trace.',
    status: 'built',
    statusNote: 'Stage 2 · 27 Sugeno rules',
  },
  {
    title: 'Allocate under constraints',
    technique: 'Constraint satisfaction',
    body: 'Whole units only, never more than requested, never more than the depot holds.',
    status: 'built',
    statusNote: 'Stage 2 · CP-SAT, checked by an independent validator',
  },
  {
    title: 'Examine the explanation',
    technique: 'Decision traces',
    body: 'Every cell states what was requested, what was allocated, and which limit stopped it.',
    status: 'built',
    statusNote: 'Stage 2 · rule traces and allocation reasons',
  },
  {
    title: 'Respond to change',
    technique: 'Finite state machine',
    body: 'A new zone, an escalation or a stock change creates a new snapshot. Urgency and the plan are recomputed, and the engine explains what changed.',
    status: 'built',
    statusNote: 'Stage 3 · events, replay, dispatch ledger',
  },
];
