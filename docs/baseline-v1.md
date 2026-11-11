# QueryPilot — Baseline v1

## 1. Baseline configuration

- **Model:** `gemini-3.5-flash-lite`
- **Temperature:** `0`
- **Database:** PostgreSQL
- **Schema:** 28 tables, 41 foreign-key relationships
- **Schema context:** approximately 1,587 tokens (6,350 characters)
- **Baseline approach:** Full schema prompt → LLM-generated SQL → SQL execution
- **Prompt status:** Frozen; no repair logic or prompt modifications.

## 2. Initial baseline accuracy

**Score: 3/5 (60%)**

| # | Question | Result | Verdict |
|---|---|---|---|
| 1 | Customer count | 2,000 | Correct |
| 2 | Orders delivered | 10,262 | Incorrect; reference is 8,791 |
| 3 | Product category names | 24 rows | Correct; includes parent and child categories |
| 4 | Orders per store | 5 stores, approximately 950 each | Correct |
| 5 | Total revenue | NULL | Incorrect; invalid payment status filter |

### Reference definitions

- **Delivered orders:** Count orders where `orders.status = 'delivered'`. Reference query: `SELECT COUNT(*) FROM orders WHERE status = 'delivered';` Result: **8,791**.
- **Revenue:** Sum successful payments where `payments.status = 'succeeded'`. Reference query: `SELECT SUM(amount) FROM payments WHERE status = 'succeeded';` Result: **2,194,961.56**.
- **Orders per store:** Count orders grouped by physical store. Online orders (`store_id IS NULL`) are excluded.

### Initial failure observations

- Wrong grain / table selection: shipment counts used instead of delivered order counts.
- Invalid enum value: `completed` used instead of the valid payment status `succeeded`.
- Silent failure: invalid payment status produced NULL rather than a database error.
- Other observations from the initial evaluation: incomplete answer (hidden NULL store) and prose/comment leakage.

## 3. Stability experiment

Five successful samples were targeted per question. API capacity errors (503) and rate-limit errors (429) are infrastructure failures, not successful model evaluations.

| Question | Successful samples | Observed results | Verdict |
|---|---:|---|---|
| Q1 — Customer count | 5/5 | 2,000 × 5 | Stable |
| Q2 — Delivered orders | 5/5 | 10,262 × 4; 9,617 × 1 | Unstable and incorrect |
| Q3 — Category names | 3/5 | Identical results in all 3 | Stable among observed samples; incomplete |
| Q4 — Orders per store | 5/5 | Identical correct results | Stable |
| Q5 — Total revenue | 2/5 | NULL × 2 | Incorrect; incomplete |

**Note:** Q3 and Q5 were interrupted before collecting five successful samples. Their stability conclusions are provisional.

### Distinct SQL behaviour

**Q2 — Delivered orders**

Two different SQL approaches appeared:

1. `SELECT COUNT(*) FROM shipments WHERE delivered_at IS NOT NULL`
   - Result: 10,262
2. `SELECT COUNT(DISTINCT o.order_id) FROM orders AS o JOIN shipments AS s ON o.order_id = s.order_id WHERE s.delivered_at IS NOT NULL`
   - Result: 9,617

Neither matches the reference count of 8,791.

**Q5 — Total revenue**

Both successful samples generated:

`SELECT SUM(amount) FROM payments WHERE status = 'completed'`

The query returned NULL because `completed` is not a valid payment status.

## 4. Key findings

1. Temperature 0 does not guarantee identical SQL generation or semantic results.
2. The model confuses shipment delivery with an order's final delivery status.
3. The model can invent enum values despite having the schema context.
4. SQL can execute successfully and still return a semantically incorrect result.
5. API availability and rate limits affect evaluation throughput and must be tracked separately from model accuracy.

## 5. Baseline limitations

- Full schema is provided without retrieval.
- No explicit ambiguity detection.
- No column-level validation.
- No business-definition retrieval.
- No bounded SQL repair.
- SQL safety and database read-only protections are implemented separately in Phase 3.

## 6. Evaluation rules

- Keep the baseline prompt frozen.
- Do not introduce repair logic into baseline measurements.
- Separate infrastructure failures from generation, validation, execution, and semantic failures.
- Compare generated results against explicit reference definitions.
- Do not claim stability from insufficient successful samples.

## Phase 4

baseline-v1 points to the original Phase 2 implementation without SQL validation. The later stability runs were performed using the Phase 3 safety wrapper, which additionally applies SQL validation and a row limit.

ambiguity.py and tets_ambiguity_terms.py are used for deterministic ambiguity watchlist matching. 