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

    output_path = Path(f"outputs/LayerAudit_{drawing_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    with open(output_path, "w") as f:
        f.write(f"LAYER AUDIT REPORT — {drawing_name}\n{'='*40}\n")
        f.write(f"Valid: {len(valid)} | Violations: {len(violations)}\n\n")
        if violations:
            f.write("VIOLATIONS:\n")
            for v in violations:
                f.write(f"  '{v['layer']}' — {v['issue']}\n")
        f.write("\nVALID LAYERS:\n")
        for l in valid:
            f.write(f"  {l}\n")

    logger.success(f"Layer audit complete: {len(violations)} violations")
    return {"drawing": drawing_name, "valid": len(valid),
            "violations": len(violations), "details": violations, "report_file": str(output_path)}
