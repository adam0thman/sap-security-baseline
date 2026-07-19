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

> ## ⚠️ SAP Notes change — always check the current version
>
> Several definition sets derive their exact values from **SAP Notes and KBAs, which SAP
> revises continuously.** A Note that mandated one value last quarter may mandate another
> today.
>
> Every Note-derived source records the **exact Note version and release date** it was
> built from, in the file's `sources` block. Before relying on any of this for an audit,
> a customer report, or a system change: **open the current Note on SAP for Me, compare
> the version, and confirm nothing has moved.**
>
> Notes this repository currently tracks:
>
> | Definition set | SAP Note / KBA | Version used | Released |
> |---|---|---|---|
> | `hana` | 3480723 | v5 | 2026-04-21 |
> | `nw-as-abap` | 3250501 | v46 | 2026-05-15 |
> | `nw-as-java` | 3381209 | v9 | 2026-04-09 |
>
> If you find a Note has been revised past what is recorded here, that is a bug worth
> reporting — **hello@adamoneservices.com** — or a pull request.

---

## Coverage

| Definition set | Product key | Controls | Set version |
|---|---|---:|---|
| `nw-as-abap` | `NW_AS_ABAP` | 80 (61 auto / 19 manual) | 2026.07.4 |
| `nw-as-java` | `NW_AS_JAVA` | 32 (20 auto / 12 manual) | 2026.07.2 |
| `hana` | `HANA` | 32 (4 auto / 28 manual) | 2026.07.2 |
| `sap-gateway` | `SAP_GATEWAY` | 8 (2 auto / 6 manual) | 2026.07.1 |
| `solman` | `SOLMAN` | 10 (2 auto / 8 manual) | 2026.07.1 |
| `bw` | `BW` | 8 (1 auto / 7 manual) | 2026.07.1 |
| `bw4hana` | `BW4HANA` | 12 (1 auto / 11 manual) | 2026.07.1 |
| `ase` | `ASE` | 9 (0 auto / 9 manual) | 2026.07.1 |
| `btp` | `BTP` | 13 (0 auto / 13 manual) | 2026.07.1 |
| `db2` | `DB2` | 9 (0 auto / 9 manual) | 2026.07.1 |
| `oracle` | `ORACLE` | 9 (0 auto / 9 manual) | 2026.07.1 |
| `sqlserver` | `SQLSERVER` | 10 (0 auto / 10 manual) | 2026.07.1 |
| — | `MAXDB` | — | Backlog |

**232 controls across 12 products — 91 machine-checkable, 141 attested.**

Four things to understand about how these fit together:

- **Sets layer, they don't duplicate.** BW, BW/4HANA, Gateway and Solution Manager all run on
  AS ABAP, so `nw-as-abap` applies *in addition* to those sets. Each file states its layering in a
  comment above `controls`.
- **Some values are the SAP cloud (ECS / RISE / GCO) mandatory standard.** The AS ABAP, AS Java and
  HANA sets incorporate SAP's mandatory hardening Notes. Those values are stricter than general
  on-premise guidance — a 15-character minimum password length on ABAP, for example — and the
  controls carrying them are tagged **`ecs-mandatory`**. Compulsory if you run ECS or RISE; a strong
  baseline otherwise. Filter the tag to separate the two regimes.
- **The third-party database sets are deliberately scoped** to the SAP-managed surface: the accounts
  SAP creates, how the application server authenticates, the network path, backups and patch cadence.
  Engine hardening remains governed by the database vendor's own documentation, which each file names
  in a scope note. They are intentionally all-manual — no probe here should imply authority over a
  vendor's engine configuration.
- **Non-security parameters are out of scope.** SAP also publishes mandatory *non-security* parameter
  Notes for ECS (memory sizing and similar). Mixing operational tuning into a security baseline would
  blur what a finding means.

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
