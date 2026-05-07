"""
Batch Rename Macro
-------------------
Applies prefix/suffix rules to a set of parts by category.
"""

from datetime import datetime
from pathlib import Path
from core.logger import logger

MOCK_PARTS = {
    "Export":     ["housing_v1", "shaft_01", "bearing_assy"],
    "Validation": ["drw_engine_front", "drw_gearbox_top"],
    "Automation": ["template_base", "frame_weld", "bracket_left"],
}


def run(params: dict) -> dict:
    prefix          = params.get("prefix", "")
    suffix          = params.get("suffix", "")
    target_category = params.get("target_category", "Automation")

    logger.info(f"Batch rename: category={target_category}, prefix='{prefix}', suffix='{suffix}'")

    parts = MOCK_PARTS.get(target_category)
    if parts is None:
        raise ValueError(f"Category '{target_category}' not found. Available: {list(MOCK_PARTS.keys())}")

    renamed = []
    for part in parts:
        new_name = f"{prefix}{part}{suffix}" if (prefix or suffix) else part
        renamed.append({"original": part, "renamed": new_name})

    output_path = Path(f"outputs/BatchRename_{target_category}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    with open(output_path, "w") as f:
        f.write(f"BATCH RENAME REPORT\n{'='*40}\n")
        f.write(f"Category : {target_category}\n")
        f.write(f"Prefix   : '{prefix}' | Suffix: '{suffix}'\n")
        f.write(f"Parts    : {len(renamed)}\n\n")
        for r in renamed:
            f.write(f"  {r['original']:<30} →  {r['renamed']}\n")

    logger.success(f"Batch rename complete: {len(renamed)} parts renamed")
    return {"category": target_category, "renamed_count": len(renamed),
            "renamed": renamed, "report_file": str(output_path)}
