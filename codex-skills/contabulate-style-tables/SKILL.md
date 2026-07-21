---
name: contabulate-style-tables
description: Design, implement, port, or review a polished data table using Contabulate's hard-won visual and interaction conventions. Use when a project needs sortable and filterable columns, movable or optional columns, drill-down links, URL-deep-linked state and browser history, pagination, full-result CSV download, numeric color scales, rank hints, search highlighting, responsive behavior, or a high-density parchment/burgundy/gold table UI—even outside the Contabulate codebase.
---

# Contabulate Style Tables

Build a table as an exploratory interface, not a static grid. Preserve the user's analytical context across sorting, filtering, paging, drilling, sharing, and exporting.

## Establish the table contract

1. Identify the row entity, stable row key, column schema, data types, default sort, dataset size, hierarchy, drill targets, and which state must be shareable.
2. Read [references/table-contract.md](references/table-contract.md) completely before a net-new implementation or a broad port. For a focused change, read the relevant named section.
3. Inspect the host project's stack and design system. Recreate the behaviors idiomatically; do not force Contabulate's vanilla-JS structure onto another framework.
4. Separate raw values from display values. Sorting, filtering, color scales, ranks, and export must use typed raw values; formatting belongs at render/export boundaries.

## Implement in dependency order

1. Render semantic table structure, stable column keys, typed values, loading/empty/error states, and horizontal overflow.
2. Add deterministic sorting and per-column filtering. Reset to page 1 when either changes. Expose active filters as removable chips with Clear all.
3. Add pagination over the filtered and sorted row set. Show page and total-row context; disable impossible navigation.
4. Add deep links that serialize the analytical view: query, row granularity, sort, column order/visibility, filters, and meaningful display toggles. Use `replaceState` for refinements and `pushState` for navigation-like drills so Back retraces exploration.
5. Add drill doors only where the target is predictable. Distinguish count-cell drill-down from ancestor-cell filtering, and carry meaningful scope across granularity changes.
6. Add full-result CSV export using visible columns in visible order and all filtered rows, not merely the current page. Escape commas, quotes, and newlines correctly.
7. Add optional columns, drag reorder, quantile color scales with a legend and contrast-safe text, search highlighting, and numeric rank hints where they improve analysis.
8. Apply Contabulate visual tokens or adapt them to the host brand while retaining hierarchy, density, and interaction affordances.

## Verify interactions, not just appearance

Test composed workflows: filter → sort → page → download; drill → change granularity → Back; add/reorder/remove columns → reload deep link; color-scale toggle after paging; keyboard-open and Escape-close popovers; mobile horizontal scrolling; and datasets with zero, one, tied, missing, negative, percentage, and large numeric values.

Treat the detailed acceptance checklist in [references/table-contract.md](references/table-contract.md) as the definition of done. If a requested shortcut conflicts with data correctness or shareability, explain the tradeoff before omitting it.

## Resources

- [references/table-contract.md](references/table-contract.md): behavior specification, visual tokens, edge cases, testing matrix, and current Contabulate source map.
