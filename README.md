# SAP Security Baseline

**Machine-readable security control checklists for SAP products**, compiled from SAP's
publicly available Security Guides and published as versioned YAML.

Each control states what must be true, why it matters, and — wherever possible — exactly how
to verify it on a running system. That turns a security guide from something you *read* into
something you can *check*.

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

---

## Why this exists

SAP publishes thorough security guidance, but it is prose spread across dozens of pages per
product, it changes between releases, and none of it is directly comparable against a system
you actually operate. Every security review therefore starts by re-reading the same documents
and hand-building the same spreadsheet.

This project does that work once, in a stable format:

- **Checkable, not narrative.** Where a guide names a profile parameter, a table, an ICF
  service or a standard user, the control carries the exact artefact and expected value.
- **Versioned and diffable.** Definition sets use CalVer and declare what they supersede, so
  you can see precisely what changed between releases of the baseline itself.
- **Stable control ids.** A finding recorded against `ABAP-AUTHN-0004` still means the same
  control a year later. Ids are never renumbered or recycled.
- **Tool-agnostic.** The YAML plus the JSON Schema is the entire contract. Consume it from
  Python, Java, TypeScript, a spreadsheet, or your own audit tooling.

It is **not** a scanner. This repository is the *definition* of what good looks like; running
the checks against a system is the job of whatever tool you point at it.

---

## Repository structure

```
schema/
  definition.schema.json     The contract. JSON Schema (draft 2020-12), language-agnostic.

definitions/
  nw-as-abap.yaml            SAP NetWeaver AS ABAP / ABAP Platform
  nw-as-java.yaml            SAP NetWeaver AS Java
  sap-gateway.yaml           SAP Gateway (OData / Fiori Foundation)
  bw.yaml                    SAP Business Warehouse (classic, on NetWeaver)
  bw4hana.yaml               SAP BW/4HANA

tools/
  validate.py                Validates definitions: schema + rules JSON Schema can't express
  selftest.py                Proves the validator actually rejects malformed input
  requirements.txt           PyYAML + jsonschema
  EXTRACTION_PROMPT.md       The repeatable procedure for regenerating definitions from SAP docs

.github/workflows/
  validate.yml               CI: validates every definition on push and pull request
```

### Anatomy of a definition file

| Field | Meaning |
|---|---|
| `spec_version` | Version of the schema the file conforms to |
| `id` | Stable machine id for the set; matches the filename |
| `product.key` | Product family (`NW_AS_ABAP`, `SAP_GATEWAY`, `BW`, …) — how you match a set to a system |
| `version` | CalVer `YYYY.MM.PATCH` for the definition set |
| `supersedes` | The version this release replaces; the validator enforces forward movement |
| `sources` | The SAP guides the controls were derived from, with retrieval dates |
| `controls[]` | The controls themselves |

Each control carries `id`, `title`, `category`, `severity`, `rationale`, `check`, `remediation`,
and optional `references`, `applies_to` and `tags`.

### How controls are verified

Every control declares a `check`. One type is manual; the rest are machine-checkable, and a
consuming tool implements one probe per type.

| `check.type` | Verified by reading | Example |
|---|---|---|
| `profile_parameter` | Instance profile / `RSPARAM` | `login/min_password_lng >= 8` |
| `ume_property` | AS Java UME property | `ume.superadmin.activated = false` |
| `table_query` | A table via RFC | Production clients closed in `T000` |
| `user_query` | User master data | No standard user left on a default password |
| `gateway_acl` | `secinfo` / `reginfo` | ACL exists and is restrictive |
| `icf_service` | SICF service state | `/sap/bc/soap/rfc` disabled |
| `manual` | A human, with evidence | System change option in SE06 |

The mix is deliberate. A large part of any Security Guide is procedural and no probe can settle
it; marking those honestly as `manual` (each with an `evidence_hint`) is what keeps the automated
subset trustworthy.

---

## Coverage

