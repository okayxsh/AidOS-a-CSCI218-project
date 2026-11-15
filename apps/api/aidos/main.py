"""FastAPI application. Adapts HTTP to the engine; contains no domain logic.

Run from apps/api/:  uv run uvicorn aidos.main:app --reload --port 8000
"""

from __future__ import annotations

import os

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from aidos import ENGINE_STAGE, __version__
from aidos.ai.constraints import AllocationConfigError
from aidos.ai.fuzzy import FuzzyInputError
from aidos.api.routes_allocation import POLICY_CATALOGUE
from aidos.api.routes_allocation import router as allocation_router
from aidos.api.routes_evaluation import router as evaluation_router
from aidos.api.routes_scenarios import router as scenario_router
from aidos.api.routes_simulation import router as simulation_router
from aidos.api.routes_urgency import router as urgency_router
from aidos.api.schemas import ErrorBody, ErrorDetail, ErrorResponse, HealthResponse
from aidos.domain.snapshots import ScenarioNotFoundError
from aidos.domain.validation import ScenarioValidationError
from aidos.evaluation.artifacts import RESULTS_ROOT, InvalidRunIdError, RunNotFoundError
from aidos.simulation.fsm import InvalidTransitionError
from aidos.simulation.reducer import EventRejectedError
from aidos.simulation.session import InvariantBreachError, ReplayError, SolverFailedError
from aidos.simulation.store import SessionNotFoundError, SessionStore, VersionConflictError

DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173"
)


def _error(status: int, code: str, message: str, details: list[ErrorDetail] | None = None):
    body = ErrorResponse(error=ErrorBody(code=code, message=message, details=details or []))
    return JSONResponse(status_code=status, content=body.model_dump())


def create_app() -> FastAPI:
    app = FastAPI(
        title="AidOS API",
        version=__version__,
        description="CSCI218 academic prototype. Synthetic scenarios only.",
    )

    origins = [o.strip() for o in os.getenv("AIDOS_CORS_ORIGINS", DEFAULT_CORS_ORIGINS).split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o for o in origins if o],
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @app.exception_handler(RequestValidationError)
    async def _request_invalid(_: Request, exc: RequestValidationError):
        details = [
            ErrorDetail(path=".".join(str(p) for p in err["loc"]), message=err["msg"])
            for err in exc.errors()
        ]
        return _error(422, "validation_error", "The request is invalid.", details)

    @app.exception_handler(ScenarioValidationError)
    async def _scenario_invalid(_: Request, exc: ScenarioValidationError):
        details = [ErrorDetail(path=i.path, message=i.message) for i in exc.issues]
        return _error(422, "invalid_scenario", "The scenario failed validation.", details)

    @app.exception_handler(ScenarioNotFoundError)
    async def _not_found(_: Request, exc: ScenarioNotFoundError):
        return _error(404, "scenario_not_found", str(exc))

    @app.exception_handler(AllocationConfigError)
    async def _config_invalid(_: Request, exc: AllocationConfigError):
        return _error(422, "invalid_config", str(exc))

    @app.exception_handler(HTTPException)
    async def _http(_: Request, exc: HTTPException):
        codes = {404: "not_found", 405: "method_not_allowed", 422: "validation_error"}
        return _error(exc.status_code, codes.get(exc.status_code, "http_error"), str(exc.detail))

    @app.exception_handler(InvalidRunIdError)
    async def _bad_run(_: Request, exc: InvalidRunIdError):
        return _error(422, "invalid_run_id", str(exc))

    @app.exception_handler(RunNotFoundError)
    async def _no_run(_: Request, exc: RunNotFoundError):
        return _error(404, "run_not_found", str(exc))

    @app.exception_handler(SessionNotFoundError)
    async def _no_session(_: Request, exc: SessionNotFoundError):
        return _error(404, "session_not_found", str(exc))

    @app.exception_handler(VersionConflictError)
    async def _conflict(_: Request, exc: VersionConflictError):
        detail = ErrorDetail(path="expected_version", message=f"current version is {exc.current}")
        return _error(409, "version_conflict", str(exc), [detail])

    @app.exception_handler(InvalidTransitionError)
    async def _transition(_: Request, exc: InvalidTransitionError):
        return _error(409, "invalid_transition", str(exc))

    @app.exception_handler(EventRejectedError)
    async def _event_rejected(_: Request, exc: EventRejectedError):
        details = [ErrorDetail(**d) for d in exc.details]
        return _error(409 if exc.code == "stale_plan" else 422, exc.code, str(exc), details)

    @app.exception_handler(ReplayError)
    async def _replay(_: Request, exc: ReplayError):
        path = "document" if exc.index < 0 else f"events.{exc.index}"
        detail = ErrorDetail(path=path, message=str(exc.cause))
        return _error(422, "replay_failed", str(exc), [detail])

    @app.exception_handler(SolverFailedError)
    async def _solver(_: Request, exc: SolverFailedError):
        return _error(503, "solver_failed", str(exc))

    @app.exception_handler(InvariantBreachError)
    async def _breach(_: Request, exc: InvariantBreachError):
        return _error(
            500, "engine_invariant", f"Engine invariant failed; session is in ERROR: {exc}"
        )

    @app.exception_handler(FuzzyInputError)
    async def _ratings_invalid(_: Request, exc: FuzzyInputError):
        return _error(422, "invalid_ratings", str(exc))

    @app.get("/api/health", response_model=HealthResponse, tags=["meta"])
    def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            version=__version__,
            engine_stage=ENGINE_STAGE,
            policies=list(POLICY_CATALOGUE),
        )

    app.include_router(scenario_router)
    app.include_router(urgency_router)
    app.include_router(allocation_router)
    app.include_router(simulation_router)
    app.include_router(evaluation_router)
    app.state.results_root = RESULTS_ROOT  # precomputed evaluation runs (read-only)
    # In-memory, single-process session store (docs/simulation/state-machine.md).
    app.state.sessions = SessionStore()
    return app


app = create_app()
