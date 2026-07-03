# Stream Health Monitor

A real-time health monitor for web endpoints. It concurrently checks a set of live services, measures their latency, status code and response body, evaluates configurable health rules, and exposes the current state through a Flask API and a lightweight dashboard.

**Live demo:** https://stream-health-monitor.onrender.com

![status](https://img.shields.io/badge/mypy-strict-blue) ![tests](https://img.shields.io/badge/tests-pytest-green)

---

## What it does

Each endpoint is checked on a fixed interval and classified into one of three states:

- **healthy** — responds fast, with the expected status code and valid content
- **degraded** — responds correctly but slower than its latency budget
- **down** — wrong status code, invalid content, or no response at all (timeout / refused)

The measurements come from **real, public endpoints** (GitHub API, Open-Meteo, JSONPlaceholder), not simulated data. The dashboard reads the latest computed state and renders it as a set of live "vital sign" cards.

## Why I built it

This is a **fundamentals project**, not a tutorial follow-along. I wanted to practice several Python concepts in a single, real, working system where each one is *forced by the design* rather than bolted on:

| Concept | Where it lives in the code |
|---|---|
| **async + httpx** | `client.py` — `fetch_all` checks N endpoints in parallel with a shared client and `asyncio.gather` |
| **Generators** | `client.py` — `monitor_stream` yields one fresh batch per cycle, forever, without accumulating state in memory |
| **OOP / inheritance** | `models.py` — abstract `HealthRule` base with `LatencyRule`, `StatusCode`, `ContentRule` subclasses; endpoints compose their own rule list |
| **Custom decorator** | `client.py` — hand-written `@retry` with exponential backoff for flaky requests (no external library) |
| **Strict typing** | whole codebase passes `mypy --strict`, including a generic decorator (`ParamSpec` / `TypeVar`) and `Literal` states |
| **Flask** | `app.py` — a `/status` endpoint serves the last computed state as JSON; Flask only serves, it never measures |

## Architecture

Three moving parts, each with its own rhythm, communicating through shared state:

- **The monitor** runs forever in a background thread, measures all endpoints on an interval, and stores the latest batch of reports.
- **Flask** serves that stored batch when asked. It never runs the async loop; it just returns the most recent snapshot.
- **The dashboard** polls `/status` on its own interval and repaints — no page reloads.

This separation means the monitored APIs get hit once per cycle regardless of how many people open the dashboard.

## The interesting problems

- **Designing the objects in harmony.** The hardest part was the modeling, not the code. Separating *what to check* (`Endpoint`, plain data), *how to measure* (the async client), *the raw measurement* (`Check`), *how to judge* (the `HealthRule` hierarchy) and *the final verdict* (`Report`) so each has a single responsibility and they connect cleanly. Once the design was right, the implementation was straightforward.
- **Async + retry.** Writing the `@retry` decorator over async functions, letting the exception bubble up so it could actually retry, and typing it generically so `mypy --strict` stayed happy.
- **Threads under gunicorn.** In development the monitor thread and Flask shared memory fine. In production under gunicorn they didn't — the thread was writing to one process's state while Flask read another's. Solved by launching the monitor inside the worker that serves requests.

## Stack

Python 3 · asyncio · httpx · Flask · gunicorn · pytest · mypy (strict) · deployed on Render.

## Run it locally

```bash
# from the project root
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# run the app
cd src
python app.py                    # http://localhost:5000
```

## Run the tests

```bash
pytest                           # rules + report aggregation
mypy --strict .                  # type checking
```

## Endpoints

- `GET /` — the dashboard
- `GET /status` — current state as JSON: `{ generated_at, services: [ { name, url, state, latency_ms, status_code, threshold, checked_at } ] }`

## Notes

The frontend is a minimal single-file dashboard generated with AI assistance — the focus of this project is the backend. Endpoints are chosen on purpose to demonstrate each state (one intentionally slow to show `degraded`, one intentionally broken to show `down`).

## Possible v2

Room to grow, deliberately left out to keep the scope tight: user-configurable endpoints from the UI (with safe rate limits), persisted history for real trend charts, and per-rule severity configuration. The current design already isolates rules and endpoints as data, so these would slot in without a rewrite.