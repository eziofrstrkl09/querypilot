# QueryPilot — Phase 4: Ambiguity Detection
## Technical Design, Implementation Progress and Execution Plan

**Project:** QueryPilot — Reliable Natural Language-to-SQL System  
**Phase:** 4 — Ambiguity Detection  
**Status:** In Progress  
**Primary approach:** Deterministic, heuristic-based detection (Stage A)  
**Benchmark:** `data/ambiguity_cases.json`  
**Benchmark version:** `ambiguity-set-v1`  
**Last updated:** 8 November 2026

---

# 1. Phase Overview

## 1.1 Objective

Phase 4 introduces an ambiguity-detection mechanism into QueryPilot.

The purpose is to identify natural-language questions that have multiple plausible interpretations and could consequently produce materially different SQL queries or results.

Instead of immediately generating SQL for every user question, QueryPilot should first determine whether the question is sufficiently well-defined.

For example:

**Question:**

"Who are our best customers?"

This question is ambiguous because "best" could refer to:
- Customers with the highest total spending.
- Customers with the highest number of orders.
- Customers with the most recent purchases.
- Customers with the highest average order value.

Generating SQL without resolving this ambiguity could produce a technically valid query that answers the wrong business question.

A reliable NL-to-SQL system must therefore distinguish between:
1. Questions that are sufficiently clear to proceed.
2. Questions that require clarification before SQL generation.

## 1.2 Primary goal

Implement a lightweight, deterministic ambiguity detector that:

- Identifies predefined ambiguous business terminology.
- Checks whether sufficient context resolves the ambiguity.
- Avoids unnecessary clarification requests.
- Uses predictable rules rather than an additional LLM call.
- Produces a structured result.
- Can be evaluated against a manually labelled benchmark.

The detector should improve the reliability of QueryPilot without introducing unnecessary latency, API costs or nondeterministic decisions.

---

# 2. Why Ambiguity Detection Is Necessary

Natural-language questions frequently omit information that is important for selecting the correct database entities, metrics, filters or aggregation methods.

The main ambiguity categories considered in QueryPilot are:

### 2.1 Metric ambiguity

A business term may refer to multiple metrics.

Example:
"Show our best customers."

Possible metrics include total spending, order count and recency.

### 2.2 Entity and grain ambiguity

A question may refer to an entity whose underlying database representation has a different grain.

Example:
"How many orders were delivered?"

Possible interpretations:
- Number of orders whose `orders.status` is `delivered`.
- Number of distinct orders associated with delivered shipments.
- Number of delivered shipment records.

These are not necessarily equivalent.

### 2.3 Time-period ambiguity

A question may omit the period over which a metric should be calculated.

Example:
"Show active customers."

Possible interpretations:
- Customers with `customers.is_active = TRUE`.
- Customers who placed an order within a recent period.

### 2.4 Business-definition ambiguity

Business terminology may not have a universally accepted definition.

Example:
"What was our total revenue?"

Possible definitions include:
- Gross successfully collected payments.
- Successfully collected payments minus refunds.
- Item revenue excluding cancelled and pending orders.

A database column does not automatically establish the correct business definition.

---

# 3. Architecture and Design Decisions

Phase 4 is divided into two conceptual stages.

## 3.1 Stage A — Heuristic ambiguity detection

**This is the implementation being developed in Phase 4.**

Stage A uses:
- A predefined terminology watchlist.
- Word-boundary matching.
- Deterministic contextual rules.
- Static clarification templates.

It does not use an LLM to decide whether a question is ambiguous.

The initial watchlist contains:

| Term | Potential ambiguity |
|---|---|
| best | Undefined ranking metric |
| top | Ranking criterion |
| most valuable | Undefined value metric |
| loyal | Undefined loyalty criterion |
| active | Undefined activity definition |
| growth | Undefined metric or comparison period |

The detector should not automatically classify every question containing these terms as ambiguous.

Instead, it should examine whether the question already supplies enough information.

Examples:

| Question | Expected interpretation |
|---|---|
| Who are our best customers? | Ambiguous |
| Show our top 5 products by units sold. | Clear |
| List the top-level product categories. | Clear |
| How many active customers do we have? | Ambiguous |
| How many customers with `is_active = TRUE` do we have? | Clear |
| Show revenue growth between 2024 and 2025. | Potentially clear if the metric is explicitly defined |

Important distinction: grouping information such as "by country" is not necessarily a ranking metric.

"Who are our best customers by country?" remains ambiguous because country only describes grouping; it does not define what makes a customer best.

## 3.2 Stage B — Definition-aware ambiguity detection

Stage B is planned for a later phase, alongside business-definition retrieval and RAG.

It will use retrieved business definitions to resolve ambiguity that simple heuristics cannot reliably handle.

