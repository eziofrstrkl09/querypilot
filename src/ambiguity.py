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

RANKING_METRIC_PATTERN = re.compile(
    r"\b(?:ranked\s+by|based\s+on|measured\s+by|in\s+terms\s+of|by)\b"
    r"(?:\W+\w+){0,3}?\W+"
    r"\b(?:number\s+of\s+orders|order\s+count|orders|"
    r"spend(?:ing)?|revenue|sales|units(?:\s+sold)?|"
    r"quantity|profit|rating|payment\s+amount)\b",
    re.IGNORECASE
)


def ranking_metric_present(question: str) -> bool:
    """Check whether a ranking cue is followed by a recognized metric."""
    return bool(RANKING_METRIC_PATTERN.search(question))

"""How it works:
- First, it looks for a ranking cue: by, ranked by, based on, etc.
- Then it allows up to three intervening words.
- Finally, it looks for a recognized metric.
- It doesn't treat country, category or a time period as ranking metrics."""