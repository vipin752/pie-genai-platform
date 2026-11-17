"""Intent classification — Section 5.2.

SCAFFOLD: a keyword heuristic, not a trained/ML classifier. It exists so
the orchestrator has a real (if crude) routing decision to make, not to
claim real intent understanding. Confidence is reported so callers can
tell a confident match from a guess - per Section 5.2's own rule, nothing
downstream should treat a low-confidence classification as certain.
"""

from __future__ import annotations

from dataclasses import dataclass

# Subset of Section 5.2's intent list - only what this orchestrator can
# currently act differently on. Extend only as real differing behavior is
# added, not speculatively.
INTENT_GENERAL_QUESTION = "general_question"
INTENT_MARKET_ANALYSIS = "market_analysis"

_MARKET_KEYWORDS = (
    "nifty",
    "banknifty",
    "sensex",
    "option",
    "strike",
    "market",
    "trade",
    "pcr",
    "iv",
    "gamma",
)


@dataclass
class IntentResult:
    intent: str
    confidence: float  # 0.0-1.0; heuristic, not a calibrated probability


def classify_intent(text: str) -> IntentResult:
    lowered = text.lower()
    hits = sum(1 for kw in _MARKET_KEYWORDS if kw in lowered)
    if hits == 0:
        return IntentResult(intent=INTENT_GENERAL_QUESTION, confidence=0.5)
    # More keyword hits -> higher heuristic confidence, capped well below
    # 1.0 since this is pattern matching, not understanding.
    confidence = min(0.5 + 0.15 * hits, 0.85)
    return IntentResult(intent=INTENT_MARKET_ANALYSIS, confidence=confidence)
