# testing baseline accuracy

QUESTIONS = [
    "How many customers do we have?",
    "How many orders were delivered?",
    "What are the names of all product categories?",
    "How many orders did each store handle?",
    "What was our total revenue?",
]

Score: 3/5 (Q2 ✗, Q5 ✗), n=5.
Prompt cost: ~1,587 tokens.
Failure categories: invented enum values ×2, wrong grain ×1, incomplete answer (hidden NULL store) ×1, prose/comment leak ×1.
Reference definitions: revenue = succeeded payments; store orders exclude online.
Rules: prompt frozen, no repair logic.

#	Question	Result	Verdict
1	Customer count	2000	✅ correct
2	Orders delivered	10,262	❌ wrong (should be 8,791 by orders.status)
3	Category names	24 rows	✅ correct (includes parents and children)
4	Orders per store	5 stores, ~950 each	✅ correct
5	Total revenue	None	❌ wrong, silent failure