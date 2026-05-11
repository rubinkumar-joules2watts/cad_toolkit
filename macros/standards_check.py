"""
Drawing Standards Check Macro
------------------------------
Simulates validating a CAD drawing against company standards.
Checks title block fields, layer naming, annotation rules, GD&T usage.

In real NX/CATIA: replace MOCK_DRAWINGS with API calls to read
actual drawing sheets, annotations, and layer data.
"""

from dataclasses import dataclass
from typing import List
from pathlib import Path
from datetime import datetime
from core.logger import logger


@dataclass
class CheckResult:
    rule: str
    passed: bool
    message: str
    severity: str = "error"  # error | warning | info


# Mock drawing data — simulates what NX/CATIA drawing API returns
MOCK_DRAWINGS = {
    "DRW-ENGINE-001": {
        "title_block": {
            "drawn_by": "J. Smith",
            "checked_by": "",            # MISSING
            "part_number": "PN-001",
            "revision": "C",
            "date": "2024-01-15",
            "title": "Cylinder Block",
            "scale": "1:2",
            "units": "mm",
            "standard": "ISO"
        },
        "layers": ["GEOMETRY", "DIMENSIONS", "HIDDEN", "CENTERLINES", "notes", "BoundingBox"],
        "views": [
            {"name": "Front View",  "scale": "1:2", "has_dimensions": True},
            {"name": "Side View",   "scale": "1:2", "has_dimensions": True},
            {"name": "Section A-A", "scale": "1:1", "has_dimensions": False},  # No dims
        ],
        "annotations": {
            "total": 24,
            "gdt_symbols": 6,
            "surface_finish": 3,
            "notes": 4,
            "unattached": 2   # Floating annotations not attached to geometry
        },
        "tolerances_defined": True,
        "north_arrow": False
    },
    "DRW-GEARBOX-002": {
        "title_block": {
            "drawn_by": "A. Patel",
            "checked_by": "R. Kumar",
            "part_number": "GB-001",
            "revision": "B",
            "date": "2024-02-20",
            "title": "Gearbox Housing",
            "scale": "1:5",
            "units": "mm",
            "standard": "ISO"
        },
        "layers": ["GEOMETRY", "DIMENSIONS", "HIDDEN", "CENTERLINES", "NOTES", "HATCHING"],
        "views": [
            {"name": "Front View", "scale": "1:5", "has_dimensions": True},
            {"name": "Top View",   "scale": "1:5", "has_dimensions": True},
            {"name": "ISO View",   "scale": "1:5", "has_dimensions": False},
        ],
        "annotations": {
            "total": 18,
            "gdt_symbols": 4,
            "surface_finish": 2,
            "notes": 3,
            "unattached": 0
        },
        "tolerances_defined": True,
        "north_arrow": False
    }
}

VALID_LAYERS = {"GEOMETRY", "DIMENSIONS", "HIDDEN", "CENTERLINES", "NOTES", "HATCHING", "BORDERS", "SYMBOLS"}
REQUIRED_TITLE_FIELDS = ["drawn_by", "checked_by", "part_number", "revision", "date", "title", "scale", "units"]


def _check_title_block(title_block: dict) -> List[CheckResult]:
    results = []
    for field in REQUIRED_TITLE_FIELDS:
        val = title_block.get(field, "")
        if not val:
            results.append(CheckResult(
                rule=f"Title block: '{field}' must not be empty",
                passed=False,
                message=f"Field '{field}' is empty or missing",
                severity="error"
            ))
        else:
            results.append(CheckResult(
                rule=f"Title block: '{field}'",
                passed=True,
                message=f"'{field}' = '{val}'"
            ))
    return results


def _check_layers(layers: list) -> List[CheckResult]:
    results = []
    for layer in layers:
        if layer.upper() != layer:
            results.append(CheckResult(
                rule="Layer naming: must be UPPERCASE",
                passed=False,
                message=f"Layer '{layer}' is not uppercase",
                severity="error"
            ))
        elif layer not in VALID_LAYERS:
            results.append(CheckResult(
                rule="Layer naming: must be from approved list",
                passed=False,
                message=f"Layer '{layer}' not in approved list: {VALID_LAYERS}",
                severity="warning"
            ))
        else:
            results.append(CheckResult(
                rule=f"Layer '{layer}'",
                passed=True,
                message="Valid layer name"
            ))
    return results


