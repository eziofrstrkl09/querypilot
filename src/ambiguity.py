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

_CUE = (
    r"(?:ranked\s+by|sorted\s+by|based\s+on|"
    r"measured\s+by|in\s+terms\s+of|by)"
)

_METRIC = (
    r"(?:number\s+of\s+orders|order\s+count|orders|"
    r"spend(?:ing)?|revenue|sales|units(?:\s+sold)?|"
    r"quantity|profit|rating|payment\s+amount)"
)

_METRIC_MODIFIER = (
    r"(?:(?:total|overall|gross|net)\s+)?"
)

RANKING_METRIC_PATTERN = re.compile(
    r"\b" + _CUE + r"\s+" + _METRIC_MODIFIER +
    r"\b" + _METRIC + r"\b",
    re.IGNORECASE
)


def ranking_metric_present(question: str) -> bool:
    return bool(RANKING_METRIC_PATTERN.search(question))

""" This is intentionally conservative. 
    It recognizes by total spend, sorted by revenue, 
    and in terms of order count, but does not infer that 
    a metric is specified merely because a metric word appears 
    somewhere later."""