import re

""" (?<!\w) prevents matching a term inside a larger word, such as inactive.
    (?!\w) prevents partial word matches.
    top(?!-level) excludes the hierarchy meaning of top-level.
    The hyphen after best is allowed, so best-selling is detected.
    re.IGNORECASE handles capitalization."""

WATCHLIST_PATTERN = re.compile(
    r"(?<!\w)(most\s+valuable|best|top(?!-level)|loyal|active|growth)(?!\w)",
    re.IGNORECASE
)


def find_terms(question: str) -> list[str]:
    """Return unique watchlist terms found in a question."""
    matches = WATCHLIST_PATTERN.finditer(question)

    return list(dict.fromkeys(
        " ".join(match.group().lower().split())
        for match in matches
    ))