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