# Extraction procedure (the "run my AI" step)

This is the repeatable instruction set for regenerating or updating a definition file
from SAP's official documentation. Paste the **Prompt** below into an agent that has
web access, filling in the product. The output must pass `python3 tools/validate.py`
before it is committed.

## Why a fixed procedure

Two failure modes make ad-hoc extraction useless:

1. **Drift** — a control silently changes id or wording between runs, so findings
   recorded against the old id can no longer be compared over time.
2. **Copying** — bulk-pasting SAP's prose produces a file that cannot be
   redistributed and is, in practice, less useful than a crisp checkable control.

The rules below exist to prevent both.

## Where the content actually lives

`help.sap.com/docs/...` is a JavaScript single-page app and returns an empty shell to
a plain fetch. Use these instead:

| Route | Pattern | Use for |
|---|---|---|
| Crawler index | `https://help.sap.com/crawler/PRODUCTION/<PRODUCT_ID>/<version>/en-US` | Enumerating every doc page for a product — this is the entry point |
| Static content | `https://help.sap.com/doc/<hash>/<version>/en-US/<page>.html` | Reading an individual guide section |
| Legacy static | `https://help.sap.com/saphelp_<rel>/helpdata/en/<path>/content.htm?no_cache=true` | Older guides; reliably plain HTML |
| PDF | `https://help.sap.com/doc/<guid>/<ver>/en-US/<Name>_en.pdf` | Whole security guides (e.g. BW/4HANA) |

Start at the crawler index, find the entries whose titles contain *Security Guide*,
*Security Information*, *Secure Configuration*, or *Security Aspects*, then fetch those.

## Prompt

> You are extracting a security baseline for **\<PRODUCT NAME\>** (product key
> `<PRODUCT_KEY>`) from SAP's official documentation, into a definition file that
> conforms to `schema/definition.schema.json` in this repository.
>
> **Sources.** Begin at the crawler index for the product, identify every
> security-related guide, and read them. Record each guide you actually used in
> `sources` with its URL and today's date as `retrieved`. Never cite a page you did
> not read.
>
> **Write derived controls, not quotations.** Each control's `rationale` and
> `remediation` must be in your own words, stating the risk and the fix concisely.
> Do not paste SAP's sentences. If a control cannot be expressed without quoting,
> summarise the requirement and link the section in `references` instead.
>
> **Prefer machine-checkable controls.** When the guide names a concrete artefact —
> a profile parameter, a table, an ICF service, a gateway ACL file, a standard user —
> express it as the matching non-`manual` `check` type with a definite expected value.
> Use `manual` only when the requirement is genuinely procedural, and always give an
> `evidence_hint` naming the transaction or export that proves it.
>
> **Be honest about values.** Where SAP states a specific value, use it. Where the
> "right" value is customer policy (password length, timeouts, retention), choose a
> defensible baseline and say so in `remediation` — never invent a precise SAP
> recommendation that the guide does not make.
>
> **Control ids are permanent.** Format `<PREFIX>-<AREA>-NNNN`, e.g. `ABAP-AUTHN-0001`.
> When updating an existing file: keep every existing id attached to its existing
> control, append new controls with fresh numbers, and never renumber or recycle an
> id. To withdraw a control, keep the id and mark it with the tag `withdrawn` rather
> than deleting the entry.
>
> **Versioning.** Set `version` to CalVer `YYYY.MM.PATCH`, set `supersedes` to the
> previous version string, and bump the patch for a same-month re-issue.
>
> Output a single YAML file. Then run `python3 tools/validate.py` and fix anything it
> reports.

## After the run

```bash
python3 tools/validate.py            # must be clean
python3 tools/selftest.py            # validator itself still behaves
git diff --stat definitions/         # review what changed before committing
```

Review the diff by hand. The point of stable ids is that a real diff should be small
and explainable: new controls appended, wording sharpened, values corrected. A diff
that renumbers everything means the procedure was not followed and the run should be
redone — otherwise every historical finding loses its anchor.
