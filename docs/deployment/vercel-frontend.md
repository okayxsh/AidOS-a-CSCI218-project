# Deploying the frontend to Vercel

Live site: <https://aid-os-a-csci-218-project.vercel.app/>

Only `apps/web` (the React/Vite dashboard) is deployed to Vercel. The FastAPI engine is not part of this deployment; it will be hosted separately (Render) and connected later through a Vercel rewrite. Until then, every engine-backed page shows the "engine not running" state. No numbers are invented.

## How the frontend finds the engine

`apps/web/src/api/client.ts` decides the engine address once:

| Situation | Engine base | Requests go to |
|---|---|---|
| `npm run dev` with no `VITE_API_BASE_URL` | `http://localhost:8000` | `http://localhost:8000/api/...` |
| Production build with no `VITE_API_BASE_URL` | same origin | `/api/...` on the deployed site |
| `VITE_API_BASE_URL` set (any mode) | that URL | `<VITE_API_BASE_URL>/api/...` |

A trailing `/` or `/api` on `VITE_API_BASE_URL` is removed, so paths never become `/api/api/...`. The `localhost` default is compiled out of production bundles.

If no engine answers, the dashboard shows "The AidOS engine is not running" with a Retry button. This covers no network reply, a timeout, a non-JSON 404/502/503/504 page from the host, and an HTML page served instead of JSON. Errors that the engine itself sends (JSON envelopes) are still shown as engine errors.

## `apps/web/vercel.json`

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "framework": "vite",
  "installCommand": "npm ci",
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "rewrites": [{ "source": "/:path((?!api/).*)", "destination": "/index.html" }]
}
```

Static files are served before rewrites, so `/assets/*` and `/favicon.svg` load directly. Every other path except `/api/*` returns `index.html`, so React Router deep links and refreshes work (`/dashboard/allocate?...`). `/api/*` is excluded, so a missing backend returns a real 404 rather than the app shell.

## Vercel project settings

| Setting | Value |
|---|---|
| Framework preset | Vite |
| Root directory | `apps/web` |
| Include files outside the root directory in the Build Step | **Enabled** (the default). The build imports `data/scenarios/*.json`, `data/simulations/*.json` and `apps/api/aidos/config/fuzzy_rules.json`. |
| Install command | `npm ci` (set in `vercel.json`) |
| Build command | `npm run build` (set in `vercel.json`; runs `tsc --noEmit && vite build`) |
| Output directory | `dist` (set in `vercel.json`) |
| Node.js version | 22.x or later (Vite 8 needs Node 20.19+ or 22.12+) |
| Environment variables | None for now. Do **not** set `VITE_API_BASE_URL` to a localhost address. |

## Connecting the engine later

When the Render backend exists, add a rewrite **before** the SPA fallback, replacing the placeholder with the real host:

```json
{ "source": "/api/:path*", "destination": "https://<render-host>/api/:path*" }
```

The browser keeps calling `/api/...` on the Vercel domain, so no CORS change and no frontend rebuild with a new variable are needed. Alternatively, set `VITE_API_BASE_URL` to the Render URL and redeploy; the engine's `AIDOS_CORS_ORIGINS` must then include the Vercel domain.

The engine keeps simulation sessions in memory, so it must run as a single instance with a single worker (see `docs/simulation/`). That is a constraint for the Render setup, not for this frontend deployment.
