# QueryPilot Execution & Evaluation Report

## System Architecture: Intended Flow

```text
User question
     |
     v
Stage A ambiguity detector
     |
     +---- Ambiguous --> Ask clarification
     |
     +---- Clear ------> Generate SQL
                               |
                               v
                           SQL safety
                               |
                               v
                           Execute query
```

## Benchmark Results

| Metric | Result | 
| ----- | ----- | 
| Clarification precision | 82% | 
| Clarification recall | 69% | 
| False-clarify rate | 12% | 
| Slice A detection | 9/9 | 
| Slice B false clarifications | 2/10 | 
| Slice C false clarifications | 0/6 | 
| Slice D detection | 0/4 | 

## Execution Output

```text
(Querypilot) PS D:\projects1\Querypilot> python -m src.main
Schema retrieved: 6350 characters
Allowed tables: 28
Tables with column metadata: 28

======================================================================
QUESTION 1: How many customers do we have?

Generated SQL:
SELECT count(*) FROM customers;

Validated SQL:
SELECT COUNT(*) FROM customers LIMIT 100

Rows returned: 1
Columns: ['count']
(2000,)

======================================================================
QUESTION 2: How many orders were delivered?

Generated SQL:
SELECT count(DISTINCT s.order_id)
FROM shipments s
WHERE s.delivered_at IS NOT NULL;

Validated SQL:
SELECT COUNT(DISTINCT s.order_id) FROM shipments AS s WHERE s.delivered_at IS NOT NULL LIMIT 100

Rows returned: 1
Columns: ['count']
(9617,)

======================================================================
QUESTION 3: What are the names of all product categories?

Generated SQL:
SELECT name FROM categories;

Validated SQL:
SELECT name FROM categories LIMIT 100

Rows returned: 24
Columns: ['name']
('Electronics',)
('Phones',)
('Laptops',)
('Audio',)
('Clothing',)
('Men',)
('Women',)
('Kids',)
('Home',)
('Kitchen',)

======================================================================
QUESTION 4: How many orders did each store handle?

Generated SQL:
SELECT s.store_id, s.name, COUNT(o.order_id) AS order_count
FROM stores s
LEFT JOIN orders o ON s.store_id = o.store_id
GROUP BY s.store_id, s.name;

Validated SQL:
SELECT s.store_id, s.name, COUNT(o.order_id) AS order_count FROM stores AS s LEFT JOIN orders AS o ON s.store_id = o.store_id GROUP BY s.store_id, s.name LIMIT 100

Rows returned: 5
Columns: ['store_id', 'name', 'order_count']
(4, 'QP Dubai', 983)
(2, 'QP Delhi', 956)
(3, 'QP Kolkata', 949)
(5, 'QP Singapore', 940)
(1, 'QP Mumbai', 970)

======================================================================
QUESTION 5: What was our total revenue?

Generated SQL:
SELECT SUM(amount) FROM payments WHERE status = 'completed';

Validated SQL:
SELECT SUM(amount) FROM payments WHERE status = 'completed' LIMIT 100

Rows returned: 1
Columns: ['sum']
(None,)

======================================================================
QUESTION 6: Who are our best customers?

CLARIFICATION REQUIRED
"best" can mean different things. Do you mean: by total revenue; or by number of orders; or by units sold?
```