| Definition set | Product key | Controls | Status |
|---|---|---:|---|
| `nw-as-abap` | `NW_AS_ABAP` | 25 (18 auto / 7 manual) | Published |
| `nw-as-java` | `NW_AS_JAVA` | 12 (3 auto / 9 manual) | Published |
| `sap-gateway` | `SAP_GATEWAY` | 8 (2 auto / 6 manual) | Published |
| `bw` | `BW` | 8 (1 auto / 7 manual) | Published |
| `bw4hana` | `BW4HANA` | 12 (1 auto / 11 manual) | Published |
| — | `SOLMAN`, `HANA`, `MAXDB`, `ORACLE`, `SQLSERVER`, `DB2`, `ASE`, `BTP` | — | Backlog |

**65 controls across 5 products.** Layering is deliberate: BW, BW/4HANA and Gateway all run on
AS ABAP, so `nw-as-abap` applies *in addition* to those sets rather than being duplicated into
them. Each file states its layering in a comment at the top of `controls`.

---

## Usage

### Validate

```bash
pip install -r tools/requirements.txt

python3 tools/validate.py                          # validate every definition
python3 tools/validate.py definitions/nw-as-abap.yaml
python3 tools/selftest.py                          # check the validator itself
```

Editors pick the schema up automatically from the `# yaml-language-server` line at the top of
each definition file, giving autocomplete and inline errors while authoring.

### Consume

The files are ordinary YAML — load them with whatever you already use.

```python
import yaml

spec = yaml.safe_load(open("definitions/nw-as-abap.yaml"))

# Controls a tool can check automatically, hardest-hitting first
severity = {"critical": 0, "high": 1, "medium": 2, "low": 3}
auto = [c for c in spec["controls"] if c["check"]["type"] != "manual"]
for c in sorted(auto, key=lambda c: severity[c["severity"]]):
    print(f"{c['id']:<18} {c['severity']:<8} {c['title']}")
```

Pin to the `version` field so an updated baseline never silently changes a report you have
already issued, and record findings against the control `id` so they stay comparable when you
move to a newer version.

### Keep it current

Definition files are regenerated from SAP's published documentation following
[`tools/EXTRACTION_PROMPT.md`](tools/EXTRACTION_PROMPT.md), which fixes the extraction rules so
successive runs stay comparable. Because control ids are stable, a re-run yields a small,
reviewable diff rather than a wholesale rewrite.

---

## Contributing, feature requests and bug reports

Corrections are especially welcome — if a control is wrong for your release, cites the wrong
parameter, or is missing from a product, please say so.

- **Issues and pull requests:** via this repository.
- **Email:** **hello@adamoneservices.com**

When reporting a problem with a control, quoting its `id` and the definition-set `version` makes
it immediately actionable.

---

## Provenance, accreditation and disclaimer

Compiled and maintained by **Nik M Adam — Adam One Services**.

The controls are **derived** from SAP's publicly available documentation. The risk and remediation
wording is original, written to be concise and checkable; each definition file cites the SAP guides
it was derived from in `sources`, with per-control deep links in `references`. **No SAP documentation
is reproduced verbatim in this repository.**

SAP, SAP NetWeaver, ABAP, S/4HANA, SAP HANA and other SAP product names referenced here are
trademarks or registered trademarks of SAP SE in Germany and other countries. This project is
independent: it is **not affiliated with, endorsed by, sponsored by, or supported by SAP SE**.

This material is provided for guidance only and is no substitute for the official documentation.
Always confirm a control against the current SAP guide and the relevant SAP Notes for your exact
release, and validate any change in a non-production system first. Baseline values for
policy-driven settings (password length, timeouts, retention) are defensible starting points, not
SAP-mandated figures — align them with your own security policy.

## Licence — free for everyone, including commercial use

**MIT** (see [`LICENSE`](LICENSE)). In plain terms, you may:

- use this in **private, internal, consulting, or commercial** work;
- **copy, modify and redistribute** it, including inside a paid product or service;
- do so with **no fee, no royalty, and no permission required**.

The only condition is that the copyright and licence notice travels with substantial copies.

The licence covers **this repository's own material** — the control statements, schema and tooling,
which are original work. It does not and cannot license SAP's documentation, which remains the
property of SAP SE: publicly readable is not the same as public domain. That is precisely why the
controls here are *derived and rewritten* rather than copied, so this repository is free to pass on.
