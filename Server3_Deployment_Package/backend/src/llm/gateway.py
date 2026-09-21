"""
LLM Gateway — Phase 10: LLM Layer Architecture
Grounded in ESP APM LLM Architecture Design (Phase 10 §8)

Provides an OpenAI-compatible HTTP transport layer for local inference servers:
  - Ollama (http://localhost:11434/v1)
  - vLLM, LM Studio, or any OpenAI-compatible endpoint

Features:
  - Configurable timeout, exponential backoff retries (max 3)
  - Structured telemetry: tokens, latency_ms, model version
  - Project policy: LLM_OFFLINE is disabled — the real local LLM server is always used.
    Deterministic mock responses only occur as an automatic runtime fallback when the
    LLM server itself is unreachable (see is_available()), never via an env-var toggle.
"""

import os
import json
import time
import logging
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Load esp_agent/.env before reading any LLM_* vars below. This is the module that
# actually reads os.getenv(...) at import time, so the load must happen here rather
# than relying on some other entrypoint to have called load_dotenv() first — no other
# module in esp_agent currently does. find_dotenv() walks up from this file's directory
# so this works regardless of which script/CWD imports LLMGateway first.
try:
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv(usecwd=False), override=False)
except Exception:  # pragma: no cover — python-dotenv should always be installed, but
    pass            # never let a missing .env or import hiccup block LLM gateway startup.

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config (from environment)
# ---------------------------------------------------------------------------
# Defaults to llama.cpp HTTP server on Server 2 (http://192.168.1.191:8080/v1)
LLM_GATEWAY_URL: str = os.getenv("LLM_GATEWAY_URL", "http://192.168.1.191:8080/v1")
LLM_MODEL_NAME: str = os.getenv("LLM_MODEL_NAME", "Qwen2.5-Coder-3B-Instruct")
LLM_TIMEOUT_SEC: float = float(os.getenv("LLM_TIMEOUT_SEC", "120.0"))
LLM_MAX_RETRIES: int = int(os.getenv("LLM_MAX_RETRIES", "3"))
# Health probe timeout — must tolerate a model still loading weights, not just a warm server.
LLM_HEALTH_TIMEOUT_SEC: float = float(os.getenv("LLM_HEALTH_TIMEOUT_SEC", "2.0"))

# Hard project policy: the real local LLM is ALWAYS used. Offline/mock mode is disabled
# at the code level so no stray `$env:LLM_OFFLINE="1"` in any terminal can silently switch
# the agent back to canned mock responses. If the LLM server is genuinely unreachable,
# LLMGateway.chat() still falls back to _mock_response() automatically (see is_available()
# below) — that fallback is a runtime *availability* check, independent of this flag.
_LLM_OFFLINE_ENV = os.getenv("LLM_OFFLINE", "0").strip().lower() in ("1", "true", "yes")
if _LLM_OFFLINE_ENV:
    logger.warning(
        "LLM_OFFLINE=1 was set in the environment but is IGNORED by project policy — "
        "the real LLM server is always used. Unset LLM_OFFLINE if you did not intend this."
    )
LLM_OFFLINE: bool = False


# ---------------------------------------------------------------------------
# Response Schema
# ---------------------------------------------------------------------------
@dataclass
class LLMUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class LLMGatewayResponse:
    content: str
    model: str
    usage: LLMUsage = field(default_factory=LLMUsage)
    latency_ms: float = 0.0
    is_mock: bool = False
    finish_reason: str = "stop"


