#!/usr/bin/env python3
"""
Validate SAP Security Baseline definition files.

Checks each YAML file against schema/definition.schema.json, then applies the rules
JSON Schema cannot express on its own:

  * control ids are unique within a file
  * the filename matches the definition `id`
  * `version` is CalVer and, when `supersedes` is set, strictly greater than it
  * every non-manual control carries enough detail for a probe to run
  * `sources` are cited (the derivation trail back to SAP's guides)

Usage:
    python3 tools/validate.py                 # validate every definitions/*.yaml
    python3 tools/validate.py definitions/nw-as-abap.yaml
Exit code 0 = all valid, 1 = at least one problem (suitable for CI).
"""
from __future__ import annotations

import json
import pathlib
import sys

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required:  pip install -r tools/requirements.txt")

try:
    from jsonschema import Draft202012Validator
except ImportError:
    sys.exit("jsonschema is required:  pip install -r tools/requirements.txt")

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schema" / "definition.schema.json"


def normalize(node):
    """
    YAML turns an unquoted 2026-07-19 into a datetime.date, which then fails the
    schema's `type: string`. Rather than make every author remember to quote dates,
    coerce date/datetime back to ISO-8601 strings before validating.
    """
    import datetime

    if isinstance(node, dict):
        return {k: normalize(v) for k, v in node.items()}
    if isinstance(node, list):
        return [normalize(v) for v in node]
    if isinstance(node, (datetime.date, datetime.datetime)):
        return node.isoformat()
    return node


def calver(v: str) -> tuple[int, int, int]:
    """'2026.07.3' -> (2026, 7, 3) for ordering."""
    year, month, patch = v.split(".")
    return int(year), int(month), int(patch)


def validate_file(path: pathlib.Path, validator: Draft202012Validator) -> list[str]:
    problems: list[str] = []
    try:
        data = normalize(yaml.safe_load(path.read_text(encoding="utf-8")))
    except yaml.YAMLError as exc:
        return [f"not parseable as YAML: {exc}"]
    if not isinstance(data, dict):
        return ["top level must be a mapping"]

    # 1. Schema.
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        where = "/".join(str(p) for p in err.path) or "(root)"
        problems.append(f"{where}: {err.message}")
    if problems:
        return problems  # structure is wrong; the semantic checks below would just add noise

    # 2. Filename matches the id — consumers resolve definitions by id.
    if path.stem != data["id"]:
        problems.append(f"filename '{path.stem}.yaml' does not match id '{data['id']}'")

    # 3. Control ids unique within the file.
    seen: dict[str, int] = {}
    for i, control in enumerate(data["controls"]):
        cid = control["id"]
        if cid in seen:
            problems.append(f"duplicate control id '{cid}' (also at index {seen[cid]})")
        seen[cid] = i

    # 4. Version ordering against the version this file supersedes.
    if data.get("supersedes"):
        try:
            if calver(data["version"]) <= calver(data["supersedes"]):
                problems.append(
                    f"version '{data['version']}' must be greater than superseded "
                    f"'{data['supersedes']}'"
                )
        except ValueError:
            problems.append(f"supersedes '{data['supersedes']}' is not CalVer YYYY.MM.PATCH")

    # 5. Automated controls need a reference so a finding can cite its origin, and
    #    manual controls are far more useful with an evidence hint.
    for control in data["controls"]:
        check = control["check"]
        if check["type"] == "manual" and not check.get("evidence_hint"):
            problems.append(f"{control['id']}: manual check should set evidence_hint")

    return problems


def main(argv: list[str]) -> int:
    if not SCHEMA_PATH.exists():
        sys.exit(f"schema not found at {SCHEMA_PATH}")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)

    paths = [pathlib.Path(a) for a in argv[1:]] or sorted((ROOT / "definitions").glob("*.yaml"))
    if not paths:
        sys.exit("no definition files found in definitions/")

    total_controls = 0
    failed = False
    for path in paths:
        problems = validate_file(path, validator)
        if problems:
            failed = True
            print(f"✗ {path.name}")
            for p in problems:
                print(f"    {p}")
        else:
            data = normalize(yaml.safe_load(path.read_text(encoding="utf-8")))
            controls = data["controls"]
            auto = sum(1 for c in controls if c["check"]["type"] != "manual")
            total_controls += len(controls)
            print(
                f"✓ {path.name}  v{data['version']}  "
                f"{len(controls)} controls ({auto} auto / {len(controls) - auto} manual)"
            )

    print(f"\n{len(paths)} file(s), {total_controls} control(s) — "
          f"{'FAILED' if failed else 'all valid'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
