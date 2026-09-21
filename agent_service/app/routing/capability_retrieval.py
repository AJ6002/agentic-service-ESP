from app.contracts.routing import CandidateTool
from app.routing.objective_registry import list_objectives

DEFAULT_TOOLS = [
    "get_live_telemetry",
    "get_asset_context",
    "get_historian_window",
    "search_knowledge",
]

def retrieve_candidates(query: str, top_k: int = 5) -> tuple[list[str], list[str], list[CandidateTool]]:
    """
    Retrieves candidate objectives and tools.
    In Slice 1, loaded from the objective manifest registry.
    Real embedding retrieval is added in Slice 2.
    """
    objectives = list_objectives()
    if not objectives:
        objectives = [
            "OP07_GENERAL_INQUIRY",
            "OP01_CURRENT_STATUS",
            "OP03_FAULT_DIAGNOSIS",
        ]

    candidates = [
        CandidateTool(tool=t, score=round(0.95 - (i * 0.05), 2))
        for i, t in enumerate(DEFAULT_TOOLS[:top_k])
    ]
    return objectives, DEFAULT_TOOLS, candidates
