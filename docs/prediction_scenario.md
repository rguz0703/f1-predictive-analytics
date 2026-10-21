# Prediction Scenario: Qualifying Lap Time

This spec is the agreement that feature engineering (Milestone 4) and its leakage
tests are checked against. It is the design; the code doesn't exist yet.

## Target

For each driver entered in a **Grand Prix qualifying session** (sprint
qualifying excluded), the target is their **best valid lap time**: the minimum
of their official Q1/Q2/Q3 times, in seconds.

The model predicts **relative pace** rather than raw seconds:

```
relative_pace = best_lap_time / circuit_reference_time
```

`circuit_reference_time` must be known before the weekend. The first choice is
the previous year's pole time at the same circuit layout. Raw lap times are
dominated by circuit length (Monaco ≈ 70 s vs. Spa ≈ 105 s), so a raw-time model
would mostly learn which track it is. Predictions are converted back to seconds
for reporting.

Fallbacks, for new circuits or changed layouts, are documented when they are
implemented.

## Prediction moment

**Scenario A (baseline):** the Thursday before the race weekend, with only
completed past events available.

| Allowed | Not allowed |
|---|---|
| Results and lap times from previous events | Anything from the target weekend (practice, qualifying) |
| Driver/team rolling form up to the previous event | Final qualifying position or Q1/Q2/Q3 of the target event |
| Circuit history from previous seasons | Actual session weather |
| The entry list and calendar | Telemetry from the target session |

**Scenario B (Milestone 5):** after the final practice session, adding practice
pace. Sprint weekends have only one practice session, which needs separate
handling.

## Known sources of noise

- **Wet or mixed sessions** produce large outliers that Scenario A can't predict.
  Errors are reported with and without them.
- **Elimination bias:** Q1 eliminees only have a Q1 time, set on a slower track
  than Q3 times. The target is still well defined; this is documented as a
  limitation.
- **Regulation changes** (2022, 2026) shift lap times across the whole grid.

## Baselines and models

1. **Naive:** the driver's best qualifying time at the same circuit last year,
   falling back to the team's, then the field median.
2. **Relative naive:** last year's pole × the driver's rolling average
   gap-to-pole over their last N races.
3. **Ridge regression** on point-in-time features.
4. Tree ensembles or gradient boosting **only if** they beat 1–3 under the same
   validation.

## Metrics

MAE and RMSE in seconds (also shown in milliseconds), plus MAE as a % of lap time
so circuits can be compared. Reported overall, per season and per circuit.

## Validation

- **Walk-forward by race** with an expanding training window. Each fold trains
  only on events dated strictly before the predicted event.
- Development folds: 2019–2023 (2018 is warm-up history for rolling features).
- **Held-out test: 2024–2025**, evaluated once at the end of a modeling round.
- **2026** is reported separately as a regulation-change stress test.
- No random splits. Every feature is computed with an explicit `as_of`
  timestamp, and a unit test checks that no feature uses data dated on or after
  the target event.
