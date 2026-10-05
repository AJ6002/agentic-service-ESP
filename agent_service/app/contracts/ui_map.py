"""UI Map Contract — Static Platform Self-Description Schema (V1).

Mirrors the TypeScript schema in esp-insight-suite (src/agent-dock/types/uiMap.ts)
and the YAML source of truth in docs/ui_map/ui_map.yaml.
"""
from typing import Literal, Optional
from pydantic import BaseModel, Field

UiMapType = Literal["route", "component", "concept", "navigation", "glossary"]
UiMapWorkspace = Literal["operations", "engineering", "single-well", "platform"]


class UiMapEntry(BaseModel):
    """A grounded self-description entry for an element of the platform interface."""

    id: str = Field(description="Stable dot-namespaced identifier (e.g. route.working-status)")
    type: UiMapType = Field(description="Classification enum")
    title: str = Field(description="Human-readable title")
    path: Optional[str] = Field(default=None, description="URL path - only present for routes")
    workspace: UiMapWorkspace = Field(description="Platform workspace domain")
    summary: str = Field(description="Single-sentence summary")
    description: str = Field(description="Full grounded explanation (100-300 words)")
    related: list[str] = Field(default_factory=list, description="Cross-references to other entry IDs")
    aliases: list[str] = Field(default_factory=list, description="Synonyms and user phrasing variations")