# ---------------------------------------------------------------------------
# Gateway
# ---------------------------------------------------------------------------
class LLMGateway:
    """
    OpenAI-compatible HTTP transport layer for local LLM inference via llama.cpp (llama-server).
    LangGraph → LLM Adapter → LLM Gateway → llama.cpp (CPU) / Qwen GGUF
    """

    def __init__(
        self,
        gateway_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout_sec: Optional[float] = None,
        max_retries: Optional[int] = None,
        offline_mode: Optional[bool] = None,
    ):
        self.gateway_url = (gateway_url or LLM_GATEWAY_URL).rstrip("/")
        self.model_name = model_name or LLM_MODEL_NAME
        self.timeout_sec = timeout_sec if timeout_sec is not None else LLM_TIMEOUT_SEC
        self.max_retries = max_retries if max_retries is not None else LLM_MAX_RETRIES
        self.offline_mode = offline_mode if offline_mode is not None else LLM_OFFLINE

    def is_available(self) -> bool:
        """Probe the llama.cpp / OpenAI health endpoint."""
        now = time.time()
        if hasattr(self, "_avail_cache") and (now - getattr(self, "_avail_ts", 0)) < 2.0:
            return self._avail_cache

        health_urls = [
            self.gateway_url.replace("/v1", "") + "/health",
            f"{self.gateway_url}/models",
        ]
        for url in health_urls:
            try:
                req = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(req, timeout=LLM_HEALTH_TIMEOUT_SEC) as resp:
                    if resp.status == 200:
                        self._avail_cache = True
                        self._avail_ts = now
                        return True
            except Exception:
                continue

        self._avail_cache = False
        self._avail_ts = now
        return False

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 512,
        json_mode: bool = False,
    ) -> LLMGatewayResponse:
        """
        POST to /v1/chat/completions with exponential backoff retries.
        Falls back to deterministic mock response if offline_mode=True or server unreachable.

        json_mode: when True, requests grammar-constrained JSON output from llama.cpp
        (OpenAI-compatible `response_format: {"type": "json_object"}`). This forces the
        server's sampler to only emit syntactically valid JSON, eliminating the class of
        "almost valid" outputs (missing commas, etc.) that plain text generation produces.
        """
        if self.offline_mode or not self.is_available():
            logger.info("LLMGateway: Server offline or unavailable — returning fast mock response.")
            return self._mock_response(messages)

        payload_dict: Dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if json_mode:
            payload_dict["response_format"] = {"type": "json_object"}
        payload = json.dumps(payload_dict).encode("utf-8")

        url = f"{self.gateway_url}/chat/completions"
        last_exc: Optional[Exception] = None

        if self.offline_mode or not self.is_available():
            logger.info("LLMGateway: Local LLM offline. Returning mock response instantly.")
            return self._mock_response(messages)

        for attempt in range(self.max_retries):
            try:
                t0 = time.monotonic()
                req = urllib.request.Request(
                    url,
                    data=payload,
                    method="POST",
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                )
                with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                    raw = resp.read().decode("utf-8")
                    latency_ms = (time.monotonic() - t0) * 1000
                    data = json.loads(raw)
                    return self._parse_response(data, latency_ms)

            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last_exc = exc
                wait = min(2 ** attempt, 8)
                logger.warning(
                    f"LLMGateway: attempt {attempt + 1}/{self.max_retries} failed ({exc}). "
                    f"Retrying in {wait}s..."
                )
                time.sleep(wait)

        logger.error(
            f"LLMGateway: all {self.max_retries} attempts failed. "
            f"Last error: {last_exc}. Returning offline mock response."
        )
        return self._mock_response(messages)

    def _parse_response(self, data: Dict[str, Any], latency_ms: float) -> LLMGatewayResponse:
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        content = message.get("content", "").strip()
        finish_reason = choice.get("finish_reason", "stop")

        usage_raw = data.get("usage", {})
        usage = LLMUsage(
            prompt_tokens=usage_raw.get("prompt_tokens", 0),
            completion_tokens=usage_raw.get("completion_tokens", 0),
            total_tokens=usage_raw.get("total_tokens", 0),
        )

        logger.info(
            f"LLMGateway: response received. "
            f"model={data.get('model', self.model_name)} "
            f"tokens={usage.total_tokens} latency={latency_ms:.0f}ms"
        )
        return LLMGatewayResponse(
            content=content,
            model=data.get("model", self.model_name),
            usage=usage,
            latency_ms=latency_ms,
            is_mock=False,
            finish_reason=finish_reason,
        )

    def _mock_response(self, messages: List[Dict[str, str]]) -> LLMGatewayResponse:
        # MOCK_SCAFFOLD: deterministic LLM mock | reason: automatic runtime fallback ONLY when the
        # llama.cpp server is genuinely unreachable (is_available() == False) | expiry: N/A — this is
        # an intentional availability safeguard, not scaffolding to remove | ref: gateway.chat()
        """
        Deterministic offline mock response. Returns structured JSON that the
        structured_output parser can validate. Used in CI and when LLM is offline.
        """
        last_user_msg = next((m.get("content", "") for m in reversed(messages) if m.get("role") == "user"), "")
        q_lower = last_user_msg.lower()
        if any(w in q_lower for w in ["hi", "hello", "role", "who are you", "identity"]):
            assessment = "Hello! I am Agent Jane, your AI SCADA Operations Assistant. I monitor ESP telemetry, predict failure risks, compute TDH/BEP physics, and provide diagnostic advisories."
            cause = "Operational Identity Check"
            rec = "Specify an asset ID (e.g. FS-010) or query sensor signals to begin diagnostic analysis."
            verif = "Ready for telemetry queries."
        elif any(w in q_lower for w in ["temp", "pressure", "vibration", "sensor", "alarm"]):
            assessment = "Multi-sensor telemetry evaluation complete. All active intake pressure, motor temperature, and vibration signals are within operational limits."
            cause = "Normal Telemetry Baseline"
            rec = "Continue regular SCADA telemetry monitoring."
            verif = "Verify baseline pressure and motor temperature logs."
        elif any(w in q_lower for w in ["tdh", "bep", "head", "submergence", "drawdown", "calculate"]):
            assessment = "Engineering physics calculation complete for operating parameters."
            cause = "Engineering Hydrodynamic Calculation"
            rec = "Maintain operating frequency near Best Efficiency Point (BEP)."
            verif = "Cross-reference calculated TDH against pump performance curve."
        elif any(w in q_lower for w in ["risk", "rul", "failure", "24h", "72h"]):
            assessment = "ML failure risk prediction model evaluated. 24h risk is 5% with RUL estimate of 1,080 hours."
            cause = "Low Degradation Risk"
            rec = "Schedule routine preventive maintenance check."
            verif = "Review 7-day RUL risk trajectory."
        elif any(w in q_lower for w in ["simulate", "what-if", "frequency", "water cut", "58 hz", "85%"]):
            assessment = "Digital Twin what-if simulation completed across operating envelope."
            cause = "Digital Twin Simulation"
            rec = "Verify motor current limits before adjusting VSD frequency."
            verif = "Confirm simulated head against system curve."
        else:
            assessment = f"Operational analysis complete for prompt: '{last_user_msg[:60]}'."
            cause = "Normal System Operations"
            rec = "Maintain current operating parameters."
            verif = "Confirm SCADA telemetry alignment within 4 hours."

        mock_content = json.dumps({
            "assessment": assessment,
            "hypotheses": [
                {
                    "cause": cause,
                    "confidence": 0.92,
                    "reasoning": f"Evaluated prompt context: {last_user_msg[:60]}",
                    "supporting_evidence": ["EV-001"],
                    "contradicting_evidence": []
                }
            ],
            "uncertainties": ["Continuous telemetry monitoring active."],
            "recommendation": rec,
            "verification": verif,
            "_mock": True,
            "_query_echo": last_user_msg[:80],
        })
        logger.info(f"LLMGateway: returning dynamic mock response for query '{last_user_msg[:30]}'")
        return LLMGatewayResponse(
            content=mock_content,
            model=f"{self.model_name}-mock",
            usage=LLMUsage(prompt_tokens=80, completion_tokens=120, total_tokens=200),
            latency_ms=1.0,
            is_mock=True,
            finish_reason="stop",
        )
