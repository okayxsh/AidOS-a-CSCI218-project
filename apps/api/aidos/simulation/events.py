"""Crisis event schema (docs/simulation/events.md).

Each event is a validated, immutable request to change the scenario. Field-level checks
(types, ranges, unknown fields) happen here; checks that need the current scenario (does
the zone exist, would stock go negative, is it a no-op) happen in reducer.py.

Values are absolute where that avoids ambiguity: `urgency_changed` sets new ratings and
`request_updated` sets the new requested quantity. Stock events carry a positive quantity
and a direction given by the type, so a loss can never be expressed as a negative arrival.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from aidos.ai.policies import PolicyId
from aidos.domain.models import MAX_UNITS, Identifier, Rating, Units

Quantity = Annotated[int, Field(ge=1, le=MAX_UNITS, strict=True)]
SnapshotHash = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]


class _Event(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class NewZone(_Event):
    """A zone reporting during the simulation. It arrives after every existing zone."""

    id: Identifier
    name: str = Field(min_length=1, max_length=80)
    severity: Rating
    vulnerability: Rating
    time_criticality: Rating
    population: int | None = Field(default=None, ge=0, le=100_000_000)
    demand: dict[Identifier, Units]


class ZoneAdded(_Event):
    type: Literal["zone_added"] = "zone_added"
    zone: NewZone


class UrgencyChanged(_Event):
    """New values for one or more of a zone's ratings (e.g. severity escalates)."""

    type: Literal["urgency_changed"] = "urgency_changed"
    zone_id: Identifier
    severity: Rating | None = None
    vulnerability: Rating | None = None
    time_criticality: Rating | None = None

    @model_validator(mode="after")
    def _some_rating(self) -> UrgencyChanged:
        if self.severity is None and self.vulnerability is None and self.time_criticality is None:
            raise ValueError("give at least one of severity, vulnerability, time_criticality")
        return self


class SupplyArrived(_Event):
    type: Literal["supply_arrived"] = "supply_arrived"
    resource_id: Identifier
    quantity: Quantity


class SupplyLost(_Event):
    type: Literal["supply_lost"] = "supply_lost"
    resource_id: Identifier
    quantity: Quantity


class RequestUpdated(_Event):
    """A zone's new total request for one resource (0 withdraws the request)."""

    type: Literal["request_updated"] = "request_updated"
    zone_id: Identifier
    resource_id: Identifier
    quantity: Units


class ZoneResolved(_Event):
    """The emergency in a zone is over: it leaves the allocation problem."""

    type: Literal["zone_resolved"] = "zone_resolved"
    zone_id: Identifier


class TimeAdvanced(_Event):
    """The simulation clock moves one step; zones scheduled for that step become active."""

    type: Literal["time_advanced"] = "time_advanced"


class PlanCommitted(_Event):
    """Dispatch the current recommendation of `policy`: its units leave the depot.

    `expected_snapshot_hash` must equal the current snapshot, so a plan computed for an
    older state (or a repeated commit) is rejected instead of consuming stock twice.
    """

    type: Literal["plan_committed"] = "plan_committed"
    policy: PolicyId = PolicyId.AIDOS
    expected_snapshot_hash: SnapshotHash


Event = Annotated[
    ZoneAdded
    | UrgencyChanged
    | SupplyArrived
    | SupplyLost
    | RequestUpdated
    | ZoneResolved
    | TimeAdvanced
    | PlanCommitted,
    Field(discriminator="type"),
]

EVENT_TYPES = (
    "zone_added",
    "urgency_changed",
    "supply_arrived",
    "supply_lost",
    "request_updated",
    "zone_resolved",
    "time_advanced",
    "plan_committed",
)