For example, if QueryPilot retrieves an approved business definition stating that active customers are customers with `is_active = TRUE`, it may be able to resolve a question that Stage A would flag.

Stage B is NOT part of the current Phase 4 implementation.

The distinction is important:

- Phase 4: detect ambiguity using deterministic rules.
- Phase 6: introduce business-definition retrieval and definition-aware detection.

---

# 4. Frozen Evaluation Benchmark

A benchmark was created before implementing the detector.

This prevents the implementation from being designed entirely around examples encountered during development.

## 4.1 Benchmark details

File:

`data/ambiguity_cases.json`

Git tag:

`ambiguity-set-v1`

Commit:

`028c9bf`

Total cases: **29**

Unique IDs: **29**

Benchmark distribution:

| Slice | Cases | Purpose |
|---|---:|---|
| A | 9 | Watchlist terms with unresolved ambiguity |
| B | 10 | Watchlist terms that are resolved or have a non-ranking meaning |
| C | 6 | Clear questions without watchlist terms |
| D | 4 | Ambiguous questions outside the watchlist |
| **Total** | **29** | |

### Slice A — Ambiguous watchlist cases

These cases test whether the detector correctly identifies ambiguous terminology.

Examples include:
- Best customers.
- Most valuable customers.
- Active customers.
- Revenue growth without sufficient context.

### Slice B — Clear watchlist cases

These cases test whether the detector can avoid unnecessary clarification.

Examples include:
- Top products by units sold.
- Best-selling products with an explicit ranking metric.
- Top-level product categories.

This slice is especially important because a simplistic detector could flag every occurrence of `best` or `top`.

### Slice C — Clear questions without watchlist terms

These cases ensure that ordinary, well-defined questions are not unnecessarily flagged.

### Slice D — Ambiguous questions outside the watchlist

These cases test the limitations of the predefined terminology list.

Stage A is not expected to identify every possible ambiguity outside its watchlist.

This slice measures that limitation rather than hiding it.

## 4.2 Benchmark integrity

The benchmark has been committed and tagged.

The current repository also contains a separate branch:

`challenger-llm-ambiguity`

This branch preserves an experimental LLM-based ambiguity detector for a possible future comparison.

The primary implementation on `main` remains deterministic.

The benchmark must not be silently modified to improve evaluation results. Any new benchmark version should be separately reviewed, committed and tagged.

---

# 5. Current Implementation

## 5.1 Watchlist matching

File:

`src/ambiguity.py`

Implemented function:

`find_terms(question) -> list[str]`

Its responsibility is to identify the predefined watchlist terms in a question.

The implementation uses Python's standard-library `re` module.

Current matching behavior:

| Input | Expected output |
|---|---|
| Which are our best-selling products? | `["best"]` |
| Show our top 5 customers. | `["top"]` |
| How many inactive customers do we have? | `[]` |
| How many active customers do we have? | `["active"]` |
| Who are our most valuable customers? | `["most valuable"]` |
| Show revenue growth by category. | `["growth"]` |
| List the top-level product categories. | `[]` |
| Find our best and most valuable customers. | `["best", "most valuable"]` |

### Why word boundaries matter

A naïve substring search would incorrectly match `active` inside `inactive`.

Similarly, the term `top` should not trigger ranking ambiguity in `top-level`.

The implementation therefore uses:
- Case-insensitive matching.
- Word-boundary-aware matching.
- A specific exclusion for `top-level`.
- Support for hyphenated `best-selling`.

### Test results

Test file:

`test_ambiguity_terms.py`

Command:

`python -m test_ambiguity_terms`

Result:

**8/8 tests passed.**

This validates the initial watchlist-matching component only. It does not yet validate the complete ambiguity detector.

---

# 6. Challenges Identified and Their Remedies

## 6.1 False positives

**Problem:**

A detector that flags every watchlist term will unnecessarily interrupt users.

Example:

"Show the top 5 products by units sold."

The ranking metric is already specified.

**Remedy:**

Use contextual rules to identify whether the question contains sufficient metric information.

Do not treat the presence of a watchlist term as sufficient evidence of ambiguity.

## 6.2 False negatives

**Problem:**

Some ambiguous questions do not contain any watchlist terms.

Example:

"How many orders were delivered?"

This could refer to order status or shipment delivery records.

**Remedy:**

Maintain Slice D in the benchmark to measure these misses.

Stage A is intentionally limited. Broader detection can be introduced through later business-definition retrieval and other system improvements.

## 6.3 Ranking metric detection

**Problem:**

A naïve implementation might treat any occurrence of "by" as a resolved ranking criterion.

Example:

"Who are our best customers by country?"

Country is a grouping dimension, not a ranking metric.

**Remedy:**

Recognize actual metric expressions such as:
- Total spending.
- Revenue.
- Number of orders.
- Order count.
- Units sold.
- Quantity sold.
- Recency.

