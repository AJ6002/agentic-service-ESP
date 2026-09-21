"""
Structured Output Validation & Repair Loop — Phase 10: LLM Layer Architecture
Grounded in ESP APM LLM Architecture Design §5

Guarantees the LLM returns JSON conforming to Pydantic schema contracts.
On failure, feeds the exact validation error back to Qwen for up to 2 repair attempts.

Flow:
  Qwen raw output
      ↓
  JSON extraction (strip markdown fences, prefix prose)
      ↓
  Pydantic validation
      ↓ (fail)
  Repair prompt → Qwen (up to LLM_REPAIR_RETRIES)
      ↓ (still fail)
  Raise StructuredOutputError
"""

import json
import logging
import re
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

try:
    from json_repair import loads as _json_repair_loads
    _HAS_JSON_REPAIR = True
except ImportError:  # pragma: no cover — fallback if library not installed
    _HAS_JSON_REPAIR = False

from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

LLM_REPAIR_RETRIES: int = 3


# ---------------------------------------------------------------------------
# Output Schemas
# ---------------------------------------------------------------------------
class HypothesisSchema(BaseModel):
    cause: str
    confidence: float
    # Optional: small local models frequently omit this; don't fail validation over it.
    reasoning: str = ""
    supporting_evidence: List[str] = []
    contradicting_evidence: List[str] = []


class AdvisoryOutputSchema(BaseModel):
    """
    Canonical schema for Qwen advisory output.
    The LLM MUST return JSON strictly conforming to this schema.
    """
    assessment: str
    hypotheses: List[HypothesisSchema] = []
    uncertainties: List[str] = []
    # Optional with a safe default: conversational/general-inquiry queries (e.g. OP07) often
    # have nothing actionable to recommend, and small local models omit the field rather
    # than write a placeholder. Don't fail validation over it.
    recommendation: str = "No specific action required at this time."
    verification: Union[str, List[str]] = Field(default="1. Verify sensor alignment.")


class ToolCallSchema(BaseModel):
    """Schema for Qwen tool call requests (dispatched to LangGraph tool registry)."""
    tool: str
    arguments: Dict[str, Any]


class ClassificationSchema(BaseModel):
    """Schema for Qwen classification results."""
    category: str
    confidence: float
    reasoning: Optional[str] = None


# ---------------------------------------------------------------------------
# JSON Extraction Helper
# ---------------------------------------------------------------------------
def extract_json_block(text: str) -> str:
    """
    Extract the full valid JSON object from raw model text.
    Handles markdown fences (```json ... ```), nested braces, and leading/trailing prose.
    """
    if not text:
        return ""

    # Strip code block fences
    cleaned = text.strip()
    if "```" in cleaned:
        # Extract content inside markdown fence if present
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
        if fence_match:
            cleaned = fence_match.group(1).strip()

    # Find the outermost opening '{' and closing '}'
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")

    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return cleaned[first_brace:last_brace + 1]

    return cleaned


def loads_lenient(json_str: str) -> Any:
    """
    Parse JSON using json-repair (battle-tested LLM output parser) when available,
    falling back to stdlib json + conservative hand-rolled repair if not installed.

    json-repair handles all common small-LLM output defects: missing commas,
    trailing commas, unclosed braces/brackets, markdown fences, unquoted keys,
    and truncation — far more robustly than hand-written regex.
    """
    if _HAS_JSON_REPAIR:
        # json_repair.loads() always returns a Python object — it never raises on
        # recoverable malformed JSON. Pass ensure_ascii=False to preserve evidence IDs.
        result = _json_repair_loads(json_str)
        return result

    # Fallback: stdlib strict parse, then one round of conservative regex repair.
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # Minimal regex repair: trailing commas + missing commas between lines.
        repaired = re.sub(r",(\s*[}\]])", r"\1", json_str)
        repaired = re.sub(
            r'((?:true|false|null|\"|[}\]0-9]))[ \t\r]*\n([ \t]*["{\[])',
            r"\1,\n\2",
            repaired,
        )
        repaired = re.sub(r",\s*,", ",", repaired)
        return json.loads(repaired)


# ---------------------------------------------------------------------------
# Structured Output Error
# ---------------------------------------------------------------------------
class StructuredOutputError(Exception):
    """Raised when structured output repair loop exhausts all retries."""
    pass


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------
class StructuredOutputValidator(Generic[T]):
    """
    Validates raw LLM text against a target Pydantic schema.
    Orchestrates repair loop via callback to LLM Adapter if parsing fails.
    """

    def __init__(self, schema: Type[T], max_repair_retries: int = LLM_REPAIR_RETRIES):
        self.schema = schema
        self.max_repair_retries = max_repair_retries

    def parse(self, raw_text: str) -> T:
        """
        Parse raw model text into target schema. No repair retries (caller handles).
        Raises StructuredOutputError on failure.
        """
        json_str = extract_json_block(raw_text)
        try:
            data = loads_lenient(json_str)
            return self.schema.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise StructuredOutputError(
                f"StructuredOutputValidator: JSON/Pydantic parse failure for schema "
                f"'{self.schema.__name__}'. Error: {exc}. "
                f"Raw (truncated): {raw_text[:200]}"
            ) from exc

    def parse_with_repair(
        self,
        raw_text: str,
        repair_callback,  # Callable[[str], str]: sends repair prompt to LLM, returns new raw text
    ) -> T:
        """
        Parse raw model text, with up to max_repair_retries LLM repair calls on failure.
        repair_callback: function(repair_prompt: str) -> raw_text: str
        """
        attempt = 0
        current_text = raw_text

        while True:
            json_str = extract_json_block(current_text)
            try:
                data = loads_lenient(json_str)
                result = self.schema.model_validate(data)
                if attempt > 0:
                    logger.info(
                        f"StructuredOutputValidator: repair succeeded on attempt {attempt}."
                    )
                return result

            except (json.JSONDecodeError, ValidationError) as exc:
                if attempt >= self.max_repair_retries:
                    raise StructuredOutputError(
                        f"StructuredOutputValidator: repair loop exhausted after "
                        f"{self.max_repair_retries} retries. Schema: {self.schema.__name__}. "
                        f"Last error: {exc}"
                    ) from exc

                attempt += 1
                error_detail = str(exc)
                repair_prompt = (
                    f"Your previous response failed Pydantic validation.\n"
                    f"Schema: {self.schema.__name__}\n"
                    f"Validation Error: {error_detail}\n\n"
                    f"Your invalid response was:\n{current_text[:400]}\n\n"
                    f"Return ONLY a strictly valid JSON object matching the schema. "
                    f"No prose, no markdown fences, no extra keys. "
                    f"Fix the exact validation error above."
                )
                logger.warning(
                    f"StructuredOutputValidator: attempt {attempt}/{self.max_repair_retries} "
                    f"— sending repair prompt to LLM. Error: {error_detail[:120]}"
                )
                current_text = repair_callback(repair_prompt)
