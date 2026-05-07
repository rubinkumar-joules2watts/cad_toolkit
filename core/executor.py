import importlib.util
import time
from dataclasses import dataclass, field
from typing import Any, Optional
from pathlib import Path

from core.logger import logger
from core.registry_loader import load_registry, get_macro


@dataclass
class MacroResult:
    macro_id: str
    success: bool
    output: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    metadata: dict = field(default_factory=dict)

    def __str__(self):
        status = "✓ SUCCESS" if self.success else "✗ FAILED"
        duration = f"{self.duration_ms:.0f}ms"
        if self.success:
            return f"[{status}] {self.macro_id} ({duration})\n  Output: {self.output}"
        return f"[{status}] {self.macro_id} ({duration})\n  Error: {self.error}"


def _load_module(path: str):
    """Dynamically loads a Python module from a file path."""
    abs_path = Path(path).resolve()
    spec = importlib.util.spec_from_file_location("macro_module", abs_path)
    if spec is None:
        raise ImportError(f"Cannot load module from: {abs_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def execute(macro_id: str, params: dict = {}) -> MacroResult:
    """
    Core executor. Resolves macro_id from registry,
    dynamically loads the module, calls run(params),
    returns a structured MacroResult.
    """
    registry = load_registry()
    start = time.time()

    try:
        macro = get_macro(registry, macro_id)
        logger.info(f"Running macro: [{macro.category}] {macro.label}")
        logger.debug(f"Params: {params}")

        module = _load_module(macro.path)

        if not hasattr(module, macro.entry):
            raise AttributeError(
                f"Macro '{macro_id}' has no entry function '{macro.entry}'"
            )

        entry_fn = getattr(module, macro.entry)
        output = entry_fn(params)

        duration_ms = (time.time() - start) * 1000
        logger.success(f"Macro '{macro_id}' completed in {duration_ms:.0f}ms")

        return MacroResult(
            macro_id=macro_id,
            success=True,
            output=output,
            duration_ms=duration_ms,
            metadata={"label": macro.label, "category": macro.category}
        )

    except Exception as e:
        duration_ms = (time.time() - start) * 1000
        logger.error(f"Macro '{macro_id}' failed after {duration_ms:.0f}ms — {e}")

        return MacroResult(
            macro_id=macro_id,
            success=False,
            error=str(e),
            duration_ms=duration_ms
        )


def execute_batch(macro_ids: list, params_map: dict = {}) -> list[MacroResult]:
    """
    Run multiple macros sequentially.
    params_map: { macro_id: params_dict }
    """
    results = []
    logger.info(f"Batch execution started — {len(macro_ids)} macros")
    for macro_id in macro_ids:
        params = params_map.get(macro_id, {})
        result = execute(macro_id, params)
        results.append(result)
    passed = sum(1 for r in results if r.success)
    logger.info(f"Batch complete — {passed}/{len(results)} passed")
    return results
