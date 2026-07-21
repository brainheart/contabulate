---
name: contabulate-instances
description: Create, port, extend, or repair a Contabulate literary-corpus instance and keep its generated data, tests, instance metadata, deployment files, and contabulate.org hub entry in sync. Use for new `*-contabulate` repositories; corpus ingestion or tokenizer changes; adopting improvements from another instance; editing `instance-meta.json` or generated `docs/instance.json`; adding sample-query deep links; updating the main Contabulate page; or diagnosing drift among the independent instance repositories.
---

# Contabulate Instances

Treat an instance as a data build, an exploratory table application, a published metadata endpoint, and an independent Git repository. Preserve all four contracts.

## Start safely

1. Locate the Contabulate hub and the target instance. Confirm repository roots with `git -C <path> rev-parse --show-toplevel`.
2. Inspect status, branch, remote, recent history, build instructions, and tests in each repository before editing. The hub's `instances/` directory may contain nested repos that the hub intentionally ignores.
3. Read [references/playbook.md](references/playbook.md) completely before creating an instance. For a narrower maintenance task, read the relevant sections listed there.
4. Choose a donor by corpus shape and feature needs, then compare it with the most recently improved instance. Do not assume the oldest or visually closest copy is current.

## Create or port an instance

1. Define the corpus contract first: source provenance and license, works and order, hierarchy, stable IDs, tokenizer/normalization, row labels, and optional characters or commentary.
2. Copy only an appropriate donor's reusable shell. Rename branding, URLs, CNAME, labels, source links, defaults, parser assumptions, and tests deliberately.
3. Make the build pipeline authoritative. Generate `docs/data/*`, `docs/lines/*`, metrics, and `docs/instance.json`; avoid hand-editing generated output except to diagnose and then fix the generator.
4. Adapt the table's row granularities, columns, drill doors, ancestor filters, search semantics, metric denominators, and empty optional features to this corpus. Invoke `$contabulate-style-tables` for the shared interaction and visual contract.
5. Keep IDs stable and sortable. Test representative first/last rows, uniqueness, referential integrity, totals, Unicode/diacritic behavior, and corpus-specific parsing boundaries.

## Publish metadata and register the instance

1. Curate `instance-meta.json`; generate `docs/instance.json` from it plus computed statistics on every build.
2. Keep `created` stable. Set `updated` from the build date. Publish schema 1, absolute canonical URLs, labels, zero-valued optional stats, and tested sample-query deep links.
3. Validate `docs/CNAME` against the canonical host.
4. In the separate hub repository, add the base URL to `docs/instances.json` and add the human-readable row to `README.md`. The landing page fetches each live `/instance.json`; do not duplicate its computed fields in hub HTML.
5. Run `python3 scripts/audit_instance.py <instance> --hub-root <hub> --require-hub` from this skill for a read-only preflight.

## Verify before handoff

Run the instance build, build-output tests, Playwright tests through a local HTTP server, and a focused browser smoke test. Exercise both the default view and a nontrivial deep link. Check responsive overflow, loading/error/empty states, Back behavior after drills, CSV contents, and all optional-feature combinations relevant to the corpus.

Review diffs and status in the instance repository and hub repository separately. Report what was generated, what remains uncommitted, and which deployment or DNS steps—if any—still need authorization.

## Keep this skill alive

After a new instance or substantial cross-instance change, update [references/playbook.md](references/playbook.md) with only generalized, verified lessons: the new best donor, a changed contract, a failure mode, or a validation step. Date source-map changes, remove superseded advice, and rerun the skill validator. Do not turn the reference into a chronological changelog.

## Resources

- [references/playbook.md](references/playbook.md): workspace topology, donor map, contracts, checklist, and known traps.
- `scripts/audit_instance.py`: read-only metadata and hub-registration preflight; run with `--help` for options.
