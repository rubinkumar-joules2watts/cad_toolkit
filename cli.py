"""
CAD Toolkit CLI
--------------
Trigger any registered macro by ID from the command line.

This version uses only Python's standard library so it can run in minimal
environments where `typer` / `rich` aren't installed.
"""

from __future__ import annotations

import argparse
import json
import sys

from core.executor import execute, execute_batch
from core.registry_loader import load_registry, list_macros


def _parse_params(params_str: str) -> dict:
    if not params_str:
        return {}
    try:
        data = json.loads(params_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid params JSON: {e}") from e
    if not isinstance(data, dict):
        raise ValueError("`--params` must be a JSON object (e.g. '{\"key\": \"value\"}').")
    return data


def _cmd_run(macro_id: str, params_str: str) -> int:
    parsed_params = _parse_params(params_str)
    result = execute(macro_id, parsed_params)

    if result.success:
        print(f"✓ SUCCESS — {result.duration_ms:.0f}ms")
        print(json.dumps(result.output, indent=2))
        return 0

    print(f"✗ FAILED — {result.error}")
    return 1


def _cmd_list() -> int:
    registry = load_registry()
    grouped = list_macros(registry)

    for category in sorted(grouped.keys()):
        print(category)
        for m in grouped[category]:
            print(f"  {m.id:20} | {m.label:28} | {m.platform:10} | {m.description}")
        print()
    return 0


def _cmd_batch() -> int:
    print("Batch Smoke Test — All Macros")

    default_params = {
        "bom_export":       {"assembly_name": "ENGINE_BLOCK_v3", "output_format": "xlsx"},
        "standards_check":  {"drawing_name": "DRW-ENGINE-001"},
        "rgco_comparison":  {"part_name": "PN-001", "revision_a": "B", "revision_b": "C"},
        "layer_audit":      {"drawing_name": "DRW-ENGINE-001"},
        "batch_rename":     {"prefix": "REV_", "suffix": "", "target_category": "Automation"},
    }

    registry = load_registry()
    macro_ids = [m.id for m in registry.macros]
    results = execute_batch(macro_ids, default_params)

    for r in results:
        status = "PASS" if r.success else "FAIL"
        summary = str(r.output)[:60] if r.success else str(r.error)[:60]
        print(f"{r.macro_id:18} {status:4} {r.duration_ms:.0f}ms {summary}")

    passed = sum(1 for r in results if r.success)
    print(f"\n{passed}/{len(results)} macros passed")
    return 0 if passed == len(results) else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CAD Macro Toolkit — run engineering macros from the command line")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_p = subparsers.add_parser("run", help="Run a single macro by its ID")
    run_p.add_argument("macro_id", help="Macro ID (from registry)")
    run_p.add_argument("--params", "-p", default="{}", help="JSON string of input params")

    subparsers.add_parser("list", help="List all registered macros grouped by category")
    subparsers.add_parser("batch", help="Run all registered macros with default params (smoke test)")

    args = parser.parse_args(argv)

    if args.command == "run":
        return _cmd_run(args.macro_id, args.params)
    if args.command == "list":
        return _cmd_list()
    if args.command == "batch":
        return _cmd_batch()
    raise RuntimeError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
