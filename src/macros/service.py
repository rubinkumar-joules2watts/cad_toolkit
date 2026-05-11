from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from core.executor import execute
from core.registry_loader import load_registry


RESULT_TYPES = {
    "bom_export": "table_report",
    "rgco_comparison": "3d_comparison",
    "standards_check": "validation_report",
    "layer_audit": "validation_report",
    "batch_rename": "preview_table",
}


def list_macro_definitions() -> dict[str, Any]:
    registry = load_registry()
    macros = [
        {
            "id": macro.id,
            "label": macro.label,
            "category": macro.category,
            "platform": macro.platform,
            "description": macro.description,
            "params": macro.params,
        }
        for macro in registry.macros
    ]

    categories: dict[str, list[dict[str, Any]]] = {}
    for macro in macros:
        categories.setdefault(macro["category"], []).append(macro)

    return {
        "count": len(macros),
        "macros": macros,
        "categories": categories,
    }


def _summary_for(macro_id: str, output: dict[str, Any]) -> dict[str, Any]:
    if macro_id == "bom_export":
        return {
            "assembly": output.get("assembly"),
            "total_parts": output.get("total_parts"),
            "total_weight_kg": output.get("total_weight_kg"),
        }
    if macro_id == "rgco_comparison":
        return {
            "part": output.get("part"),
            "revision_a": output.get("revision_a"),
            "revision_b": output.get("revision_b"),
            "overall": output.get("overall"),
            "total_changes": output.get("total_changes"),
            "modified": output.get("modified"),
            "added": output.get("added"),
            "removed": output.get("removed"),
        }
    if macro_id in {"standards_check", "layer_audit"}:
        return {
            "overall": output.get("overall"),
            "drawing": output.get("drawing"),
            "errors": output.get("errors"),
            "warnings": output.get("warnings"),
            "violations": output.get("violations"),
        }
    if macro_id == "batch_rename":
        return {
            "category": output.get("category"),
            "renamed_count": output.get("renamed_count"),
        }
    return {}


def _data_for(macro_id: str, output: dict[str, Any]) -> dict[str, Any]:
    if macro_id == "bom_export":
        return {"table": output.get("table")}
    if macro_id == "rgco_comparison":
        return {
            "changes": output.get("changes", []),
            "comparison_views": output.get("comparison_views"),
            "execution": output.get("execution"),
        }
    if macro_id == "batch_rename":
        return {
            "table": {
                "columns": [
                    {"key": "original", "label": "Original"},
                    {"key": "renamed", "label": "Renamed"},
                ],
                "rows": output.get("renamed", []),
            }
        }
    return {
        key: value
        for key, value in output.items()
        if key not in {"report", "viewer", "report_file", "file"}
    }


def _normalize_success_response(result) -> dict[str, Any]:
    output = result.output if isinstance(result.output, dict) else {"value": result.output}
    macro_id = result.macro_id

    return {
        "macro_id": macro_id,
        "success": result.success,
        "result_type": RESULT_TYPES.get(macro_id, "report"),
        "duration_ms": result.duration_ms,
        "metadata": result.metadata,
        "summary": _summary_for(macro_id, output),
        "data": _data_for(macro_id, output),
        "viewer": output.get("viewer"),
        "report": output.get("report"),
        "output": output,
    }


def execute_macro(macro_id: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    api_params = dict(params or {})
    api_params["_persist_report"] = False
    api_params["_include_report"] = True

    result = execute(macro_id, api_params)
    if not result.success:
        status_code = 404 if "not found" in (result.error or "").lower() else 400
        raise HTTPException(
            status_code=status_code,
            detail={
                "macro_id": macro_id,
                "success": False,
                "error": result.error,
                "duration_ms": result.duration_ms,
            },
        )

    return _normalize_success_response(result)
