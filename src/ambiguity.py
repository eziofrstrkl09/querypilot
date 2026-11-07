import re


WATCHLIST_PATTERN = re.compile(
    r"(?<!\w)(most[\s\-\u2010\u2011]+valuable|best|"
    r"top(?![\s\-\u2010\u2011]+level)|"
    r"loyal(?:ty)?|active|growth)(?!\w)",
    re.IGNORECASE
)


def find_terms(question: str) -> list[str]:
    """Return unique watchlist terms found in a question."""

    matches = WATCHLIST_PATTERN.finditer(question)

    return list(dict.fromkeys(
        re.sub(
            r"[\s\-\u2010\u2011]+",
            " ",
            match.group().lower()
        )
        for match in matches
    ))