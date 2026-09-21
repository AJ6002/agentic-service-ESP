"""
LLM Adapter — Phase 10: LLM Layer Architecture
Grounded in ESP APM LLM Architecture Design §1

Provides a model-agnostic contract interface over Qwen3 4B / local LLMs:
  - generate()
  - structured_generate()
  - tool_call()
  - classify()
  - summarize()

LangGraph
   ↓
LLM Adapter
   ↓
LLM Gateway
   ↓
Qwen3 4B / Ollama / OpenAI API

This interface allows swapping model runtimes without redesigning LangGraph.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Type, TypeVar

from pydantic import BaseModel, Field

from src.llm.gateway import LLMGateway, LLMGatewayResponse
from src.llm.context_builder import CompactContextBuilder
from src.llm.prompts import LayeredPromptBuilder, SYSTEM_PROMPT
from src.llm.structured_output import (
    AdvisoryOutputSchema,
    ClassificationSchema,
    StructuredOutputError,
    StructuredOutputValidator,
    ToolCallSchema,
)
from src.llm.xai_builder import XAIVisualStoryBuilder, XAIExplanationPayload
from src.llm.observability import LLMTraceRecord, tracer

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


# ---------------------------------------------------------------------------
# High-Level Adapter Response Objects
# ---------------------------------------------------------------------------
class LLMGenerationResponse(BaseModel):
    content: str
    model: str
    tokens: int
    latency_ms: float
    is_mock: bool = False


class ClassificationResult(BaseModel):
    category: str
    confidence: float
    reasoning: Optional[str] = None


# ---------------------------------------------------------------------------
# LLM Adapter Contract
# ---------------------------------------------------------------------------
class LLMAdapter:
    """
    Model-agnostic LLM Adapter for ESP APM Agentic Platform.
    Enforces contract decoupling between LangGraph supervisor and underlying LLM models.
    """

    def __init__(
        self,
        gateway: Optional[LLMGateway] = None,
        context_builder: Optional[CompactContextBuilder] = None,
        xai_builder: Optional[XAIVisualStoryBuilder] = None,
    ):
        self.gateway = gateway or LLMGateway()
        self.context_builder = context_builder or CompactContextBuilder()
        self.xai_builder = xai_builder or XAIVisualStoryBuilder()
        # Trace of the most recent generate_advisory_from_compact_context() call —
        # lets callers read the real is_mock/model_name/latency_ms verdict for the
        # call that actually produced the current advisory, without re-probing
        # gateway.is_available() after the fact (see graph.py generate_advisory_draft_node).
        self.last_trace: Optional[LLMTraceRecord] = None

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        run_id: str = "RUN-001",
    ) -> LLMGenerationResponse:
        """
        Standard unconstrained generation endpoint.
        """
        messages = [
            {"role": "system", "content": system_prompt or SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        gw_resp = self.gateway.chat(messages, temperature=temperature)

        # Record observability trace
        tracer.record_trace(LLMTraceRecord(
            run_id=run_id,
            model_name=gw_resp.model,
            prompt_tokens=gw_resp.usage.prompt_tokens,
            completion_tokens=gw_resp.usage.completion_tokens,
            total_tokens=gw_resp.usage.total_tokens,
            latency_ms=gw_resp.latency_ms,
            is_mock=gw_resp.is_mock,
            validation_passed=True,
        ))

        return LLMGenerationResponse(
            content=gw_resp.content,
            model=gw_resp.model,
            tokens=gw_resp.usage.total_tokens,
            latency_ms=gw_resp.latency_ms,
            is_mock=gw_resp.is_mock,
        )

    def structured_generate(
        self,
        prompt: str,
        schema: Type[T],
        system_prompt: Optional[str] = None,
        run_id: str = "RUN-001",
        objective_id: str = "OP01_PRODUCTION_DECLINE",
    ) -> T:
        """
        Structured generation endpoint enforcing Pydantic schema validation
        with up to 2-step repair retries on malformed JSON or validation errors.
        """
        validator = StructuredOutputValidator(schema)
        messages = [
            {"role": "system", "content": system_prompt or SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        repair_attempts = [0]

        def _repair_callback(repair_prompt: str) -> str:
            repair_attempts[0] += 1
            repair_messages = list(messages) + [
                {"role": "user", "content": repair_prompt}
            ]
            resp = self.gateway.chat(repair_messages, temperature=0.0, json_mode=True)
            return resp.content

        gw_resp = self.gateway.chat(messages, temperature=0.0, json_mode=True)

        try:
            parsed = validator.parse_with_repair(
                raw_text=gw_resp.content,
                repair_callback=_repair_callback,
            )
            validation_passed = True
            error_str = None
        except StructuredOutputError as exc:
            validation_passed = False
            error_str = str(exc)
            logger.error(
                f"LLMAdapter: structured_generate failed after retries: {exc}\n"
                f"RAW MODEL OUTPUT (truncated 800 chars): {gw_resp.content[:800]!r}"
            )
            raise

        finally:
            tracer.record_trace(LLMTraceRecord(
                run_id=run_id,
                objective_id=objective_id,
                model_name=gw_resp.model,
                prompt_tokens=gw_resp.usage.prompt_tokens,
                completion_tokens=gw_resp.usage.completion_tokens,
                total_tokens=gw_resp.usage.total_tokens,
                latency_ms=gw_resp.latency_ms,
                is_mock=gw_resp.is_mock,
                validation_passed=validation_passed,
                repair_attempts=repair_attempts[0],
                error=error_str,
            ))

        return parsed

    def generate_advisory_from_compact_context(
        self,
        compact_context: Dict[str, Any],
        user_query: Optional[str] = None,
        run_id: str = "RUN-001",
    ) -> tuple[AdvisoryOutputSchema, XAIExplanationPayload]:
        """
        End-to-end advisory generation:
          1. Layered prompt composition
          2. Qwen inference via LLM Gateway
          3. Structured Pydantic validation & repair loop
          4. XAI Visual Story Engine mapping
        Returns tuple of (AdvisoryOutputSchema, XAIExplanationPayload).
        """
        messages = LayeredPromptBuilder.build_chat_messages(
            compact_context=compact_context,
            user_query=user_query,
        )

        gw_resp = self.gateway.chat(messages, temperature=0.0, json_mode=True)
        validator = StructuredOutputValidator(AdvisoryOutputSchema)

        repair_attempts = [0]

        def _repair_callback(repair_prompt: str) -> str:
            repair_attempts[0] += 1
            repair_messages = list(messages) + [
                {"role": "user", "content": repair_prompt}
            ]
            resp = self.gateway.chat(repair_messages, temperature=0.0, json_mode=True)
            return resp.content

        try:
            advisory = validator.parse_with_repair(
                raw_text=gw_resp.content,
                repair_callback=_repair_callback,
            )
            validation_passed = True
            error_str = None
        except StructuredOutputError as exc:
            validation_passed = False
            error_str = str(exc)
            logger.error(
                f"LLMAdapter: advisory generation failed: {exc}\n"
                f"RAW MODEL OUTPUT (truncated 800 chars): {gw_resp.content[:800]!r}"
            )
            raise

        finally:
            trace = LLMTraceRecord(
                run_id=run_id,
                objective_id=compact_context.get("objective", "OP01_PRODUCTION_DECLINE"),
                model_name=gw_resp.model,
                prompt_tokens=gw_resp.usage.prompt_tokens,
                completion_tokens=gw_resp.usage.completion_tokens,
                total_tokens=gw_resp.usage.total_tokens,
                latency_ms=gw_resp.latency_ms,
                is_mock=gw_resp.is_mock,
                validation_passed=validation_passed,
                repair_attempts=repair_attempts[0],
                error=error_str,
            )
            tracer.record_trace(trace)
            # Expose the trace of THIS specific call on the instance so callers (e.g.
            # graph.py's generate_advisory_draft_node) can read the real is_mock/model_name
            # verdict for the call that actually produced this advisory's text, instead of
            # re-probing gateway.is_available() afterward — which checks current server
            # health, not whether THIS call was live or mock (a real gap if the server
            # blips mid-request and recovers before the re-probe runs).
            self.last_trace = trace

        # Build XAI visual story explanation
        xai_explanation = self.xai_builder.build(advisory, compact_context)

        return advisory, xai_explanation

    def tool_call(
        self,
        prompt: str,
        tools: List[Dict[str, Any]],
        run_id: str = "RUN-001",
    ) -> ToolCallSchema:
        """
        Request Qwen to emit a JSON tool call structure.
        """
        tools_str = json.dumps(tools, indent=2)
        full_prompt = (
            f"You are a tool execution planner.\n"
            f"Available Tools:\n{tools_str}\n\n"
            f"User Request: {prompt}\n\n"
            f"Respond strictly with a JSON object matching:\n"
            f'{{"tool": "<name>", "arguments": {{...}}}}\n'
        )

        return self.structured_generate(
            prompt=full_prompt,
            schema=ToolCallSchema,
            run_id=run_id,
        )

    def classify(
        self,
        text: str,
        categories: List[str],
        run_id: str = "RUN-001",
    ) -> ClassificationResult:
        """
        Classify input text into one of the allowed categories.
        """
        cats_str = ", ".join(f'"{c}"' for c in categories)
        prompt = (
            f"Classify the following text into exactly one of these categories: [{cats_str}].\n"
            f"Text: {text}\n\n"
            f'Respond with JSON: {{"category": "<category>", "confidence": <float>, "reasoning": "<short explanation>"}}\n'
        )

        schema_res = self.structured_generate(
            prompt=prompt,
            schema=ClassificationSchema,
            run_id=run_id,
        )

        return ClassificationResult(
            category=schema_res.category,
            confidence=schema_res.confidence,
            reasoning=schema_res.reasoning,
        )

    def summarize(
        self,
        context: Dict[str, Any],
        max_words: int = 50,
        run_id: str = "RUN-001",
    ) -> str:
        """
        Summarize a complex operational context into concise natural language.
        """
        ctx_str = json.dumps(context, indent=2)
        prompt = (
            f"Summarize the following operational context in under {max_words} words:\n"
            f"{ctx_str}\n"
        )
        gen = self.generate(prompt=prompt, run_id=run_id)
        return gen.content.strip()
