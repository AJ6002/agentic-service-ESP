from typing import Literal

Route = Literal["SIMPLE", "WORKFLOW", "FOLLOW_UP"]
AssetSource = Literal["EXPLICIT", "RESOLVED", "SESSION", "UI", "UNRESOLVED"]
TimeSource = Literal["EXPLICIT", "UI", "SESSION", "DEFAULT"]
TimeRangeLabel = Literal["last_1h", "last_6h", "last_24h", "last_7d", "last_30d"]
Resolution = Literal["NEW", "BIND", "SUPERSEDE", "META"]
Scope = Literal["ASSET", "MULTI_ASSET", "FLEET", "GLOBAL"]
SafetyClass = Literal["READ", "WRITE"]
CallKind = Literal["READ", "WRITE"]
CallStatus = Literal["PENDING", "OK", "FAILED", "TIMEOUT", "SKIPPED"]
RunStatus = Literal["RUNNING", "PAUSED", "DONE", "ABANDONED", "FAILED", "INSUFFICIENT"]
InterruptType = Literal["CLARIFY", "INSUFFICIENT", "APPROVE"]
ResumeAt = Literal["CONTEXT", "ROUTER", "PLAN_BUILD", "SEAL_CHECK", "GAP_FILL", "WRITE"]
AdapterStatus = Literal["AVAILABLE", "DEGRADED", "ABSENT", "SIMULATED"]
DecisionAction = Literal["APPROVE", "REJECT", "MODIFY"]
FrameType = Literal[
    "status",
    "text_delta",
    "evidence",
    "clarification",
    "interrupt",
    "visual",
    "advisory",
    "error",
    "done",
]
MatchMethod = Literal["EXACT_ID", "ALIAS", "PRONOUN", "NONE"]
