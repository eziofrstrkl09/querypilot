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

_UNIT = r"(?:days?|weeks?|months?|quarters?|years?)"
_MONTH = (r"(?:january|february|march|april|may|june|july|august|"
          r"september|october|november|december)")
_LOYALTY_METRIC = (r"(?:repeat\s+purchases?|purchase\s+frequency|number\s+of\s+orders|"
                   r"order\s+count|tenure|lifetime\s+spend)")

ACTIVE_FLAG_PATTERN = re.compile(r"\bis_active\b", re.IGNORECASE)

TIME_WINDOW_PATTERN = re.compile(
    r"\b(?:(?:last|past)\s+(?:\d+\s+)?" + _UNIT +
    r"|this\s+(?:week|month|quarter|year)"
    r"|within\s+\d+\s+" + _UNIT +
    r"|since\s+(?:" + _MONTH + r"|\d{4})"
    r"|in\s+(?:" + _MONTH + r"\s+)?\d{4}"
    r"|(?:between\s+\d{4}\s+and|from\s+\d{4}\s+to)\s+\d{4})\b",
    re.IGNORECASE)

# Growth needs a comparison/range, not just a granularity ("monthly") or one year.
GROWTH_PERIOD_PATTERN = re.compile(
    r"\b(?:(?:year|month|quarter|week)[\s\-]+over[\s\-]+(?:year|month|quarter|week)"
    r"|yoy|mom|qoq"
    r"|between\s+\d{4}\s+and\s+\d{4}|from\s+\d{4}\s+to\s+\d{4}"
    r"|since\s+(?:" + _MONTH + r"|\d{4})"
    r"|(?:over|during)\s+the\s+(?:last|past)\s+\d+\s+" + _UNIT +
    r"|(?:compared\s+(?:to|with)|versus|vs\.?)\s+\S+)",
    re.IGNORECASE)

def is_term_resolved(term: str, question: str) -> bool:
    """True only if the question supplies what this term needs."""
    term = term.lower().strip()
    if term in {"best", "top", "most valuable"}:
        return ranking_metric_present(question)
    if term in {"loyal", "loyalty"}:
        return bool(re.search(_CUE + r"\s+" + _LOYALTY_METRIC, question, re.IGNORECASE))
    if term == "active":
        return bool(ACTIVE_FLAG_PATTERN.search(question) or TIME_WINDOW_PATTERN.search(question))
    if term == "growth":
        return bool(re.search(r"\b" + _METRIC + r"\b", question, re.IGNORECASE)
                    and GROWTH_PERIOD_PATTERN.search(question))
    return False

OPTIONS = {
    "best": ["by total revenue", "by number of orders", "by units sold"],
    "top": ["by total revenue", "by number of orders", "by units sold"],
    "most valuable": ["by total spend", "by number of orders", "by lifetime spend"],
    "loyal": ["by repeat purchase frequency", "by customer tenure", "by lifetime spend"],
    "loyalty": ["by repeat purchase frequency", "by customer tenure", "by lifetime spend"],
    "active": ["customers with is_active = true", "customers who ordered in a period you specify"],
    "growth": ["which metric (revenue, orders, units)",
               "which comparison (e.g. year over year, 2024 vs 2025)"],
}

def detect(question: str) -> dict:
    """Stage A: flag the question if any watchlist term is left unresolved."""
    unresolved = [t for t in find_terms(question) if not is_term_resolved(t, question)]
    if not unresolved:
        return {"status": "clear", "terms": [], "options": []}
    term = unresolved[0]
    return {"status": "ambiguous", "terms": unresolved, "options": OPTIONS[term],
            "clarification": f'"{term}" can mean different things. Do you mean: '
                             + "; or ".join(OPTIONS[term]) + "?"}