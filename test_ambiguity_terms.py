from src.ambiguity import find_terms


TESTS = [
    ("Which are our best-selling products?", ["best"]),
    ("Show our top 5 customers.", ["top"]),
    ("How many inactive customers do we have?", []),
    ("How many active customers do we have?", ["active"]),
    ("Who are our most valuable customers?", ["most valuable"]),
    ("Show revenue growth by category.", ["growth"]),
    ("List the top-level product categories.", []),
    ("Find our best and most valuable customers.", ["best", "most valuable"]),
    ("List the top level categories", []),
    ("Who are our most-valuable customers?", ["most valuable"]),
    ("highest loyalty", ["loyalty"]),
    ("Who is our most\nvaluable customer?", ["most valuable"]),
    ("Show Top5 customers.", []),
    ("Find our bestselling products.", []),
    ("List the top   level categories", []),
]


def main():
    passed = 0

    for question, expected in TESTS:
        actual = find_terms(question)
        success = actual == expected

        print(f"{'PASS' if success else 'FAIL'}: {question}")

        if not success:
            print(f"  Expected: {expected}")
            print(f"  Actual:   {actual}")
        else:
            passed += 1

    print(f"\nResults: {passed}/{len(TESTS)} passed")


if __name__ == "__main__":
    main()