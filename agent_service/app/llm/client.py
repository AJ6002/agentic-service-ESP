"""
Shared LLM gateway client.

Single place every LLM-calling stage (Router, Direct Handler, Workflow
narration) goes through — so "the LLM is down" is detected once, in one
way, and reported the same way everywhere, instead of each caller having
its own silent `except Exception: pass`.

Never raises on ordinary business logic (bad JSON from the model still
comes back as text); only raises LLMUnavailableError when the gateway
itself could not be reached or reported an error status. Callers decide
their own fallback, but must not swallow this exception silently — they
must flag it (record_audit + surface to the user), per the "whenever the
LLM is down, we need to flag that" requirement.
"""

import os
from dataclasses import dataclass

import httpx

from app.audit.audit_sink import record_audit


class LLMUnavailableError(Exception):
    """Raised when the LLM gateway cannot be reached or errors out."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


@dataclass
class LLMResult:
    text: str
    available: bool  # False only ever set by build_unavailable_result helpers


def _config() -> tuple[str, str, float]:
    llm_url = os.getenv("LLM_GATEWAY_URL", "http://127.0.0.1:8080/v1")
    model_name = os.getenv("LLM_MODEL_NAME", "Qwen2.5-Coder-3B-Instruct-Q4_K_M")
    timeout = float(os.getenv("LLM_TIMEOUT_SEC", "30.0"))
    return llm_url, model_name, timeout


async def call_llm_chat(
    system_prompt: str,
    user_content: str,
    temperature: float = 0.0,
    caller: str = "unknown",
) -> str:
    """
    Calls the LLM gateway's chat/completions endpoint.

    Raises LLMUnavailableError (never a bare Exception) if:
      - the connection fails / times out,
      - the gateway returns a non-200 status,
      - the response body doesn't contain the expected choice content.

    `caller` is a short tag ("router", "direct_handler", "workflow") used
    only for the audit record, so a downed LLM can be traced to which
    stage first noticed it.
    """
    llm_url, model_name, timeout = _config()

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{llm_url}/chat/completions",
                json={
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    "temperature": temperature,
                },
            )
    except (httpx.ConnectError, httpx.TimeoutException, httpx.TransportError) as ex:
        record_audit("llm_unavailable", payload={"caller": caller, "reason": f"connection_error: {ex}"})
        raise LLMUnavailableError(f"LLM gateway unreachable: {ex}") from ex

    if resp.status_code != 200:
        record_audit(
            "llm_unavailable",
            payload={"caller": caller, "reason": f"http_{resp.status_code}"},
        )
        raise LLMUnavailableError(f"LLM gateway returned HTTP {resp.status_code}")

    try:
        data = resp.json()
        content = data["choices"][0]["message"]["content"].strip()
    except (ValueError, KeyError, IndexError) as ex:
        record_audit("llm_unavailable", payload={"caller": caller, "reason": f"malformed_response: {ex}"})
        raise LLMUnavailableError(f"LLM gateway returned malformed response: {ex}") from ex

    return content
