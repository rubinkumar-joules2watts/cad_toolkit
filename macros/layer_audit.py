"""
Layer Audit Macro
------------------
Audits all layer names in a drawing against approved naming conventions.
"""

from datetime import datetime
from pathlib import Path
from core.logger import logger

MOCK_DRAWINGS = {
    "DRW-ENGINE-001": ["GEOMETRY", "DIMENSIONS", "HIDDEN", "CENTERLINES", "notes", "BoundingBox", "SYMBOLS"],
    "DRW-GEARBOX-002": ["GEOMETRY", "DIMENSIONS", "HIDDEN", "CENTERLINES", "NOTES", "HATCHING"],
}

APPROVED_LAYERS = {"GEOMETRY", "DIMENSIONS", "HIDDEN", "CENTERLINES", "NOTES",
                   "HATCHING", "BORDERS", "SYMBOLS", "CONSTRUCTION", "ANNOTATIONS"}


def run(params: dict) -> dict:
    drawing_name = params.get("drawing_name", "DRW-ENGINE-001")
    persist_report = params.get("_persist_report", True)
    include_report = params.get("_include_report", False)
    logger.info(f"Layer audit started: {drawing_name}")

    layers = MOCK_DRAWINGS.get(drawing_name)
    if not layers:
        raise ValueError(f"Drawing '{drawing_name}' not found.")

    violations, valid = [], []
    for layer in layers:
        if layer.upper() != layer:
            violations.append({"layer": layer, "issue": "Not uppercase"})
        elif layer not in APPROVED_LAYERS:
            violations.append({"layer": layer, "issue": "Not in approved list"})
        else:
            valid.append(layer)

    report_lines = [
        f"LAYER AUDIT REPORT — {drawing_name}",
        "=" * 40,
        f"Valid: {len(valid)} | Violations: {len(violations)}",
        "",
    ]
    if violations:
        report_lines.append("VIOLATIONS:")
        for v in violations:
            report_lines.append(f"  '{v['layer']}' — {v['issue']}")
    report_lines.append("")
    report_lines.append("VALID LAYERS:")
    for layer in valid:
        report_lines.append(f"  {layer}")

    report_content = "\n".join(report_lines) + "\n"
    filename = f"LayerAudit_{drawing_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    output_path = Path("outputs") / filename
    if persist_report:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report_content)

    logger.success(f"Layer audit complete: {len(violations)} violations")
    output = {"drawing": drawing_name, "valid": len(valid),
              "violations": len(violations), "details": violations,
              "report_file": str(output_path) if persist_report else None}

    if include_report:
        output["report"] = {
            "filename": filename,
            "media_type": "text/plain",
            "encoding": "utf-8",
            "content": report_content,
        }

    return output
