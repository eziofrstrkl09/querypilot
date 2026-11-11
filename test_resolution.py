from src.ambiguity import is_term_resolved


TESTS = [
    # Active
    ("active", "Active customers by country", False),
    ("active", "Recently active customers", False),
    ("active", "How many customers are active?", False),
    ("active", "Active customers since January 2025", True),
    ("active", "How many customers were active in 2025?", True),
    ("active", "Customers active within the past 60 days", True),
    ("active", "Active customers last week who ordered", True),

    # Growth
    ("growth", "Revenue growth by category", False),
    ("growth", "Monthly revenue growth", False),
    ("growth", "Growth between 2024 and 2025", False),
    ("growth", "Year over year revenue growth", True),
    ("growth", "Growth in orders since 2024", True),

    # Loyalty
    ("loyal", "Loyal customers who placed orders", False),
    ("loyalty", "Customer loyalty by repeat purchases", True),
    ("loyal", "Loyal customers by purchase frequency", True),

    # Most valuable
    ("most valuable", "Most valuable customers who placed orders", False),
    ("most valuable", "Most valuable customers by total spend", True),
]


def main():
    passed = 0

    for term, question, expected in TESTS:
        actual = is_term_resolved(term, question)
        success = actual is expected

        print(f"{'PASS' if success else 'FAIL'}: {question}")

        if not success:
            print(f"  Term: {term}")
            print(f"  Expected: {expected}")
            print(f"  Actual: {actual}")
        else:
            passed += 1

    print(f"\nResults: {passed}/{len(TESTS)} passed")


if __name__ == "__main__":
    main()