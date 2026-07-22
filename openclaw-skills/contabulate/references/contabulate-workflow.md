# Contabulate Workflow Reference

## Repo/domain map

- `brainheart/contabulate` → `contabulate.org`
- `brainheart/shakespeare-contabulate` → `shakespeare.contabulate.org`
- `brainheart/kjv-contabulate` → `kjv.contabulate.org`
- `brainheart/tanakh-contabulate` → `tanakh.contabulate.org`
- `brainheart/homer-contabulate` → `homer.contabulate.org`
- `brainheart/aeneid-contabulate` → `aeneid.contabulate.org`
- `brainheart/luther-contabulate` → `luther.contabulate.org`
- `brainheart/dante-contabulate` → `dante.contabulate.org`
- `brainheart/hawthorne-contabulate` → `hawthorne.contabulate.org`
- `brainheart/melville-contabulate` → `melville.contabulate.org`
- `brainheart/moby-dick-contabulate` → `moby-dick.contabulate.org`
- `brainheart/thucydides-contabulate` → `thucydides.contabulate.org`
- `brainheart/xenophon-contabulate` → `xenophon.contabulate.org`
- `brainheart/kafka-contabulate` → `kafka.contabulate.org` (Cloudflare proxied HTTPS as of 2026-05-21; GitHub Pages cert had not appeared immediately after launch)
- `brainheart/moby-dick-contabulate-sqlite` → deprecated experiment; do not use as a starting point unless investigating the old WASM idea.

Confirm live state with `gh repo list`/Pages API before relying on this list.

## Design preferences

- Static JSON beats SQLite/WASM for GitHub Pages: smaller over the wire with gzip, simpler hosting, incremental loading.
- Footer should use a plain build timestamp, not a commit hash.
- When a corpus changes, update that corpus site's footer build timestamp. When the main landing table changes, update the landing page footer build timestamp.
- On the main landing table, use `Released` for the original launch date and `Updated` for the most recent corpus/site release date; default-sort by `Updated` descending.
- Whenever a new corpus is released or an existing corpus changes, update `brainheart/contabulate` (`contabulate.org`) so the landing table's corpus row, stats, release/update dates, and language label stay current.
- Each site should link the `Contabulate` header/title back to `https://contabulate.org`.
- Emoji/logo/table consistency matters across the landing page and corpus sites.
- Prefer neutral UI terms like `Segment` for arbitrary text units; `Passage` is acceptable for citable retrieval contexts but less general.
- For prose corpora, user-facing `Paragraph` should mean the text-bearing paragraph row. Do not add a separate numeric paragraph segment/column by default; `Location` already carries the stable citation. Avoid `Paragraph Text`.
- For prose corpora with story collections, label the named subdivision `Story / Chapter`, because the same field may be a distinct short story in collections and a chapter/part in novels. In `Story / Chapter` and `Paragraph` row views, omit `Type`; instead show `Chapter #` plus the named `Story / Chapter`. Single-chapter stories should use chapter number `1`. Paragraph row views should also show `Paragraph #` plus the text-bearing `Paragraph` column.
- Remove meaningless granularity labels. Do not display generic labels like `Genre`/`Section` if they do not help users.
- Refer to Ancient Greek corpora as `Greek` in user-facing table labels unless a more specific distinction is genuinely needed.

## Common implementation checks

### Corpus/data generation

- Identify unit hierarchy: work → book/chapter → segment/paragraph/verse/line.
- Preserve stable IDs and human-readable citations.
- Generate summary stats: works, segments, word count, unique terms.
- Ensure generated JSON is small enough for static hosting and can load incrementally.
- For single-work corpora, do not compute work-level TF-IDF over one document; use books/chapters/segments as comparison documents.

### Search/tokenization

- Normalize both indexed text and query terms consistently, usually NFC.
- Use Unicode-aware regex (`[\p{L}]+` with `u`) instead of ASCII-ish classes.
- Test exact lookup and text-view highlighting; these may use separate code paths.
- Regression terms to consider: Hebrew with nikud, Greek accents, Latin macrons/diacritics, German umlauts.

### UI parity

When porting features between repos, compare:

- Filter disclosure behavior.
- Segment tabs/detail modals.
- Sort orders and default TF-IDF views.
- Loading overlay hide/show CSS; `.is-hidden` must win over loading indicator display rules.
- Back-links, titles, emoji, table columns, and terminology.

### Lines-without-search-terms: two code paths

The "show all lines/paragraphs when no search terms" requirement touches **two separate features** that look similar but are different:

1. **Segments tab + granularity="line"** — driven by `index.html` `granVal === 'line'` branch (around line ~1272 in shakespeare). Fix: change `if (hasTerm)` to `if (hasTerm || lineMatchers.length === 0)` before `rowsMap.set(...)`. This is the prose `Paragraph` view in Hawthorne/Kafka-style sites.
2. **Separate "Rows are Lines" tab** — driven by `docs/js/lines-tab.js` `buildLinesRows()` + `doSearch()`. Fix: add `const showAllLines = !queryNgram && !isRegex;` and skip early returns on empty query.

If a user complaint references "Lines mode", **ask for a screenshot first**. Telling the two apart by description alone is hard.

## Publishing checklist

1. `git status` before editing.
2. Build/test locally with repo conventions.
3. Commit generated `/docs` output if that is the published artifact.
4. Update build timestamps: corpus footer when that corpus changed; main landing footer when the landing table changed.
5. If releasing/changing a corpus, update and publish the main `contabulate.org` landing table too.
6. Push.
7. Verify Pages API:
   ```bash
   gh api repos/brainheart/<repo>/pages --jq '{status,cname,https_certificate,https_enforced,source}'
   ```
8. Verify live HTTP and HTTPS:
   ```bash
   curl -sSI http://<host> | sed -n '1,10p'
   curl -sSI https://<host> | sed -n '1,12p'
   ```
9. If a CNAME reset created commits remotely, pull them into the local clone.
10. Update daily memory when the workflow taught us something reusable.