def _check_views(views: list) -> List[CheckResult]:
    results = []
    for view in views:
        if not view["has_dimensions"] and "ISO" not in view["name"] and "Section" not in view["name"]:
            results.append(CheckResult(
                rule=f"View '{view['name']}': must have dimensions",
                passed=False,
                message=f"View '{view['name']}' has no dimensions",
                severity="warning"
            ))
        else:
            results.append(CheckResult(
                rule=f"View '{view['name']}'",
                passed=True,
                message=f"Scale {view['scale']}, dimensions present"
            ))
    return results


def _check_annotations(annotations: dict) -> List[CheckResult]:
    results = []
    if annotations["unattached"] > 0:
        results.append(CheckResult(
            rule="Annotations: no unattached annotations allowed",
            passed=False,
            message=f"{annotations['unattached']} unattached annotations found",
            severity="error"
        ))
    else:
        results.append(CheckResult(
            rule="Annotations: unattached check",
            passed=True,
            message="All annotations are attached to geometry"
        ))

    if annotations["gdt_symbols"] == 0:
        results.append(CheckResult(
            rule="Annotations: GD&T symbols required",
            passed=False,
            message="No GD&T symbols found in drawing",
            severity="warning"
        ))
    else:
        results.append(CheckResult(
            rule="Annotations: GD&T symbols",
            passed=True,
            message=f"{annotations['gdt_symbols']} GD&T symbols present"
        ))
    return results


def run(params: dict) -> dict:
    drawing_name = params.get("drawing_name", "DRW-ENGINE-001")
    persist_report = params.get("_persist_report", True)
    include_report = params.get("_include_report", False)
    logger.info(f"Standards check started for: {drawing_name}")

    drawing = MOCK_DRAWINGS.get(drawing_name)
    if not drawing:
        available = list(MOCK_DRAWINGS.keys())
        raise ValueError(f"Drawing '{drawing_name}' not found. Available: {available}")

    all_results: List[CheckResult] = []
    all_results += _check_title_block(drawing["title_block"])
    all_results += _check_layers(drawing["layers"])
    all_results += _check_views(drawing["views"])
    all_results += _check_annotations(drawing["annotations"])

    passed = [r for r in all_results if r.passed]
    errors = [r for r in all_results if not r.passed and r.severity == "error"]
    warnings = [r for r in all_results if not r.passed and r.severity == "warning"]

    overall = "PASS" if not errors else "FAIL"

    report_lines = [
        "CAD DRAWING STANDARDS CHECK REPORT",
        "=" * 50,
        f"Drawing  : {drawing_name}",
        f"Date     : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Result   : {overall}",
        f"Passed   : {len(passed)} | Errors: {len(errors)} | Warnings: {len(warnings)}",
        "=" * 50,
        "",
    ]

    if errors:
        report_lines.append("ERRORS:")
        for r in errors:
            report_lines.append(f"  [ERROR]   {r.rule}\n           → {r.message}")

    if warnings:
        report_lines.append("")
        report_lines.append("WARNINGS:")
        for r in warnings:
            report_lines.append(f"  [WARN]    {r.rule}\n           → {r.message}")

    report_lines.append("")
    report_lines.append("PASSED CHECKS:")
    for r in passed:
        report_lines.append(f"  [OK]      {r.rule}")

    report_content = "\n".join(report_lines) + "\n"
    filename = f"StandardsCheck_{drawing_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    output_path = Path("outputs") / filename
    if persist_report:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report_content)

    logger.success(f"Standards check complete: {overall} — {len(errors)} errors, {len(warnings)} warnings")

    output = {
        "overall": overall,
        "drawing": drawing_name,
        "passed": len(passed),
        "errors": len(errors),
        "warnings": len(warnings),
        "report_file": str(output_path) if persist_report else None,
        "error_details": [{"rule": r.rule, "message": r.message} for r in errors]
    }

    if include_report:
        output["report"] = {
            "filename": filename,
            "media_type": "text/plain",
            "encoding": "utf-8",
            "content": report_content,
        }

    return output
