"""
RGCO Overlay Comparison Macro
------------------------------
Simulates a Red/Green Comparison Overlay between two revisions of a part.
Diffs geometry attributes, dimensions, and material specs.

In real NX/CATIA: load two part files via API, extract geometry data,
compare face counts, body volumes, key dimensions, and attribute values.
"""

from pathlib import Path
from datetime import datetime
from core.logger import logger


# Mock part revision database
MOCK_PARTS = {
    "PN-001": {
        "A": {
            "volume_mm3": 48200.0,
            "surface_area_mm2": 18400.0,
            "faces": 24,
            "material": "Cast Iron",
            "mass_kg": 44.8,
            "dimensions": {"length": 480, "width": 220, "height": 310},
            "tolerances": {"bore_dia": "±0.02", "flatness": "0.05"},
            "holes": 12,
            "threads": 8
        },
        "B": {
            "volume_mm3": 48200.0,
            "surface_area_mm2": 18400.0,
            "faces": 24,
            "material": "Cast Iron",
            "mass_kg": 44.8,
            "dimensions": {"length": 480, "width": 220, "height": 310},
            "tolerances": {"bore_dia": "±0.02", "flatness": "0.05"},
            "holes": 12,
            "threads": 8
        },
        "C": {
            "volume_mm3": 47850.0,          # Changed — lightweighting
            "surface_area_mm2": 18650.0,    # Changed — new ribbing
            "faces": 28,                    # Changed — 4 new faces from ribs
            "material": "Compacted Graphite Iron",  # Material change
            "mass_kg": 45.2,
            "dimensions": {"length": 480, "width": 220, "height": 310},
            "tolerances": {"bore_dia": "±0.015", "flatness": "0.04"},  # Tighter
            "holes": 12,
            "threads": 10                   # 2 new threads
        }
    },
    "GB-001": {
        "A": {
            "volume_mm3": 22400.0,
            "surface_area_mm2": 14200.0,
            "faces": 18,
            "material": "Aluminium Die Cast",
            "mass_kg": 8.2,
            "dimensions": {"length": 320, "width": 180, "height": 210},
            "tolerances": {"shaft_bore": "±0.01"},
            "holes": 8,
            "threads": 6
        },
        "B": {
            "volume_mm3": 22400.0,
            "surface_area_mm2": 14200.0,
            "faces": 18,
            "material": "Aluminium Die Cast",
            "mass_kg": 8.5,                 # Weight changed
            "dimensions": {"length": 320, "width": 185, "height": 210},  # Width changed
            "tolerances": {"shaft_bore": "±0.01"},
            "holes": 10,                    # 2 new holes
            "threads": 6
        }
    }
}


def _diff_dicts(a: dict, b: dict, path: str = "") -> list:
    """Recursively diff two dicts, return list of change descriptions."""
    changes = []
    all_keys = set(a.keys()) | set(b.keys())
    for key in all_keys:
        full_key = f"{path}.{key}" if path else key
        if key not in a:
            changes.append({"field": full_key, "type": "ADDED", "old": None, "new": b[key]})
        elif key not in b:
            changes.append({"field": full_key, "type": "REMOVED", "old": a[key], "new": None})
        elif isinstance(a[key], dict) and isinstance(b[key], dict):
            changes += _diff_dicts(a[key], b[key], full_key)
        elif a[key] != b[key]:
            changes.append({"field": full_key, "type": "MODIFIED", "old": a[key], "new": b[key]})
    return changes


def run(params: dict) -> dict:
    part_name   = params.get("part_name", "PN-001")
    revision_a  = params.get("revision_a", "B")
    revision_b  = params.get("revision_b", "C")

    logger.info(f"RGCO Comparison: {part_name} Rev {revision_a} → Rev {revision_b}")

    part_data = MOCK_PARTS.get(part_name)
    if not part_data:
        raise ValueError(f"Part '{part_name}' not found. Available: {list(MOCK_PARTS.keys())}")

    rev_a = part_data.get(revision_a)
    rev_b = part_data.get(revision_b)

    if not rev_a:
        raise ValueError(f"Revision '{revision_a}' not found for part '{part_name}'")
    if not rev_b:
        raise ValueError(f"Revision '{revision_b}' not found for part '{part_name}'")

    changes = _diff_dicts(rev_a, rev_b)

    added    = [c for c in changes if c["type"] == "ADDED"]
    removed  = [c for c in changes if c["type"] == "REMOVED"]
    modified = [c for c in changes if c["type"] == "MODIFIED"]

    overall = "NO CHANGE" if not changes else "CHANGES DETECTED"

    # Write report
    output_path = Path(f"outputs/RGCO_{part_name}_Rev{revision_a}_vs_Rev{revision_b}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    with open(output_path, "w") as f:
        f.write(f"RGCO OVERLAY COMPARISON REPORT\n")
        f.write(f"{'='*50}\n")
        f.write(f"Part      : {part_name}\n")
        f.write(f"Comparing : Rev {revision_a}  →  Rev {revision_b}\n")
        f.write(f"Date      : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Result    : {overall}\n")
        f.write(f"Changes   : {len(changes)} ({len(modified)} modified, {len(added)} added, {len(removed)} removed)\n")
        f.write(f"{'='*50}\n\n")

        if modified:
            f.write("MODIFIED:\n")
            for c in modified:
                f.write(f"  {c['field']:<30} {str(c['old']):<20} →  {str(c['new'])}\n")

        if added:
            f.write("\nADDED:\n")
            for c in added:
                f.write(f"  {c['field']:<30} (new) {c['new']}\n")

        if removed:
            f.write("\nREMOVED:\n")
            for c in removed:
                f.write(f"  {c['field']:<30} was: {c['old']}\n")

        if not changes:
            f.write("No differences found between revisions.\n")

    logger.success(f"RGCO comparison complete: {len(changes)} changes found")

    return {
        "overall": overall,
        "part": part_name,
        "revision_a": revision_a,
        "revision_b": revision_b,
        "total_changes": len(changes),
        "modified": len(modified),
        "added": len(added),
        "removed": len(removed),
        "report_file": str(output_path),
        "changes": changes
    }
