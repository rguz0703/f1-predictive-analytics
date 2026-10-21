# F1 Predictive Analytics Platform

A reproducible Formula 1 data pipeline and set of predictive models, built with
production engineering habits: tested code, explicit configuration, data
provenance, and leakage-safe chronological validation.

> **Status:** Milestone 1 (repository foundation) is complete. There is no data
> ingestion or modeling code yet; see [Roadmap](#roadmap).

## Motivation and problem

Qualifying decides the starting grid, and the grid strongly shapes the race
result. The first question this project answers:

> **Before a Grand Prix weekend starts, how fast will each driver's best
> qualifying lap be?**

It's harder than it looks:

- Lap times depend mostly on the circuit.
- Car performance shifts during a season and resets with regulation changes
  (2022, 2026).
- Weather and track evolution add noise that can't be known in advance.

The modeling question is whether driver form, team form and circuit history
beat simple historical baselines. The full spec, including what may and may not
be used as input, is in [docs/prediction_scenario.md](docs/prediction_scenario.md).

## Data sources

| Source | Used for | Coverage | License |
|---|---|---|---|
| [FastF1](https://docs.fastf1.dev/) | Session lap timing, tyres, weather, track status | 2018 onward | Library: MIT. Data is unofficial F1 timing |
| [Jolpica-F1](https://github.com/jolpica/jolpica-f1) (via FastF1) | Schedules, qualifying, results, standings | From 1950 | **CC BY-NC-SA 4.0**, non-commercial |

No API keys are needed. **This repository contains no F1 data.** It is downloaded
locally and cached under `data/`, which is gitignored. Details, rate limits and
caveats: [docs/data_sources.md](docs/data_sources.md).

*Data attribution: Jolpica-F1 (CC BY-NC-SA 4.0) and Formula 1 timing data
accessed through FastF1. This project is unofficial and not associated with
the Formula 1 companies.*

## Architecture

```
configs/            TOML configuration (paths, seasons, logging)
data/               local only, gitignored: raw/ → interim/ → processed/, cache/
docs/               data source research, prediction spec
src/f1_predictive_analytics/
├── config.py       settings loading, validation, env overrides
└── utils/          structured logging
tests/              pytest suite
```

Planned modules, added only when they're implemented: `data/` (ingestion,
validation, provenance), `features/` (point-in-time features), `models/`
(baselines, training, evaluation), `visualization/`, and a Streamlit `app/`.

Each pipeline stage reads and writes files under `data/`, so stages can be
rerun on their own and every result can be traced to its inputs.

## Modeling approach

- **Target:** relative pace (best qualifying lap ÷ a pre-weekend circuit
  reference time), converted back to seconds for reporting.
- **Baselines first:** naive same-circuit-last-year, then relative-pace naive,
  then Ridge regression. Complex models only if they beat these.
- **Validation:** walk-forward by race with an expanding window. Held-out test
  seasons 2024–2025, and 2026 as a regulation-change stress test. No random
  splits.
- **Metrics:** MAE and RMSE (seconds and milliseconds), and MAE as % of lap time.

## Setup

Requires [uv](https://docs.astral.sh/uv/). It installs the pinned Python 3.12
interpreter automatically.

```bash
git clone <repo-url> && cd f1-predictive-analytics
uv sync                      # creates .venv with Python 3.12 + locked dependencies
uv run pytest                # run the test suite
uv run ruff check .          # lint
```

Optional local overrides:

```bash
cp .env.example .env         # edit as needed
uv run --env-file .env pytest
```

### Why these choices

- **Python 3.12:** the newest version that FastF1 3.8 and its pandas<3/numpy<3
  pins fully support.
- **uv:** fast, with a committed lockfile (`uv.lock`) for reproducible installs.
  It uses uv-managed Python only, so a system or conda interpreter never leaks
  in.
- **TOML config via stdlib `tomllib`:** no extra dependency.

## Roadmap

| # | Milestone | Status |
|---|---|---|
| 0 | Discovery and architecture | ✅ Done |
| 1 | Repository foundation (config, logging, tests, CI) | ✅ Done |
| 2 | Data acquisition (cached, validated, with provenance) | ⏳ Next |
| 3 | Exploratory data analysis | Planned |
| 4 | Baseline models with walk-forward evaluation | Planned |
| 5 | Feature engineering and model improvement | Planned |
| 6 | Streamlit dashboard | Planned |
| 7 | Production readiness (Docker, tracking, deployment) | Planned |

Later goals: race finishing position prediction, driver and constructor
analysis, and tyre degradation and strategy analysis where the data allows.

## Known limitations

- The data is unofficial and community-maintained, with no correctness
  guarantees.
- Jolpica's rate limits (500 requests/hour) make the first full download slow;
  later runs use the cache.
- `PROJECT_ROOT` assumes the package runs from a source checkout (editable
  install). It isn't meant to be installed as a standalone wheel.

## License

Code: [MIT](LICENSE). Data retrieved by this code is subject to its providers'
terms (see above).
