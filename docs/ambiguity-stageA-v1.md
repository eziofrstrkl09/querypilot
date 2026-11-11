# QueryPilot — Ambiguity Detection, Stage A v1

Deterministic watchlist + rule check. No model calls, no database access.
Evaluated once on the frozen benchmark `ambiguity-set-v1` (29 cases). Rules were not edited after seeing these results.

## Configuration

- Watchlist: `best`, `top`, `most valuable`, `loyal`/`loyalty`, `active`, `growth`
- Rule: a watchlist term is *resolved* only if the question supplies what it needs, otherwise the question is flagged
  - ranking terms (`best`, `top`, `most valuable`): ranking cue (`by`, `ranked by`, `in terms of`, ...) immediately followed by a known metric. Grouping ("by country") and time windows do not count
  - `loyal`/`loyalty`: cue plus a loyalty metric (repeat purchases, purchase frequency, number of orders, tenure, lifetime spend)
  - `active`: explicit `is_active` reference or an explicit time window. Vague words ("recently", "currently") do not count
  - `growth`: a known metric *and* a comparison/range ("year over year", "since 2024", "between 2024 and 2025"). Granularity ("monthly") or a single year does not count
- Clarification options come from fixed templates per term
- Code tag: `ambiguity-stageA-v1` (`TODO: confirm commit hash`)
- Unit tests: term matching 15/15, ranking metric 19/19, resolution rules 17 cases (`TODO: record output`)

## Results

| Metric | Value |
|---|---|
| Clarification precision | 9/11 = 82% |
| Clarification recall, overall | 9/13 = 69% |
| Clarification recall, in scope (slice A) | 9/9 = 100% |
| False-clarify rate | 2/16 = 12% |

| Slice | Description | Flagged | Expected |
|---|---|---|---|
| A | watchlist term, no metric | 9/9 | high |
| B | watchlist term, metric specified | 2/10 | 0 |
| C | plainly clear | 0/6 | 0 |
| D | ambiguous, outside watchlist | 0/4 | high |

Overall recall is capped at 9/13 by design: slice D contains four ambiguous questions that no watchlist term covers.

## Errors

| ID | Slice | Type | Question | Cause |
|---|---|---|---|---|
| 011 | B | false clarify | most valuable customers ranked by lifetime successful payment amount | modifier words ("lifetime successful") between cue and metric are not allowed |
| 012 | B | false clarify | most loyal customers by number of distinct orders | loyalty vocabulary expects "number of orders"; "distinct" is a modifier |
| 023 | D | missed | What was our total revenue? | not on watchlist; four defensible definitions exist |
| 024 | D | missed | How many orders were delivered? | not on watchlist; `orders.status` vs shipment delivery |
| 025 | D | missed | What is our average order value? | not on watchlist |
| 026 | D | missed | What is our customer retention rate? | not on watchlist |

Both false clarifications are the safe-direction error: the user gets an unnecessary question, nothing wrong passes through. Both come from a deliberately strict vocabulary and were not "fixed" after the run.

## Interpretation

- Within its scope the detector caught every ambiguous case and flagged nothing plainly clear.
- Missing slice D is the design limit. Resolving "revenue", "delivered", "average order value" and "retention" requires approved business definitions (Phase 6), not a keyword list.
- The exit-set questions Q2 (delivered) and Q5 (revenue) are not flagged, so baseline failures on them are unchanged by Stage A.

## Caveats

- n is small (13 ambiguous cases); one miss moves recall about 8 points.
- Cases were authored with knowledge of the watchlist, so 100% on slice A shows the rules work as designed, not that they generalize to unseen phrasing.
- Predictions were not recorded before this run.
- Labels were proposed, then reviewed by the project author; interpretations for 023–026 depend on business definitions not yet finalized.

## What these results tell us

- Slice A: All deliberately ambiguous watchlist questions were caught.
- Slice B: Two clear questions were unnecessarily flagged because the metric vocabulary doesn't recognize lifetime successful payment amount and number of distinct orders.
- Slice C: No false clarifications.
- Slice D: All four ambiguous questions were missed because they don't use your watchlist terms. This is an intentional limitation of Stage A, not a reason to expand the watchlist after seeing the benchmark.

## Evaluation report summary

- Benchmark: 29 cases, tag ambiguity-set-v1.
- Precision: 9/11 = 82%.
- Recall: 9/13 = 69%.
- False-clarify rate: 2/16 = 12%.
- All four slice results.
- All eight errors (two false clarifications and six missed/expected D cases).
- Limitations: closed metric vocabulary and watchlist-only coverage.

## Next

- Wire `detect()` into the pipeline before SQL generation and confirm exit-set behavior is unchanged.
- Later: compare an LLM-based detector (branch `challenger-llm-ambiguity`) against Stage A on the same 29 cases.
- Phase 6: business-definition lookup is the intended fix for slice D.