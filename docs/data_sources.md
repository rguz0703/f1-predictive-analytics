# Data Sources

Research done for Milestone 0 (2026-10-20). Each fact below was checked against
the source it cites. Items marked **unverified** are re-checked in Milestone 2
before anything relies on them.

## Summary

| Need | Source | Access | Coverage |
|---|---|---|---|
| Schedules, qualifying Q1/Q2/Q3 times, race results, grid, standings | **Jolpica-F1** (Ergast-compatible API) | FastF1's Jolpica interface | Results from 1950. Start year for qualifying times **unverified** |
| Practice/qualifying lap data, tyres, deleted laps, track status, weather | **FastF1** (F1 live-timing data) | `fastf1.get_session(...).load(...)` | 2018 onward |

A single library, **FastF1**, is used for both. It covers the timing data and
also has a Jolpica-F1 interface, so caching and rate limiting are handled in
one place.

## Jolpica-F1

- Successor to the deprecated Ergast API, with backwards-compatible endpoints at
  `https://api.jolpi.ca/ergast/f1/`. Source: <https://github.com/jolpica/jolpica-f1>
- **Auth:** none required. Jolpica requires a custom User-Agent; their example
  is `MyGreatF1App/1.2.3 FastF1/1.2.2`. Source: [docs/README.md](https://github.com/jolpica/jolpica-f1/blob/main/docs/README.md)
- **Rate limits (unauthenticated):** burst of 4 requests/second, sustained
  limit of 500 requests/hour. Exceeding them returns HTTP 429. The docs say the
  limits "will decrease in the future". Source: [docs/rate_limits.md](https://github.com/jolpica/jolpica-f1/blob/main/docs/rate_limits.md)
- **Endpoints:** circuits, constructors, constructorStandings, drivers,
  driverStandings, laps, pitstops, qualifying, races, results, seasons, sprint,
  status. Pagination uses `limit` (default 30, max 100) and `offset`.
- **Coverage notes:** laps from 1996, pit stops from 2011 (per the endpoint docs).
- **License:** data under **CC BY-NC-SA 4.0**. The API is free for
  **non-commercial use**. It is volunteer-run with no uptime or correctness
  guarantees. Source: [TERMS.md](https://github.com/jolpica/jolpica-f1/blob/main/TERMS.md)
- Verified response (2026-10-20): `GET /ergast/f1/2024/1/qualifying/` returned
  HTTP 200 JSON with fields `Driver`, `Constructor`, `position`, `Q1`, `Q2`,
  `Q3` (strings like `"1:29.179"`), with `cache-control: max-age=600`.

## FastF1

- Python library (MIT), version 3.8.3 at time of writing. Requires Python ≥ 3.10,
  `pandas<3` and `numpy<3`. Source: PyPI metadata.
- **Coverage:** "Timing data, session information, car telemetry and position
  data are available from 2018 onwards". Schedules and results go back to 1950
  through Jolpica/Ergast. Source: <https://docs.fastf1.dev/data_reference/index.html>
- **Caching:** enabled by default; disabling it is discouraged. Location is set
  by `fastf1.Cache.enable_cache(path)`, then the `FASTF1_CACHE` environment
  variable, then an OS default (macOS: `~/Library/Caches/fastf1`). This project
  sets it explicitly to `data/cache/fastf1` (gitignored). Source: <https://docs.fastf1.dev/fastf1.html>
- **Rate limits:** FastF1 enforces limits itself. It throttles on a soft limit
  and raises `fastf1.RateLimitExceededError` on a hard limit. Requests served
  from the cache don't count. No numeric limits are published.
- **Legal:** FastF1 is unofficial and not associated with the Formula 1
  companies. F1 trademarks belong to Formula One Licensing B.V.

## Implications for this project

1. **No raw or processed data is committed.** The CC BY-NC-SA license forbids
   commercial reuse and requires share-alike, so the repository ships code
   only. Anyone reproducing the results downloads the data themselves.
2. **Caching is mandatory.** At 500 requests/hour, re-downloading on every run is
   not viable, and cached requests don't count against the limit.
3. **Load only what is needed.** Telemetry and position data are large. Ingestion
   loads laps and results only (`telemetry=False`) until a milestone needs more.
4. **Provenance:** each ingested dataset will record its source, endpoint or
   session, retrieval timestamp and library version (Milestone 2).

## Open questions for Milestone 2

- First season with Q1/Q2/Q3 times in Jolpica qualifying data.
- Whether FastF1 sends an identifying User-Agent to Jolpica, or whether one has
  to be configured.
- How deleted (track-limits) laps and red-flagged sessions appear in each source.
