# SAP Security Baseline

Versioned, machine-readable **security control checklists for SAP products**, derived
from SAP's official Security Guides and expressed as YAML.

Each control says what must be true, why it matters, and — where possible — exactly how
to verify it on a live system. That makes a definition file something you can run against
a customer landscape, not just read.

```yaml
- id: ABAP-AUTHN-0004
  title: Automatic SAP* fallback user is disabled
  category: authentication
  severity: critical
  rationale: >
    If the SAP* user record is deleted, the kernel falls back to a hard-coded
    built-in SAP* with a well-known default password and unrestricted power,
    bypassing every authorization check.
  check:
    type: profile_parameter
    parameter: login/no_automatic_user_sapstar
    operator: eq
    value: 1
  remediation: Set login/no_automatic_user_sapstar = 1 in DEFAULT and restart.
```

## Why this exists

SAP publishes excellent security guidance, but it is prose spread across dozens of pages
per product, it changes, and it is not comparable against a running system. This repo turns
that guidance into a stable, versioned, diffable artifact that tooling can consume — so a
proactive security review becomes a repeatable check rather than a fresh reading exercise
every time.

It is deliberately **standalone and tool-agnostic**: the YAML plus the JSON Schema is the
whole contract. [curioDesk](https://github.com/adam0thman/curioDesk) is the first consumer,
but nothing here depends on it.

## Layout

```
schema/definition.schema.json   The contract. Language-agnostic; validate from anything.
definitions/*.yaml              One definition set per SAP product.
tools/validate.py               Validates the definitions (schema + the rules JSON Schema can't express).
tools/selftest.py               Proves the validator actually rejects bad input.
tools/EXTRACTION_PROMPT.md      The repeatable "regenerate this from help.sap.com" procedure.
```

## Coverage

| Definition set | Product key | Controls | Status |
|---|---|---:|---|
| `nw-as-abap` | `NW_AS_ABAP` | 25 (18 auto / 7 manual) | first release |
| `sap-gateway` | `SAP_GATEWAY` | 8 (2 auto / 6 manual) | first release |
| _planned_ | `NW_AS_JAVA`, `BW`, `BW4HANA` | — | next extraction batch |
| _later_ | `SOLMAN`, `HANA`, `MAXDB`, `ORACLE`, `SQLSERVER`, `DB2`, `ASE`, `BTP` | — | backlog |

## Usage

```bash
pip install -r tools/requirements.txt
python3 tools/validate.py                      # validate everything
python3 tools/validate.py definitions/nw-as-abap.yaml
python3 tools/selftest.py                      # check the validator itself
```

Editors pick up the schema automatically via the `# yaml-language-server` line at the top
of each definition file, giving autocomplete and inline errors while authoring.

## How a control is verified

Every control carries a `check`. One type is manual; the rest are machine-checkable, and a
consumer implements a probe per type.

| `check.type` | Verified by reading | Example |
|---|---|---|
| `profile_parameter` | instance profile / `RSPARAM` | `login/min_password_lng >= 8` |
| `table_query` | a table via RFC | production clients closed in `T000` |
| `user_query` | user master data | no standard user on a default password |
| `gateway_acl` | `secinfo` / `reginfo` | ACL exists and is restrictive |
| `icf_service` | SICF service state | `/sap/bc/soap/rfc` disabled |
| `manual` | a human, with evidence | system change option in SE06 |

Mixed by design: much of a Security Guide is procedural and no probe can settle it, while
the parameter-level controls are exactly the ones that quietly drift. Marking each control
honestly is what keeps the automated subset trustworthy.

## Versioning

- **`spec_version`** — the schema contract. Major bump = breaking change for consumers.
- **`version`** — the definition set, CalVer `YYYY.MM.PATCH`, with `supersedes` pointing at
  the release it replaces. The validator enforces that it moves forward.
- **Control ids are permanent.** A finding recorded against `ABAP-AUTHN-0004` must still
  mean the same control a year later, so ids are never renumbered or recycled. Withdrawn
  controls keep their id and gain a `withdrawn` tag.

## Keeping it current

Definition files are regenerated from help.sap.com by an AI agent following
[`tools/EXTRACTION_PROMPT.md`](tools/EXTRACTION_PROMPT.md), which pins the extraction rules
so successive runs stay comparable. Because control ids are stable, a re-run produces a
small reviewable diff rather than a wholesale rewrite.

## Provenance and copyright

Controls here are **derived** from SAP's publicly published documentation: the risk and
remediation text is original, written to be checkable, and each definition file cites the
SAP guides it was derived from in `sources`, with per-control deep links in `references`.

No SAP documentation is reproduced verbatim in this repository. SAP, NetWeaver, S/4HANA and
other SAP product names are trademarks of SAP SE. This repository is not affiliated with,
endorsed by, or supported by SAP SE. Always confirm against the official guide and the
relevant SAP Notes for your exact release before acting on a control.

## Licence

Definition content and tooling: MIT (see `LICENSE`). This licence covers the material in
this repository only — not SAP's documentation, which remains SAP's.
