# Deployment: Vercel frontend and Render engine

| Part | Host | URL |
|---|---|---|
| Frontend (React/Vite, `apps/web`) | Vercel | <https://aid-os-a-csci-218-project.vercel.app/> |
| Engine (FastAPI, `apps/api`) | Render | <https://aidos-a-csci218-project.onrender.com> |

The deployment is a teaching demonstration of a synthetic-data prototype, not a production service.

## Architecture

```
browser ──> Vercel (aid-os-a-csci-218-project.vercel.app)
              ├─ static files (/assets/*, /favicon.svg)       served directly
              ├─ /api/*  ── rewrite ──> Render (aidos-a-csci218-project.onrender.com/api/*)
              └─ every other path ──> /index.html (React Router handles the route)
```

The browser only ever talks to the Vercel domain. Vercel forwards `/api/*` to the Render engine and returns the engine's reply unchanged. So the frontend needs no engine URL and no CORS setting. Every number on the dashboard is still computed by the engine; the frontend implements no allocation or scoring.

## How the frontend finds the engine

`apps/web/src/api/client.ts` decides the engine address once:

| Situation | Engine base | Requests go to |
|---|---|---|
| `npm run dev` with no `VITE_API_BASE_URL` | `http://localhost:8000` | `http://localhost:8000/api/...` |
| Production build with no `VITE_API_BASE_URL` (the Vercel deployment) | same origin | `/api/...` on the Vercel domain, proxied to Render |
| `VITE_API_BASE_URL` set (any mode) | that URL | `<VITE_API_BASE_URL>/api/...` |

`VITE_API_BASE_URL` is **not** set on Vercel. A trailing `/` or `/api` on it is removed, so paths never become `/api/api/...`. The `localhost` default is compiled out of production bundles.

If no engine answers, the dashboard shows "The AidOS engine is not running" with a Retry button. That covers no network reply, a timeout after 60 s, a non-JSON 404/502/503/504 page from a host, or an HTML page where JSON was expected. Errors the engine itself sends (JSON envelopes) are shown as engine errors.

## `apps/web/vercel.json`

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "framework": "vite",
  "installCommand": "npm ci",
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://aidos-a-csci218-project.onrender.com/api/:path*"
    },
    { "source": "/:path((?!api/).*)", "destination": "/index.html" }
  ]
}
```

Static files are served before rewrites. The `/api/*` proxy comes first. Every other path returns `index.html`, so deep links and refreshes such as `/dashboard/allocate?scenario=...` work.

## Vercel project settings

| Setting | Value |
|---|---|
| Framework preset | Vite |
| Root directory | `apps/web` |
| Include files outside the root directory in the Build Step | **Enabled** (the default). The build imports `data/scenarios/*.json`, `data/simulations/*.json` and `apps/api/aidos/config/fuzzy_rules.json`. |
| Install, build, output | `npm ci`, `npm run build` (`tsc --noEmit && vite build`), `dist`, all set in `vercel.json` |
| Node.js version | 22.x or later (Vite 8 needs Node 20.19+ or 22.12+) |
| Environment variables | None. Do not set `VITE_API_BASE_URL`. |

Pushes to `main` redeploy the frontend automatically.

## Render engine: constraints

**One instance, one Uvicorn worker.** Simulation sessions live in the engine's process memory (`apps/api/aidos/simulation/store.py`). With more than one worker or instance, a request can reach a process that never saw the session, and the dashboard then reports it as expired. So:
- do not pass `--workers`;
- do not set `WEB_CONCURRENCY` above 1;
- do not scale the service beyond one instance.

A start command of this form keeps the single-worker default:

```bash
uv run uvicorn aidos.main:app --host 0.0.0.0 --port $PORT
```

**Sessions are lost on restart.** A redeploy, restart or spin-down ends every open simulation session. Allocations, scenarios and evaluation results are unaffected: they are recomputed or read from the repository on each request. To keep a session, export it from the Simulate page and import it again later; the import replays and verifies it.

**Free-tier cold starts.** Render's documentation says a free web service spins down after 15 minutes without inbound traffic, and that waking it takes about a minute. The first dashboard request after a quiet period can therefore be slow:
- the dashboard waits up to 60 s, then shows the "engine not running" panel;
- pressing Retry, or waiting for the header's 20-second engine check, succeeds once the service is up;
- an open dashboard tab keeps the service awake, because it checks the engine every 20 seconds.

Before a demo, open <https://aidos-a-csci218-project.onrender.com/api/health> a minute or two in advance to wake the engine.

**Repository files.** The engine reads `data/scenarios/` and `experiments/results/` from the repository checkout, so the Render service must deploy from the full repository.

## Verifying the deployment

**From a terminal.** Each of these must return JSON from the engine, not an HTML page:

```bash
curl https://aid-os-a-csci-218-project.vercel.app/api/health               # {"status":"ok","version":"0.4.0","engine_stage":4,...}
curl https://aid-os-a-csci-218-project.vercel.app/api/scenarios            # 9 synthetic scenarios
curl https://aid-os-a-csci-218-project.vercel.app/api/evaluation/runs      # the Stage 4 runs
curl https://aid-os-a-csci-218-project.vercel.app/api/scenarios/triage-demo-001
```

The same paths on the Render URL should return identical bodies.

**In the browser** (<https://aid-os-a-csci-218-project.vercel.app/dashboard>):

1. **Engine status:** the bottom of the sidebar shows "Engine online · v0.4.0 · stage 4".
2. **Scenario loading:** Overview and Emergency scenarios show `triage-demo-001` and the scenario picker lists the fixtures.
3. **Allocation:** on Allocation results, press Run allocation. The allocation table fills, and the policy selector lists FCFS, urgency greedy, AidOS and AidOS balanced.
4. **Simulation:**
   - On Simulation, press Load into simulator, then Start.
   - Apply an escalation, for example Zone B severity 6 → 9.
   - The panel should show Zone B urgency 62.5 → 79.2 (high → critical) and the plan changes.
   - The URL gains `?session=...`.
5. **Evaluation:** Evaluation shows the frozen run: 504 static scenarios, 2,016 policy runs, 60 event scripts, 240 dispatch trajectories.
6. **Deep links:** refresh any `/dashboard/...` page; it reloads the same page instead of a 404.

## What the version label means

The dashboard's "v0.4.0 · stage 4" label comes from the engine's `/api/health`. It is the **engine's** version: the last stage that changed engine behaviour. It is not the project's overall status. Later stages added experiments, documentation, the report, hardening fixes and this deployment, but no engine features, so the engine version stayed at 0.4.0.
