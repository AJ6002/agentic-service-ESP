from dataclasses import dataclass

from app.llm.calls import direct_answer
from app.llm.client import LLMUnavailableError

GLOSSARY_FALLBACKS = {
    "tdh": "Total Dynamic Head (TDH) is the total equivalent height that a fluid is pumped, taking into account friction losses in the tubing.",
    "bep": "Best Efficiency Point (BEP) is the flow rate on a pump's performance curve where it operates at peak hydraulic efficiency.",
    "underload": "Underload occurs when motor current drops below calibrated thresholds, commonly indicating fluid pump-off, gas interference, or a sheared pump shaft.",
    "gas lock": "Gas lock occurs when free gas accumulates in the centrifugal pump impellers, causing the pump to lose head and stop delivering liquid.",
}


@dataclass
class DirectAnswer:
    text: str
    llm_available: bool  # False -> answer came from the glossary/offline fallback, not the model


async def handle_direct_query(query: str) -> DirectAnswer:
    """
    Direct Handler for the SIMPLE route (glossary / general inquiry).
    Bypasses Evidence Pack, XAI Synthesizer, and Visualization Spec entirely.

    If the LLM gateway is unavailable, this is reported explicitly via
    `DirectAnswer.llm_available=False` rather than silently swallowed —
    callers (main.py) must surface that to the user/response frame.
    """
    try:
        content = await direct_answer(query)
        if content:
            return DirectAnswer(text=content, llm_available=True)
    except LLMUnavailableError:
        pass

    # LLM is down — flagged via llm_available=False, not hidden. Fall back to
    # a deterministic glossary lookup so a SIMPLE glossary query still gets
    # some answer, but the caller knows the model itself did not respond.
    lower = query.lower()
    for term, definition in GLOSSARY_FALLBACKS.items():
        if term in lower:
            return DirectAnswer(text=definition, llm_available=False)

    return DirectAnswer(
        text=(
            "The AI engine is temporarily unavailable, so I can't generate a full explanation "
            f"right now for: {query.strip()}"
        ),
        llm_available=False,
    )
