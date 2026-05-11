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
    persist_report = params.get("_persist_report", True)
    include_report = params.get("_include_report", False)

    logger.info(f"Batch rename: category={target_category}, prefix='{prefix}', suffix='{suffix}'")

    parts = MOCK_PARTS.get(target_category)
    if parts is None:
        raise ValueError(f"Category '{target_category}' not found. Available: {list(MOCK_PARTS.keys())}")

    renamed = []
    for part in parts:
        new_name = f"{prefix}{part}{suffix}" if (prefix or suffix) else part
        renamed.append({"original": part, "renamed": new_name})

    report_lines = [
        "BATCH RENAME REPORT",
        "=" * 40,
        f"Category : {target_category}",
        f"Prefix   : '{prefix}' | Suffix: '{suffix}'",
        f"Parts    : {len(renamed)}",
        "",
    ]
    for item in renamed:
        report_lines.append(f"  {item['original']:<30} →  {item['renamed']}")

    report_content = "\n".join(report_lines) + "\n"
    filename = f"BatchRename_{target_category}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    output_path = Path("outputs") / filename
    if persist_report:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report_content)

    logger.success(f"Batch rename complete: {len(renamed)} parts renamed")
    output = {"category": target_category, "renamed_count": len(renamed),
              "renamed": renamed, "report_file": str(output_path) if persist_report else None}

    if include_report:
        output["report"] = {
            "filename": filename,
            "media_type": "text/plain",
            "encoding": "utf-8",
            "content": report_content,
        }

    return output
