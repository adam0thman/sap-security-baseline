#!/usr/bin/env python3
"""
Self-test for validate.py — proves the validator REJECTS malformed definitions.
A validator that only ever says "valid" is worse than none, so each case below is a
mistake a real author would plausibly make.

Run:  python3 tools/selftest.py     (exit 0 = all cases behaved as expected)
"""
from __future__ import annotations

import json
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from jsonschema import Draft202012Validator  # noqa: E402
from validate import validate_file  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
VALIDATOR = Draft202012Validator(json.loads((ROOT / "schema" / "definition.schema.json").read_text()))

GOOD = """
spec_version: "1.0"
id: probe-test
title: Fixture definition set
product: {key: NW_AS_ABAP, name: Test}
version: "2026.07.1"
released: 2026-07-19
sources:
  - {title: T, url: "https://help.sap.com/x", retrieved: 2026-07-19}
controls:
  - id: TEST-AUTHN-0001
    title: A sample control
    category: authentication
    severity: high
    rationale: Long enough rationale to satisfy the minimum length rule.
    check: {type: profile_parameter, parameter: login/min_password_lng, operator: gte, value: 8}
    remediation: Set the parameter.
"""

CASES: list[tuple[str, str, str]] = [
    ("baseline fixture is valid", GOOD, ""),
    (
        "duplicate control id is rejected",
        GOOD + """  - id: TEST-AUTHN-0001
    title: A duplicate control
    category: authentication
    severity: low
    rationale: Long enough rationale to satisfy the minimum length rule.
    check: {type: manual, evidence_hint: something}
    remediation: Do the thing.
""",
        "duplicate control id",
    ),
    (
        "unknown severity is rejected",
        GOOD.replace("severity: high", "severity: catastrophic"),
        "severity",
    ),
    (
        "malformed control id is rejected",
        GOOD.replace("TEST-AUTHN-0001", "test_authn_1"),
        "id",
    ),
    (
        "profile_parameter check missing its value is rejected",
        GOOD.replace(
            "check: {type: profile_parameter, parameter: login/min_password_lng, operator: gte, value: 8}",
            "check: {type: profile_parameter, parameter: login/min_password_lng}",
        ),
        "check",
    ),
    (
        "unknown check type is rejected",
        GOOD.replace(
            "check: {type: profile_parameter, parameter: login/min_password_lng, operator: gte, value: 8}",
            "check: {type: telepathy}",
        ),
        "check",
    ),
    (
        "non-CalVer version is rejected",
        GOOD.replace('version: "2026.07.1"', 'version: "v1"'),
        "version",
    ),
    (
        "sources are mandatory (derivation trail back to SAP)",
        GOOD.replace('  - {title: T, url: "https://help.sap.com/x", retrieved: 2026-07-19}\n', ""),
        "sources",
    ),
    (
        "manual check without evidence_hint is flagged",
        GOOD.replace(
            "check: {type: profile_parameter, parameter: login/min_password_lng, operator: gte, value: 8}",
            "check: {type: manual}",
        ),
        "evidence_hint",
    ),
]


def main() -> int:
    passed = failed = 0
    with tempfile.TemporaryDirectory() as tmp:
        for name, body, expect in CASES:
            path = pathlib.Path(tmp) / "probe-test.yaml"
            path.write_text(body, encoding="utf-8")
            problems = validate_file(path, VALIDATOR)
            joined = " | ".join(problems)
            if expect == "":
                ok = not problems
            else:
                ok = any(expect in p for p in problems)
            print(f"  {'ok  ' if ok else 'FAIL'} {name}")
            if not ok:
                print(f"       expected {expect!r}, got: {joined or '(no problems)'}")
            passed, failed = (passed + 1, failed) if ok else (passed, failed + 1)

    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
