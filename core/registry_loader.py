import json
from pathlib import Path
from typing import Dict, List
from core.logger import logger


try:
    from pydantic import BaseModel, field_validator  # type: ignore

    class MacroEntry(BaseModel):
        id: str
        label: str
        category: str
        platform: str
        path: str
        entry: str
        description: str
        params: Dict[str, str]

        @field_validator("path")
        @classmethod
        def path_must_exist(cls, v):
            if not Path(v).exists():
                raise ValueError(f"Macro file not found: {v}")
            return v

    class MacroRegistry(BaseModel):
        macros: List[MacroEntry]

except ModuleNotFoundError:
    # Fallback: minimal validation without pydantic.
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class MacroEntry:
        id: str
        label: str
        category: str
        platform: str
        path: str
        entry: str
        description: str
        params: Dict[str, str]

        def __post_init__(self):
            if not Path(self.path).exists():
                raise ValueError(f"Macro file not found: {self.path}")

    @dataclass(frozen=True)
    class MacroRegistry:
        macros: List[MacroEntry]


def load_registry(registry_path: str = "registry/macros.json") -> MacroRegistry:
    path = Path(registry_path)
    if not path.exists():
        raise FileNotFoundError(f"Registry not found at: {registry_path}")

    raw = path.read_text()
    data = json.loads(raw)
    macros = [MacroEntry(**m) for m in data.get("macros", [])]
    registry = MacroRegistry(macros=macros)  # type: ignore[arg-type]
    logger.info(f"Registry loaded — {len(registry.macros)} macros found")
    return registry


def get_macro(registry: MacroRegistry, macro_id: str) -> MacroEntry:
    for macro in registry.macros:
        if macro.id == macro_id:
            return macro
    available = [m.id for m in registry.macros]
    raise ValueError(f"Macro '{macro_id}' not found. Available: {available}")


def list_macros(registry: MacroRegistry) -> Dict[str, List[MacroEntry]]:
    """Returns macros grouped by category."""
    grouped: Dict[str, List[MacroEntry]] = {}
    for macro in registry.macros:
        grouped.setdefault(macro.category, []).append(macro)
    return grouped
