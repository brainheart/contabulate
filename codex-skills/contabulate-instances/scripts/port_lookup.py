#!/usr/bin/env python3
"""Add the English lookup and gloss columns to an instance's page.

The instance must already build `docs/data/glossary.json` (see the playbook's
"English lookup" section for the data contract). This script copies the shared
`glossary.js` from a donor instance and patches `docs/index.html` and
`docs/css/main.css`. Every patch is anchored on text the shared table shell is
known to contain and fails loudly when an anchor is missing or ambiguous, so
an instance with a divergent shell is reported rather than half-patched.

    port_lookup.py INSTANCE --donor DONOR --language Greek --lang grc [--dir rtl]

It is safe to run twice: an instance that already has the lookup is left alone.
"""
import argparse
import shutil
import sys
from pathlib import Path

CSS = """
/* English lookup above the term field. */
.lexicon { position: relative; display: flex; flex-wrap: wrap; align-items: center; gap: .5rem .75rem; padding-bottom: .85rem; margin-bottom: .85rem; border-bottom: 1px solid var(--border, #d9cfb8); }
.lexicon-input { flex: 1 1 14rem; max-width: 24rem; padding: .5rem .7rem; border: 1px solid var(--border, #d4c5b0); border-radius: 6px; background: #fff; font: inherit; color: inherit; }
.lexicon-hint { flex: 1 1 14rem; font-size: .9rem; }
.lexicon-results { flex: 1 1 100%; max-height: 24rem; overflow-y: auto; border: 1px solid var(--border, #d9cfb8); border-radius: 6px; background: #fffdf8; }
.lexicon-item { padding: .6rem .8rem; border-bottom: 1px solid var(--border, #e6dcc6); }
.lexicon-item:last-child { border-bottom: 0; }
.lexicon-head { display: flex; flex-wrap: wrap; align-items: baseline; gap: .35rem .8rem; }
.lexicon-insert { font: inherit; cursor: pointer; padding: .1rem .7rem; border: 1px solid var(--burgundy, #8b1538); border-radius: 6px; background: #fff; color: var(--burgundy, #8b1538); }
.lexicon-insert:hover, .lexicon-insert:focus-visible { background: var(--burgundy, #8b1538); color: #fff; }
.lexicon-lemma { font-size: 1.3rem; line-height: 1.6; }
.lexicon-meaning { font-weight: 600; }
.lexicon-meta, .lexicon-examples { font-size: .88rem; }
.lexicon-examples { margin: .15rem 0 .4rem; }
.lexicon-forms { display: flex; flex-wrap: wrap; align-items: center; gap: .35rem; margin-top: .35rem; }
.lexicon-form { font: inherit; font-size: .88rem; cursor: pointer; padding: .05rem .5rem; border: 1px solid var(--border, #d9cfb8); border-radius: 999px; background: #fff; color: inherit; }
.lexicon-form .lexicon-foreign { font-size: 1.1em; }
.lexicon-form:hover, .lexicon-form:focus-visible { border-color: var(--burgundy, #8b1538); color: var(--burgundy, #8b1538); }
.lexicon-root { border-style: dashed; }
.lexicon-empty { margin: .7rem .8rem; }
.word-gloss { min-width: 12rem; max-width: 26rem; }

/* Long search terms in a column header: one short line until expanded. */
.th-label-long { display: inline-block; max-width: 13rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; vertical-align: bottom; }
.th-label-long.is-expanded { min-width: 16rem; max-width: 24rem; white-space: normal; overflow-wrap: anywhere; line-height: 1.5; }
.term-col-expand { margin-left: .3rem; padding: 0 .35rem; border: 1px solid var(--border, #d4c5b0); border-radius: 999px; background: #fff; color: var(--burgundy, #8b1538); font: inherit; font-size: .72rem; line-height: 1.4; cursor: pointer; vertical-align: middle; }
.term-col-expand:hover, .term-col-expand:focus-visible { border-color: var(--burgundy, #8b1538); }
"""


