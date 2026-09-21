import re
from pathlib import Path
from typing import Optional
import yaml

_CANONICAL_WELLS: list[str] | None = None
_CANONICAL_PARSED: list[dict] | None = None

WELL_PARSER_REGEX = re.compile(r"^([A-Za-z]+)-0*(\d+)(?:-([A-Za-z0-9]+))?$", re.IGNORECASE)


def _load_canonical_wells() -> list[str]:
    global _CANONICAL_WELLS, _CANONICAL_PARSED
    if _CANONICAL_WELLS is not None:
        return _CANONICAL_WELLS

    base_dir = Path(__file__).resolve().parent.parent.parent
    path = base_dir / "config" / "wells_canonical.yaml"
    wells = []
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            for item in data.get("wells", []):
                wells.append(item.get("id"))

    # Fallback to hardcoded list if YAML failed to load
    if not wells:
        wells = [
            "FNW-01", "FS-17", "FS-121", "FNW-06", "FWS-06",
            "ULFA-5", "FS-96", "FS-21", "FS-06", "FS-91",
            "FSWS-001-A", "FS-014", "FS-016", "FS-031",
        ]

    _CANONICAL_WELLS = wells

    parsed = []
    for w in wells:
        m = WELL_PARSER_REGEX.match(w)
        if m:
            prefix, num, suffix = m.groups()
            parsed.append({
                "canonical": w,
                "prefix": prefix.upper(),
                "num": int(num),
                "suffix": suffix.upper() if suffix else None,
            })
        else:
            parsed.append({
                "canonical": w,
                "prefix": w.upper(),
                "num": None,
                "suffix": None,
            })
    _CANONICAL_PARSED = parsed

    return _CANONICAL_WELLS


def list_canonical_wells() -> list[str]:
    return list(_load_canonical_wells())


def is_canonical(well_id: str) -> bool:
    if not well_id:
        return False
    wells = _load_canonical_wells()
    return well_id.strip().upper() in {w.upper() for w in wells}


def normalize_well_id(text: str) -> Optional[str]:
    """
    Normalizes well reference to canonical format using numeric equivalence.
    Examples:
      'FS-017' -> 'FS-17'
      'FS-14'  -> 'FS-014'
      'FSWS-001-A' -> 'FSWS-001-A'
      'FWS-04' -> None (does not exist, only FWS-06 exists)
    """
    if not text or not isinstance(text, str):
        return None

    raw = text.strip().upper()
    _load_canonical_wells()

    # 1. Exact canonical hit
    for w in _CANONICAL_WELLS:
        if raw == w.upper():
            return w

    # 2. Parse prefix and number for numeric-equivalence lookup
    m = WELL_PARSER_REGEX.match(raw)
    if not m:
        return None

    prefix, num_str, suffix = m.groups()
    prefix = prefix.upper()
    num = int(num_str)
    suffix = suffix.upper() if suffix else None

    for entry in _CANONICAL_PARSED:
        if (
            entry["prefix"] == prefix
            and entry["num"] == num
            and entry["suffix"] == suffix
        ):
            return entry["canonical"]

    return None
