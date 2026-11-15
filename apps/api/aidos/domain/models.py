"""Canonical domain model (spec Section 4).

Models are immutable Pydantic models so that a loaded scenario can be shared between
policies without any of them mutating it. Pydantic is used for schema validation only;
nothing here depends on FastAPI.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

# Payload limits that reject pathological inputs with a clear message.
MAX_ZONES = 50
MAX_RESOURCES = 10
MAX_UNITS = 1_000_000

Identifier = Annotated[
    str,
    StringConstraints(min_length=1, max_length=64, pattern=r"^[a-z0-9][a-z0-9_-]*$"),
]
Units = Annotated[int, Field(ge=0, le=MAX_UNITS, strict=True)]
Rating = Annotated[float, Field(ge=0, le=10)]


class Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class ResourceType(Frozen):
    """One kind of physical relief unit. Resources never substitute for each other."""

    id: Identifier
    label: str = Field(min_length=1, max_length=80)
    unit: str = Field(min_length=1, max_length=40, description="Plural unit name, e.g. 'kits'.")


class CrisisZone(Frozen):
    """A zone requesting supplies. Ratings are simulated inputs, not triage grades."""

    id: Identifier
    name: str = Field(min_length=1, max_length=80)
    arrival_order: int = Field(ge=1, le=10_000, strict=True)
    severity: Rating
    vulnerability: Rating
    time_criticality: Rating
    activation_step: int = Field(default=0, ge=0, strict=True)
    population: int | None = Field(
        default=None, ge=0, le=100_000_000, description="Simulated population (synthetic)."
    )
    demand: dict[Identifier, Units]


class Scenario(Frozen):
    """A validated, synthetic scenario snapshot."""

    schema_version: Literal["1.0"]
    scenario_id: Identifier
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=1000)
    seed: int = Field(strict=True)
    synthetic: Literal[True]
    step: int = Field(default=0, ge=0, strict=True)
    resources: tuple[ResourceType, ...] = Field(min_length=1, max_length=MAX_RESOURCES)
    stock: dict[Identifier, Units]
    zones: tuple[CrisisZone, ...] = Field(min_length=1, max_length=MAX_ZONES)

    def resource_ids(self) -> tuple[str, ...]:
        """Canonical resource order: the order of the resource catalogue."""
        return tuple(r.id for r in self.resources)

    def active_zones(self) -> tuple[CrisisZone, ...]:
        """Zones whose activation step has been reached."""
        return tuple(z for z in self.zones if z.activation_step <= self.step)

    def demand_of(self, zone: CrisisZone, resource_id: str) -> int:
        return zone.demand.get(resource_id, 0)
