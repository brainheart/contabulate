# Contabulate-style table contract

## Contents

- [Design principles](#design-principles)
- [Data and column model](#data-and-column-model)
- [Sorting and filtering](#sorting-and-filtering)
- [Paging and export](#paging-and-export)
- [Deep links and history](#deep-links-and-history)
- [Drill doors and scope](#drill-doors-and-scope)
- [Optional and movable columns](#optional-and-movable-columns)
- [Color, highlighting, and rank](#color-highlighting-and-rank)
- [Visual language](#visual-language)
- [Accessibility and responsive behavior](#accessibility-and-responsive-behavior)
- [States, performance, and safety](#states-performance-and-safety)
- [Acceptance checklist](#acceptance-checklist)
- [Current source map](#current-source-map)

## Design principles

- Keep the table primary. Put global query and scope controls above it; put column controls in or beside the header.
- Preserve analytical context. Filters, sort, column choices, and scope should survive paging and be shareable when meaningful.
- Make every affordance truthful. A clickable count drills into what it counts; an ancestor label filters to that ancestor; a header sorts; a gear filters.
- Prefer progressive disclosure. Default columns answer the common question; add metrics or commentary from the `+` column control.
- Keep raw data and rendered text separate. Use typed raw values for all computation.
- Format dense information calmly: clear hierarchy, compact spacing, thousands separators, concise tooltips, and restrained color.

## Data and column model

Give every row a stable key and every column a stable key. A useful column definition contains:

```js
{
  key: 'word_count',
  label: 'Words',
  type: 'number',
  defaultDir: 'desc',
  tooltip: 'Total token count in this row scope.'
}
```

Retain raw numeric values in row data or `data-value`; never recover important values from formatted cell text. Treat percentages as ratios internally and format once at the edge. Define null ordering. Add a deterministic stable tie-breaker, usually the row key or canonical order.

Avoid duplicate information when changing row granularity. A genre row does not need a second Genre column; a work row should not repeat its title in multiple forms. Rename labels to the corpus's real nouns.

## Sorting and filtering

Sorting requirements:

- Click a sortable header to sort; click again to reverse.
- Default a new numeric sort descending and a new text sort ascending unless the column explicitly says otherwise.
- Show an unambiguous ▲/▼ indicator and expose direction accessibly, preferably with `aria-sort`.
- Parse structured identifiers component-wise instead of lexicographically when `2.10` must follow `2.9`.
- Reset to page 1 after sort and keep the current sort when data is re-rendered.

Filtering requirements:

- Put a filter control in each filterable header without letting its click trigger sorting.
- Use type-specific UI: min/max for numeric data; a documented literal/contains/regex choice for text. Do not silently treat user text as regex.
- For percentage columns, accept either displayed percentages or ratios only when the rule is explicit in the UI.
- Combine column filters with AND semantics unless the product clearly calls for another model.
- Show active filters as human-readable removable chips and provide Clear all.
- Scope filters to the row granularity when their meaning changes, but share the map among equivalent views such as word/bigram/trigram.
- Reset to page 1, rerender, recolor, update totals, and update the URL after filtering.
- Escape values inserted into generated regexes. Handle invalid regex input without breaking the table.

## Paging and export

Apply operations in this order:

```text
source rows → query/scope → column filters → stable sort → paginate → render
```

Provide First, Prev, current page/total pages, Next, Last, row-count context, and a rows-per-page selector with sensible sizes such as 25/50/100/250. Hide or de-emphasize pagination when it adds no value. Clamp the current page after filtering and disable impossible controls.

CSV means the current analytical result, not the current viewport:

- export all filtered and sorted rows across all pages;
- export visible columns in their visible order;
- use plain header labels without icons or control text;
- preserve human-readable labels and formatted percentages where useful;
- escape commas, quotes, CR/LF, and embedded newlines according to CSV rules;
- use UTF-8 and a descriptive filename;
- test zero rows and large exports.

If a product might need raw data instead, label separate actions clearly as “Download current view” and “Download raw data.”

## Deep links and history

Serialize state in readable query parameters where practical:

- query terms and match modes;
- row granularity;
- sort key and direction;
- column order and optional-column selection;
- current granularity's filters;
- scope or drill path;
- meaningful toggles such as zero rows, highlights, or color scale;
- open detail modal only if sharing it is valuable.

Omit noisy cosmetic defaults, such as palette step count, when clean URLs matter more. Keep a legacy decoder when changing a published URL format.

Arm URL synchronization only after startup state has been applied. Use `replaceState` for refinements such as sorting, filtering, and display toggles. Use `pushState` for navigation-like changes such as drills, granularity changes, ancestor scopes, or opening a shareable detail view. Handle `popstate` so browser Back restores the table instead of merely changing the address bar.

Test a copied URL in a fresh page, not just a reload with in-memory state.

## Drill doors and scope

Use two distinct interactions:

- Count-cell drill: change to the granularity of the counted entities and retain a scope filter. Example: 50 Chapters opens chapter rows for that work.
- Ancestor-cell filter: remain at the current granularity and restrict rows to that ancestor. Example: clicking a work name on paragraph rows filters paragraphs to that work.

Make drill targets explicit in a small mapping rather than deriving them from labels. Render links as real anchors when a complete URL is available; otherwise use accessible buttons with link-like styling and history behavior.

Carry location or genre scope when moving up and down a hierarchy. Remove stale filters that cannot exist in the target granularity. Preserve vocabulary scope across n-gram sizes. Browser Back should undo drills and scope changes in order.

## Optional and movable columns

Use a `+` header cell to add columns close to where they appear. On narrow screens, expose the same action from the toolbar. The chooser should:

- support keyboard opening, focus, Enter/Space selection, Escape close, and outside-click close;
- group only available dimensions, hiding empty groups such as Commentators for a corpus without commentary;
- provide search when the catalog is long;
- mark selected columns and allow removable headers for transient term/commentator columns;
- keep stable keys so order and selection can be deep-linked.

Allow drag reorder when it materially helps comparison. Suppress the click that would otherwise sort after a drag. Show a clear insertion affordance. Provide a non-drag alternative where accessibility or touch usage requires it.

## Color, highlighting, and rank

Color scales:

- apply only to genuinely numeric cells and use raw values;
- compute thresholds per column across the full filtered result set, not each page, so colors do not change while paging;
- use quantiles for skewed literary counts; skip columns with fewer than two numeric values or no range;
- provide a Low / Median / High legend and an off switch;
- choose foreground text for contrast on every swatch;
- reapply after sort, filter, page, or column changes;
- never let color be the only carrier of meaning.

The current Contabulate defaults are a seven-step blue-diverging scale from gray through near-white to deep blue. Blue-linear and burgundy-gold alternatives exist. Use a sequential scale for naturally ordered magnitude; use a diverging scale only when the midpoint has meaning. The historical “diverging” default is an aesthetic convention, not a license to imply a statistical zero.

Search highlighting must escape source text before inserting markup, handle zero-width regex matches safely, and remain optional. Limit pathological patterns or match counts that would freeze rendering.

Numeric rank hints answer “where does this value stand?” without adding another column. Rank against the full filtered result, define ties consistently, keep the displayed number visible, use dotted underline/cursor help as a subtle cue, and expose the same hint by title/ARIA and tap on non-hover devices.

## Visual language

Canonical tokens:

```css
:root {
  --parchment: #f9f7f1;
  --ink: #2b2b2b;
  --burgundy: #8b1538;
  --gold: #d4af37;
  --border: #d4c5b0;
  --shadow: rgba(43, 43, 43, 0.08);
}
```

Use Crimson Text with Georgia/Garamond fallbacks for reading and Cinzel with Georgia fallback for the main title. On non-Contabulate projects, adapt fonts to the host while retaining the role contrast.

Table treatment:

- white table on a parchment-to-off-white page;
- collapsed warm-gray borders, compact `0.7rem 0.8rem` cells, and a subtle shadow/radius;
- sticky, warm-gradient headers in burgundy with a stronger bottom border;
- subtle zebra striping and gold-tinted row hover;
- burgundy primary actions, restrained transparent link actions, and a distinct dark-green CSV button;
- numeric values with thousands separators and at most the meaningful precision;
- concise header tooltips describing the metric, denominator, and “Click to sort.”

Do not copy duplicate or obsolete CSS blocks from an instance. Extract tokens and component rules into the host's normal structure.

## Accessibility and responsive behavior

- Use `<table>`, `<thead>`, `<tbody>`, `<th scope="col">`, and real buttons/links.
- Give icon-only controls names, state, and focus styles; decorative symbols get `aria-hidden`.
- Keep sort and filter targets separate and keyboard-operable.
- Use `aria-haspopup` for popovers, restore focus on close, and manage modal focus when details open.
- Announce material result-count or loading changes with a restrained live region when appropriate.
- Maintain visible focus and sufficient color contrast. Respect `prefers-reduced-motion`.
- On screens below roughly 900px, reduce page padding, stack/wrap controls, make the table a horizontal scroll container, and expose the column chooser outside the far-right header.
- Test touch: rank hints, tiny filter icons, column removal, and horizontal scrolling must not rely on hover.

## States, performance, and safety

Implement explicit loading, empty-result, source-error, and partial-data states. A full-screen loader must always dismiss when required data settles or fails; ensure the hidden utility overrides its display rule.

Lazy-load heavyweight row text or detail records. Preload only during idle time when it improves later drills. Debounce live filters. Cache derived n-grams and computed row sets by scope where useful. Cancel or ignore stale asynchronous searches by request ID.

Escape all source text and labels before HTML insertion. Treat URL state as untrusted: validate keys, types, enums, ranges, regexes, and column names. Avoid `innerHTML` for content unless values are escaped centrally.

## Acceptance checklist

- [ ] Stable row and column keys; raw typed values separated from display.
- [ ] Sort indicators, deterministic ties, null behavior, and page reset tested.
- [ ] Type-aware filters, removable chips, Clear all, and invalid-input behavior tested.
- [ ] Filtered total and page controls stay correct after every state change.
- [ ] CSV includes all filtered rows and visible ordered columns, with correct escaping.
- [ ] Fresh-load deep link restores query, scope, filters, sort, and columns.
- [ ] Back/Forward retraces drills and navigation-like scopes.
- [ ] Count drills and ancestor filters are semantically distinct and predictable.
- [ ] Optional-column groups disappear when unsupported; keyboard and mobile access work.
- [ ] Reordering does not accidentally sort and has an accessible alternative if required.
- [ ] Color thresholds use the full filtered result, legend and contrast are correct, and ties/constant columns behave.
- [ ] Highlights are escaped and regex-safe; rank hints work with hover and tap.
- [ ] Sticky headers, overflow, focus, touch targets, reduced motion, and narrow screens verified.
- [ ] Loading, empty, error, one-row, many-row, missing, zero, tied, percentage, negative, and Unicode cases verified.
- [ ] Composed Playwright/browser workflows cover interactions rather than isolated controls only.

## Current source map

Verified 2026-07-21 in `/Users/klaus/Projects/contabulate/instances/austen-contabulate`:

- `docs/index.html`: state model, deep links/history, columns, sort/filter orchestration, drills, rendering, pagination, CSV wiring.
- `docs/js/table-ui.js`: column ordering and header drag behavior.
- `docs/js/filter-popover.js`: typed per-column filter UI.
- `docs/js/add-column-popover.js`: searchable optional-column chooser and keyboard handling.
- `docs/js/color-scale.js`: quantile palettes, legends, contrast, and highlight toggles.
- `docs/js/utils.js`: strict numeric parsing, escaping, CSV, formatting, quantiles, pagination, and regex helpers.
- `docs/css/main.css`: visual tokens, table controls, popovers, rank hints, and responsive rules.
- `tests/contabulate.spec.js`: corpus-specific end-to-end examples.

For commentary details and character details, inspect the corresponding modules in `tanakh-contabulate`/`kjv-contabulate` and `shakespeare-contabulate`. Borrow behavior selectively and write host-project tests; do not wholesale-copy a 2,000-line page.
