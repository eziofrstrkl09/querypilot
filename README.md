# QueryPilot

**Natural Language to SQL | AI Engineering | Python | PostgreSQL | Gemini | SQLGlot**

QueryPilot is an AI-powered Natural Language to SQL (NL-to-SQL) system that converts user questions into executable PostgreSQL queries using a Large Language Model.

The project focuses on building a reliable SQL generation pipeline with database-aware validation, query safety mechanisms, and systematic evaluation.

**Status:** Phase 3 completed — SQL Safety & Validation. Development ongoing.

---

## Overview

QueryPilot allows users to interact with a relational database using natural language instead of manually writing SQL queries.

The current implementation uses Google's Gemini model to generate SQL from natural-language questions and applies a SQL validation layer before executing queries against PostgreSQL.

The project uses a synthetic e-commerce database called **NovaMart**, designed to represent realistic business data and relational complexity.

## Current Architecture

```text
          User Question
                |
                v
       Schema Retrieval
                |
                v
       Gemini SQL Generation
                |
                v
       SQLGlot Parsing
                |
                v
        SQL Safety Layer
        /       |        \
   Table     Column    Function
 Validation Validation Validation
        \       |        /
                |
                v
        Query Constraints
         (LIMIT 100)
                |
                v
       Read-only PostgreSQL
                |
                v
          Query Results
```

*Note: Ambiguity detection, schema retrieval through RAG, and other advanced pipeline stages are planned but not yet implemented.*

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core application |
| PostgreSQL | Relational database |
| Google Gemini API | Natural-language-to-SQL generation |
| SQLGlot | SQL parsing and AST-based validation |
| Psycopg2 | PostgreSQL connectivity |
| python-dotenv | Environment configuration |

## Database: NovaMart

A synthetic e-commerce database designed to test SQL generation across interconnected business entities.

| Metric | Count |
|---|---:|
| Tables | 28 |
| Columns | 160 |
| Foreign-key relationships | 41 |
| Customers | 2,000 |
| Orders | 12,000 |
| Order items | 23,431 |

The database covers customers, orders, products, inventory, suppliers, payments, refunds, shipments, marketing campaigns, reviews, and customer support.

Synthetic data enables repeatable testing without exposing real customer information.

## Implemented Features

### 1. Natural Language to SQL

- Generates PostgreSQL queries from natural-language questions.
- Uses database schema context to guide SQL generation.
- Uses Gemini with temperature set to 0 for the baseline configuration.

### 2. SQL Parsing and Validation

Implemented using SQLGlot.

- Single-statement enforcement.
- SELECT-only query restriction.
- Table allowlisting.
- Schema access restrictions.
- CTE scope validation.
- Function allowlisting.
- Schema-aware column validation.
- Rejection of nonexistent and ambiguous column references.

### 3. Query Execution Safety

- Dedicated read-only PostgreSQL database role.
- 10-second database statement timeout.
- Automatic maximum row limit of 100.
- Database errors handled separately from SQL generation.

## Testing and Evaluation

### SQL Safety Tests

| Test category | Result |
|---|---:|
| Valid SQL acceptance | 8/8 |
| Invalid SQL rejection | 13/13 |
| **Total** | **21/21 passed** |

Test coverage includes valid SELECT queries, JOINs, CTEs, UNIONs, column references, ambiguous columns, forbidden operations, unauthorized tables, and restricted PostgreSQL functions.

Additional regression tests verify database schema metadata, read-only execution, and statement timeout behaviour.

### Initial NL-to-SQL Baseline

Five manually selected questions were used for the initial evaluation.

| Question | Outcome |
|---|---|
| Customer count | Correct |
| Delivered orders | Incorrect |
| Product category names | Correct |
| Orders per store | Correct |
| Total revenue | Incorrect |

**Initial result: 3/5 correct (60%).**

The evaluation exposed important semantic errors, including incorrect table/grain selection and invalid enum-value generation.

The delivered-orders question, for example, exposed a distinction between shipment delivery and an order's final status.

This baseline will serve as the reference point for evaluating subsequent improvements.

## Project Roadmap

- [x] Phase 0 — Project specification and architecture
- [x] Phase 1 — PostgreSQL schema and synthetic data generation
- [x] Phase 2 — Baseline NL-to-SQL pipeline
- [x] Phase 3 — SQL safety and validation
- [ ] Phase 4 — Ambiguity detection
- [ ] Phase 5 — Schema retrieval using embeddings
- [ ] Phase 6 — RAG and business definitions
- [ ] Phase 7 — Bounded SQL self-repair
- [ ] Phase 8 — Explicit agent state machine
- [ ] Phase 9 — Evaluation framework
- [ ] Phase 10 — Observability with Langfuse
- [ ] Phase 11 — MCP integration
- [ ] Phase 12 — Productionization
- [ ] Phase 13 — AWS deployment
- [ ] Phase 14 — Optimization

## Running Locally

### Prerequisites

- Python
- PostgreSQL
- Google Gemini API key

### Setup

Clone the repository:

```bash
git clone https://github.com/eziofrstrkl09/querypilot
cd Querypilot
```

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Install dependencies using the project's dependency file.

Configure environment variables in a `.env` file:

```env
GEMINI_API_KEY=api_key
DATABASE_URL=database_connection_string
```

Create and populate the PostgreSQL database using the provided schema and synthetic data generator.

Run the application:

```bash
python -m src.main
```

Run SQL safety tests:

```bash
python -m test_sql_safety
```

Run schema regression tests:

```bash
python test_schema.py
```

## Current Limitations

QueryPilot is under active development.

- Semantic correctness is not yet consistently reliable.
- Ambiguous business terminology is not yet handled explicitly.
- Full-schema prompting is currently used instead of retrieval-based schema selection.
- No automated benchmark suite or production observability is implemented yet.

These limitations are being addressed incrementally through the project roadmap.

## Author

Developed as an AI Engineering portfolio project to explore reliable LLM-based database interaction, SQL validation, and retrieval-augmented generation.
