# 0008. Local GUI on the stdlib HTTP server, with each job run as a CLI subprocess

## Status
Accepted, retrospective, inferred 2026-11-12

## Context
A browser UI makes it easier to try voices, presets and parameters.

## Decision
`gui/server.py` uses `http.server.ThreadingHTTPServer` with a `SimpleHTTPRequestHandler` subclass. There is no web framework, and the frontend is plain HTML/JS/CSS. It binds to `127.0.0.1:8795` by default (overridable through `SUPERTONIC_GUI_HOST`/`PORT`). Endpoints: `GET /api/state`, `/api/templates`, `/api/recent` (latest 24 sidecars in `output/gui`), `/api/surprise`, `/api/job/<id>`, `/audio/<file>` and `POST /api/generate`. Each generate request is validated (text required, lang/voice from YAML, numeric bounds), stored in an in-memory job dict, and run on a daemon thread that spawns `scripts/supertonic_mlx.py generate` with the repo `.venv` Python, keeping the last 800 log lines. The browser polls the job every 1.2 s and escapes HTML in rendered strings.

## Consequences
Positive:
- No extra dependencies, the GUI and CLI share one code path, and a crash in a job doesn't take down the server.

Negative:
- The model reloads for every job.
- Jobs aren't queued: several can run at once, and `active_job_id` tracks only the latest (A-003).
- Job history is lost when the server restarts.
- The static route joins the raw path onto `gui/static` without rejecting `..`; the localhost-only default limits exposure (A-004).

## Alternatives considered
Not recorded (A-002 covers why subprocesses were used instead of an in-process model).

## Evidence
- gui/server.py
- gui/static/index.html, gui/static/app.js, gui/static/styles.css
- gui.sh