Do not consider arbitrary grouping dimensions sufficient.

Also support expressions such as:

"Top 5 products in terms of units sold."

The absence of the word "by" must not cause a false clarification.

## 6.4 Different meanings of the same word

**Problem:**

The same term can have different meanings depending on context.

Examples:
- `top` in "top customers" indicates ranking.
- `top-level` indicates hierarchy.
- `best` in "best-selling" has an implied sales-related metric.

**Remedy:**

Use targeted deterministic exceptions and contextual rules instead of broad substring matching.

## 6.5 Undefined business terminology

**Problem:**

Terms such as revenue, active and loyal can have multiple business definitions.

**Remedy:**

Stage A should flag recognized unresolved terminology where applicable.

Later, Stage B can use retrieved business definitions to reduce unnecessary clarifications.

## 6.6 Dataset-specific overfitting

**Problem:**

A detector could achieve a high benchmark score by memorizing the 29 questions without learning reusable patterns.

**Remedy:**

Keep detection rules general.

Test rules independently using unit tests.

Use the benchmark for evaluation, not as a collection of hardcoded question-to-label mappings.

## 6.7 Clarification quality

**Problem:**

Identifying ambiguity is not sufficient. The system must ask a useful clarification question.

**Remedy:**

Use static clarification templates for the initial Stage A implementation.

A clarification should:
- Be concise.
- Address the actual ambiguous term.
- Present the important alternative interpretations.
- Avoid introducing unsupported business definitions.

---

# 7. Planned Detector Output

The detector should expose a consistent structured interface.

Proposed function:

`detect_ambiguity(question) -> dict`

Expected output for a clear question:

```python
{
    "status": "clear",
    "term": None,
    "options": []
}
```

Expected output for an ambiguous question:

```python
{
    "status": "ambiguous",
    "term": "best",
    "options": [
        "Customers with the highest total spending",
        "Customers with the highest number of orders",
        "Customers with the most recent purchases"
    ]
}
```

The exact output contract should be finalized before integration into `main.py`.

The primary detector should not:
- Call Gemini.
- Connect to PostgreSQL.
- Generate SQL.
- Execute queries.
- Retrieve embeddings.
- Use an LLM to judge its own ambiguity decision.

Its role is limited to deterministic classification and clarification.

---

# 8. Evaluation Framework

A benchmark is useful only if its results are measured systematically.

The evaluator will compare predicted labels against the manually assigned benchmark labels.

## 8.1 Confusion matrix

| | Actually ambiguous | Actually clear |
|---|---:|---:|
| Predicted ambiguous | True Positive (TP) | False Positive (FP) |
| Predicted clear | False Negative (FN) | True Negative (TN) |

### True Positive

The detector correctly identifies an ambiguous question.

### False Positive

The detector asks for clarification even though the question is sufficiently clear.

### False Negative

The detector fails to identify an ambiguous question.

### True Negative

The detector correctly allows a clear question to proceed.

## 8.2 Evaluation metrics

### Precision

Measures how often clarification requests are justified.

`Precision = TP / (TP + FP)`

Higher precision means fewer unnecessary interruptions.

### Recall

Measures how many genuinely ambiguous questions are detected.

`Recall = TP / (TP + FN)`

Higher recall means fewer unresolved ambiguities pass through.

### False-clarify rate

Measures the proportion of genuinely clear questions incorrectly flagged.

`False-clarify rate = FP / (FP + TN)`

This is particularly important for user experience.

### Accuracy

`Accuracy = (TP + TN) / Total cases`

Accuracy will be reported, but it should not be the only optimization target.

A detector that labels everything clear could achieve a misleadingly reasonable accuracy on a dataset containing many clear questions.

## 8.3 Per-slice evaluation

The evaluator should report results separately for Slices A, B, C and D.

Expected behavior:

| Slice | Desired behavior |
|---|---|
| A | Detect most unresolved watchlist ambiguity |
| B | Avoid unnecessary clarification |
| C | Avoid unnecessary clarification |
| D | Expose ambiguity outside the watchlist |

Slice D is particularly useful for documenting the limitations of Stage A.

A low recall on Slice D does not automatically mean the implementation is incorrect. It demonstrates the limited coverage of a deliberately bounded heuristic approach.

---

# 9. Implementation Roadmap

## Step 1 — Watchlist matching

**Status: Completed**

- Create `src/ambiguity.py`.
- Implement `find_terms(question)`.
- Add word-boundary handling.
- Add `top-level` exclusion.
- Test case-insensitive matching.

Result: 8/8 tests passed.

## Step 2 — Contextual ambiguity rules

**Status: Pending**

Implement deterministic checks for:

- Ranking terms and ranking metrics.
- Activity definitions.
- Growth metrics and comparison periods.
- Unresolved business terminology.

