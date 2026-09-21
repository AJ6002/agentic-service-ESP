"""
Loads versioned prompt files from app/llm/prompts/.

Prompts are plain .txt files, named {name}_v{n}.txt (or _v{n}_suffix.txt
for a variant, e.g. a strict-retry version of the same prompt). Keeping
them as files rather than string literals in .py files means:
  - a prompt change is a one-line diff, not buried inside router.py logic
  - multiple versions can coexist (router_v1.txt, router_v2.txt) during
    a rollout without branching code
  - non-engineers can review/edit prompt wording without touching Python
"""

from functools import lru_cache
from pathlib import Path

_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


@lru_cache(maxsize=32)
def load_prompt(filename: str) -> str:
    """
    Loads app/llm/prompts/{filename} and returns its contents, stripped.
    Cached — prompt files are read once per process, not per call.
    """
    path = _PROMPTS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()