def patches(language, lang, direction):
    """(anchor, replacement) pairs; each anchor must occur exactly once."""
    return [
        # 1. the shared module
        ('<script src="js/utils.js"></script>\n',
         '<script src="js/utils.js"></script>\n<script src="js/glossary.js"></script>\n'),
        # 2. the lookup box, above the term controls
        ('    <div class="controls">\n      <div class="controls-row">',
         f'''    <div class="controls">
      <div id="lexicon" class="lexicon is-hidden">
        <label class="label-strong" for="lexiconInput">Find a{'n' if language[:1] in 'AEIOU' else ''} {language} word by its English meaning:</label>
        <input id="lexiconInput" class="query-input lexicon-input" type="search" autocomplete="off" spellcheck="false" placeholder="e.g. love, light, word" aria-controls="lexiconResults">
        <span class="muted lexicon-hint">Pick a word to put it in the search box below, then hit “Add”.</span>
        <div id="lexiconResults" class="lexicon-results is-hidden" aria-live="polite"></div>
      </div>
      <div class="controls-row">'''),
        # 3. load the data with the rest; it is optional
        ('characterNameFilterConfig=null, commentaryInterestConfig=null;',
         'characterNameFilterConfig=null, commentaryInterestConfig=null, glossaryData=null;'),
        ('characterNameFilterConfig, commentaryInterestConfig] = await Promise.all([',
         'characterNameFilterConfig, commentaryInterestConfig, glossaryData] = await Promise.all(['),
        ("      loadJSON('data/commentary_interest.json').catch(() => null),\n    ]);",
         "      loadJSON('data/commentary_interest.json').catch(() => null),\n"
         "      // Reading aids only: the explorer works without them.\n"
         "      loadJSON('data/glossary.json').catch(() => null),\n    ]);"),
        # 4. initialise and wire the lookup
        ('  setLoadingState(false);\n\n  async function ensureAllLinesLoaded',
         '''  setLoadingState(false);

  // English glosses and dictionary forms (js/glossary.js). When the data is
  // missing, the lookup box and the gloss columns simply do not appear.
  const glossary = window.contabulateGlossary;
  const glossaryAvailable = !!(glossary && glossary.init(glossaryData));
  glossaryData = null;
  if (glossaryAvailable) {
    setElementHidden(document.getElementById('lexicon'), false);
    glossary.wireLookup({
      input: document.getElementById('lexiconInput'),
      results: document.getElementById('lexiconResults'),
      insert: (text, mode) => {
        matchMode.value = mode;
        if (mode === 'regex') ngramMode.value = '1';
        clearTermWarning();
        updateSegmentsMatchModeUI();
        q.value = text;
        q.dispatchEvent(new Event('input', { bubbles: true }));
        q.focus();
      }
    });
  }

  async function ensureAllLinesLoaded'''),
        # 5. gloss, dictionary form, and root on vocabulary rows
        ('        raw.push({\n          ngram,\n          count: tf,',
         '''        raw.push({
          ngram,
          gloss: glossaryAvailable ? glossary.ngramGloss(ngram) : '',
          lemma: (glossaryAvailable && n === 1) ? glossary.ngramLemma(ngram) : '',
          root: (glossaryAvailable && n === 1) ? glossary.ngramRoot(ngram) : '',
          count: tf,'''),
        ("      { key: 'ngram', label: vocabColumnLabel(granVal), defaultDir: 'asc', type: 'text' },\n"
         "      { key: 'count', label: 'Count', type: 'number', defaultDir: 'desc' },",
         '''      { key: 'ngram', label: vocabColumnLabel(granVal), defaultDir: 'asc', type: 'text' },
      ...(glossaryAvailable ? [{ key: 'gloss', label: 'English (word by word)', defaultDir: 'asc', type: 'text',
        tooltip: n === 1
          ? 'English glosses of this written form, most frequent first. A reading aid; it is not searched.'
          : 'The most frequent English gloss of each word, in order. A reading aid; it is not searched.' }] : []),
      ...((glossaryAvailable && n === 1) ? [
        { key: 'lemma', label: 'Dictionary form', defaultDir: 'asc', type: 'text',
          tooltip: 'The dictionary form (lemma) this written form belongs to. Several are listed when one spelling serves different words. A reading aid; it is not searched.' },
        ...(glossary.hasRoots() ? [{ key: 'root', label: 'Root', defaultDir: 'asc', type: 'text',
          tooltip: 'The root this word is built on. Filter this column to gather every form built on one root.' }] : []),
      ] : []),
      { key: 'count', label: 'Count', type: 'number', defaultDir: 'desc' },'''),
        ("        if (k === 'title' || k === 'play_title') td.classList.add('book-cell');",
         f'''        if (k === 'title' || k === 'play_title') td.classList.add('book-cell');
        if (k === 'lemma' || k === 'root') {{ td.lang = '{lang}'; td.dir = '{direction}'; }}
        if (k === 'gloss' && isVocabGranularity(granVal)) td.classList.add('word-gloss');'''),
        # 6. long terms in a header: one line, full text on hover, toggle to expand
        ('  let extraTerms = [];\n',
         '''  let extraTerms = [];
  // Declared early: a deep link draws term headers during startup.
  const LONG_TERM_LABEL = 28; // characters, including the leading "# " and quotes
  const expandedTermLabels = new Set();
'''),
        ("      if (Number.isInteger(c.termIdx)) {\n        const removeBtn = document.createElement('button');",
         '''      // A long term (typically a pattern inserted from the lookup) is cut to
      // one short line so the header row stays low. Hovering shows the whole
      // term; the small toggle expands it in place, which also works on
      // touch screens. The full text stays in the DOM for CSV and links.
      if (Number.isInteger(c.termIdx) && Array.from(c.label).length > LONG_TERM_LABEL) {
        const expanded = expandedTermLabels.has(c.label);
        labelSpan.classList.add('th-label-long');
        labelSpan.classList.toggle('is-expanded', expanded);
        th.title = `${c.label}\\nClick to sort.`;
        const toggle = document.createElement('button');
        toggle.type = 'button';
        toggle.className = 'term-col-expand';
        const sync = (open) => {
          toggle.textContent = open ? 'less' : 'more';
          toggle.title = open ? 'Shorten this term' : 'Show the whole term';
          toggle.setAttribute('aria-label', toggle.title);
          toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
        };
        sync(expanded);
        toggle.addEventListener('click', (e) => {
          e.stopPropagation();
          const open = !labelSpan.classList.contains('is-expanded');
          labelSpan.classList.toggle('is-expanded', open);
          if (open) expandedTermLabels.add(c.label); else expandedTermLabels.delete(c.label);
          sync(open);
        });
        th.appendChild(toggle);
      }
      if (Number.isInteger(c.termIdx)) {
        const removeBtn = document.createElement('button');'''),
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("instance", type=Path)
    parser.add_argument("--donor", type=Path, required=True, help="instance to copy docs/js/glossary.js from")
    parser.add_argument("--language", required=True, help='language name for the label, e.g. "Greek"')
    parser.add_argument("--lang", required=True, help="BCP 47 tag for lemma cells, e.g. grc")
    parser.add_argument("--dir", default="ltr", choices=["ltr", "rtl"])
    parser.add_argument("--check", action="store_true", help="report missing anchors without writing")
    args = parser.parse_args()

    index = args.instance / "docs/index.html"
    css = args.instance / "docs/css/main.css"
    html = index.read_text(encoding="utf-8")
    if 'id="lexicon"' in html:
        print("Lookup already present; nothing to do.")
        return 0
    problems = []
    for anchor, replacement in patches(args.language, args.lang, args.dir):
        count = html.count(anchor)
        if count != 1:
            problems.append(f"anchor found {count} times: {anchor[:70]!r}")
            continue
        html = html.replace(anchor, replacement)
    if problems:
        print("Cannot patch this shell:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 1
    if args.check:
        print("All anchors found.")
        return 0
    index.write_text(html, encoding="utf-8")
    css.write_text(css.read_text(encoding="utf-8").rstrip("\n") + "\n" + CSS, encoding="utf-8")
    shutil.copyfile(args.donor / "docs/js/glossary.js", args.instance / "docs/js/glossary.js")
    print(f"Patched {index} and {css}; copied glossary.js from {args.donor}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