The detector should distinguish between a term being present and its ambiguity actually being resolved.

## Step 3 — Static clarification templates

**Status: Pending**

Create clarification templates for the supported watchlist terms.

The output should consistently contain:
- Status.
- Detected term.
- Clarification options.

## Step 4 — Unit testing

**Status: Pending**

Test:
- Ambiguous ranking questions.
- Ranking questions with explicit metrics.
- Grouping dimensions mistaken for metrics.
- `top-level` hierarchy references.
- Active versus inactive matching.
- Growth with and without a defined metric and period.
- Multiple watchlist terms in one question.
- Questions without watchlist terms.

## Step 5 — Benchmark evaluator

**Status: Pending**

Create:

`evaluate_ambiguity.py`

Responsibilities:
- Load `data/ambiguity_cases.json`.
- Run every question through the detector.
- Compare predictions with expected labels.
- Calculate TP, FP, FN and TN.
- Calculate precision, recall, accuracy and false-clarify rate.
- Report per-slice results.
- Identify incorrect classifications for manual analysis.

## Step 6 — Error analysis and refinement

**Status: Pending**

Review every false positive and false negative.

Make the smallest justified rule changes.

Retest unit tests after every change.

Do not modify the frozen benchmark to make the detector look better.

## Step 7 — Phase 4 completion

**Status: Pending**

Once the detector and evaluator are reliable:

- Freeze the implementation.
- Record final benchmark results.
- Document limitations.
- Commit the completed implementation.
- Create a Git tag such as `phase4-ambiguity-v1`.

Integration into the complete QueryPilot pipeline should follow the project's architecture plan.

---

# 10. Git and Repository State

Important references:

| Item | Reference |
|---|---|
| Original Phase 2 baseline | `baseline-v1` |
| Phase 3 safety milestone | `phase3-safety` |
| Ambiguity benchmark | `ambiguity-set-v1` |
| Benchmark commit | `028c9bf` |
| LLM challenger branch | `challenger-llm-ambiguity` |
| LLM challenger commit | `beb28b4` |

The primary implementation is being developed on `main`.

The LLM-based challenger is intentionally kept on a separate branch so that it cannot accidentally become the primary Stage A detector.

The LLM challenger may later be evaluated against the same frozen 29-case benchmark.

The two approaches should be compared using identical evaluation cases and metrics.

---

# 11. Phase 4 Completion Criteria

Phase 4 should be considered complete when:

1. The deterministic watchlist detector is implemented.
2. Contextual rules distinguish unresolved ambiguity from resolved terminology.
3. Static clarification options are returned consistently.
4. Unit tests cover important edge cases.
5. All 29 benchmark cases are evaluated.
6. Precision, recall, accuracy and false-clarify rate are calculated.
7. Per-slice results are available.
8. False positives and false negatives have been reviewed.
9. Known limitations are documented.
10. The implementation is committed and tagged.

A perfect benchmark score is not a mandatory completion condition.

The objective is to produce a defensible, reproducible implementation with understood limitations, not to overfit a small benchmark.

---

# 12. Current Progress Summary

**Completed**
- Phase 4 scope and Stage A architecture established.
- 29-case manually labelled benchmark prepared.
- Benchmark corrections incorporated.
- Benchmark frozen with Git tag `ambiguity-set-v1`.
- LLM challenger separated into its own branch.
- Deterministic watchlist matcher implemented.
- Eight initial matching tests passed.

**Remaining**
- Contextual rule implementation.
- Complete ambiguity classification.
- Static clarification templates.
- Comprehensive unit tests.
- Benchmark evaluator.
- Precision, recall and false-clarify analysis.
- Final error analysis and Phase 4 release tag.

**Immediate next task:**

Implement contextual ambiguity rules in `src/ambiguity.py`.

Do not integrate the detector into the main SQL-generation pipeline yet. First establish that its independent classification behavior is correct and measurable.

---

# 13. Engineering Principles for This Phase

The following principles should guide all remaining work:

1. Deterministic first: Stage A must not depend on an LLM.
2. Benchmark integrity: the frozen benchmark is an evaluation reference, not a target to memorize.
3. Minimize false clarification: a clear question should not be interrupted unnecessarily.
4. Measure both precision and recall: neither metric alone describes detector quality.
5. Separate ambiguity detection from SQL generation.
6. Keep Stage A and Stage B distinct.
7. Prefer simple, explainable rules over an unnecessarily complex system.
8. Test every meaningful rule change.
9. Document limitations honestly.
10. Preserve the original Phase 2 baseline and the independent LLM challenger.

**End goal:** A small, explainable and independently testable ambiguity-detection component that improves QueryPilot's reliability before SQL generation, while establishing a measurable foundation for definition-aware ambiguity resolution in later phases.