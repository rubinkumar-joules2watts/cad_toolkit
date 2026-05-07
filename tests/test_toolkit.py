"""
Tests for the CAD Toolkit executor and registry.
Run with: pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from core.executor import execute, execute_batch
from core.registry_loader import load_registry, get_macro, list_macros


# ── Registry tests ─────────────────────────────────────────────────────────

def test_registry_loads():
    registry = load_registry()
    assert len(registry.macros) > 0

def test_registry_has_required_macros():
    registry = load_registry()
    ids = [m.id for m in registry.macros]
    assert "bom_export" in ids
    assert "standards_check" in ids
    assert "rgco_comparison" in ids

def test_get_macro_found():
    registry = load_registry()
    macro = get_macro(registry, "bom_export")
    assert macro.id == "bom_export"
    assert macro.entry == "run"

def test_get_macro_not_found():
    registry = load_registry()
    with pytest.raises(ValueError, match="not found"):
        get_macro(registry, "nonexistent_macro")

def test_list_macros_grouped():
    registry = load_registry()
    grouped = list_macros(registry)
    assert isinstance(grouped, dict)
    assert "Export" in grouped or "Validation" in grouped


# ── Executor tests ──────────────────────────────────────────────────────────

def test_execute_bom_export():
    result = execute("bom_export", {"assembly_name": "ENGINE_BLOCK_v3"})
    assert result.success is True
    assert result.output["total_parts"] == 10
    assert "file" in result.output

def test_execute_bom_export_gearbox():
    result = execute("bom_export", {"assembly_name": "GEARBOX_ASSY"})
    assert result.success is True
    assert result.output["total_parts"] == 5

def test_execute_bom_export_invalid_assembly():
    result = execute("bom_export", {"assembly_name": "FAKE_ASSEMBLY"})
    assert result.success is False
    assert "not found" in result.error

def test_execute_standards_check_pass():
    result = execute("standards_check", {"drawing_name": "DRW-GEARBOX-002"})
    assert result.success is True
    assert result.output["overall"] == "PASS"

def test_execute_standards_check_fail():
    result = execute("standards_check", {"drawing_name": "DRW-ENGINE-001"})
    assert result.success is True
    assert result.output["overall"] == "FAIL"
    assert result.output["errors"] > 0

def test_execute_rgco_comparison_changes():
    result = execute("rgco_comparison", {
        "part_name": "PN-001", "revision_a": "B", "revision_b": "C"
    })
    assert result.success is True
    assert result.output["total_changes"] > 0
    assert result.output["overall"] == "CHANGES DETECTED"

def test_execute_rgco_comparison_no_changes():
    result = execute("rgco_comparison", {
        "part_name": "PN-001", "revision_a": "A", "revision_b": "B"
    })
    assert result.success is True
    assert result.output["total_changes"] == 0

def test_execute_layer_audit():
    result = execute("layer_audit", {"drawing_name": "DRW-ENGINE-001"})
    assert result.success is True
    assert result.output["violations"] > 0

def test_execute_batch_rename():
    result = execute("batch_rename", {
        "prefix": "REV_", "suffix": "_2024", "target_category": "Automation"
    })
    assert result.success is True
    assert result.output["renamed_count"] == 3
    assert result.output["renamed"][0]["renamed"].startswith("REV_")

def test_execute_unknown_macro():
    result = execute("does_not_exist", {})
    assert result.success is False
    assert "not found" in result.error

def test_execute_batch():
    ids = ["bom_export", "standards_check", "layer_audit"]
    params = {
        "bom_export": {"assembly_name": "ENGINE_BLOCK_v3"},
        "standards_check": {"drawing_name": "DRW-ENGINE-001"},
        "layer_audit": {"drawing_name": "DRW-ENGINE-001"},
    }
    results = execute_batch(ids, params)
    assert len(results) == 3
    assert all(r.success for r in results)

def test_result_has_duration():
    result = execute("bom_export", {"assembly_name": "ENGINE_BLOCK_v3"})
    assert result.duration_ms > 0
