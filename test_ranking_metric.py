from src.ambiguity import ranking_metric_present


TESTS = [
    ("Show the best products ranked by revenue", True),
    ("Top stores in terms of order count", True),
    ("Which clients are best by number of orders?", True),
    ("Best sellers by units sold", True),
    ("Who are our best customers?", False),
    ("Best customers by country", False),
    ("Top customers in the last 30 days", False),
    ("Top products by category", False),
    ("Show the top 5 customers", False),
    ("Which top customers placed orders last week?", False),
    
    # Clause-boundary traps: must not detect a ranking metric
    ("Best customers by country who placed orders", False),
    ("Top products by category that had sales", False),
    ("Best customers by city, orders last month", False),

    # Additional valid ranking expressions
    ("Best customers by total spend", True),
    ("Top customers sorted by revenue", True),

    # KNOWN LIMIT: unsupported metric vocabulary
    ("Top 5 customers by lifetime value", False),
    ("Best customers by average order value", False),
    ("Top products by amount sold", False),
    ("Top customers by region and revenue", False),
]


def main():
    passed = 0

    for question, expected in TESTS:
        actual = ranking_metric_present(question)
        success = actual is expected

        print(f"{'PASS' if success else 'FAIL'}: {question}")

        if not success:
            print(f"  Expected: {expected}")
            print(f"  Actual:   {actual}")
        else:
            passed += 1

    print(f"\nResults: {passed}/{len(TESTS)} passed")


if __name__ == "__main__":
    main()