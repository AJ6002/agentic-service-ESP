"""
LLM Layer Architecture Module — Phase 10
Grounded in ESP APM LLM Architecture Design
"""

from src.llm.gateway import LLMGateway, LLMGatewayResponse, LLMUsage
from src.llm.context_builder import CompactContextBuilder
from src.llm.prompts import LayeredPromptBuilder, SYSTEM_PROMPT, ESP_DOMAIN_RULES
from src.llm.structured_output import (
    StructuredOutputValidator,
    StructuredOutputError,
    AdvisoryOutputSchema,
    ToolCallSchema,
    ClassificationSchema,
    HypothesisSchema,
)
from src.llm.xai_builder import XAIVisualStoryBuilder, XAIExplanationPayload, VisualSpec
from src.llm.observability import LLMObservabilityTracer, LLMTraceRecord, tracer
from src.llm.adapter import LLMAdapter, LLMGenerationResponse, ClassificationResult

__all__ = [
    "LLMGateway",
    "LLMGatewayResponse",
    "LLMUsage",
    "CompactContextBuilder",
    "LayeredPromptBuilder",
    "SYSTEM_PROMPT",
    "ESP_DOMAIN_RULES",
    "StructuredOutputValidator",
    "StructuredOutputError",
    "AdvisoryOutputSchema",
    "ToolCallSchema",
    "ClassificationSchema",
    "HypothesisSchema",
    "XAIVisualStoryBuilder",
    "XAIExplanationPayload",
    "VisualSpec",
    "LLMObservabilityTracer",
    "LLMTraceRecord",
    "tracer",
    "LLMAdapter",
    "LLMGenerationResponse",
    "ClassificationResult",
]
