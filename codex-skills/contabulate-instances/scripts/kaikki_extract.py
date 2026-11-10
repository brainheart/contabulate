#!/usr/bin/env python3
"""Reduce a kaikki.org Wiktionary dictionary to what one instance needs.

kaikki.org publishes English Wiktionary as one JSON line per entry, per
language (hundreds of megabytes). An instance needs only two things from it:
which dictionary words each of its written forms can belong to, and a short
English gloss for those words. This script streams the big file once and
writes a compact extract that the instance commits and pins by SHA-256, so
its build never needs the download.

    kaikki_extract.py DICTIONARY.jsonl TOKENS.json OUT.json --language la

Extract format:
  {"source": {...}, "forms": {normalized form: [[lemma, pos, kind], ...]},
   where kind is "self" (the form is that dictionary word's own headword),
   "form" (an inflected form of it), or "alt" (reached through a variant
   spelling, the weakest evidence),
   "lemmas": {"lemma\\tpos": [gloss, ...]}}

Wiktionary text is CC BY-SA 3.0 / GFDL; credit Wiktionary and kaikki.org.
"""
import argparse
import datetime
import hashlib
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

ENCLITICS = {"la": ("que", "ne", "ve")}
LEXICAL_POS = {
    "noun", "verb", "adj", "adv", "prep", "conj", "pron", "name", "num", "particle", "intj", "det",
    "article", "postp", "phrase", "prep_phrase", "contraction",
}


def normalize(word, language):
    """The spelling under which a form is looked up. Mirrors the instance's
    own search form as far as letters go: case and diacritics are dropped;
    Latin also reads j as i and writes out the ligatures."""
    text = unicodedata.normalize("NFD", word.lower())
    if language == "la":
        text = "".join(c for c in text if not unicodedata.combining(c))
        text = text.replace("j", "i").replace("æ", "ae").replace("œ", "oe")
    elif language == "it":
        # Accents distinguish words in Italian; keep them, but compose.
        pass
    return unicodedata.normalize("NFC", text)


def candidates(token, language):
    """Lookup keys for a token: itself, then without an enclitic."""
    keys = [normalize(token, language)]
    for enclitic in ENCLITICS.get(language, ()):
        if keys[0].endswith(enclitic) and len(keys[0]) > len(enclitic) + 1:
            keys.append(keys[0][: -len(enclitic)])
    return keys


def clean_gloss(gloss):
    text = re.sub(r"\s+", " ", gloss).strip().rstrip(".:;")
    return text


def is_plain_form(form):
    return bool(form) and " " not in form and "-" not in form and not any(c.isdigit() for c in form)


def extract(dictionary_path, tokens, language, max_glosses=4, max_hops=3):
    wanted = set()
    for token in tokens:
        wanted.update(candidates(token, language))
    direct = defaultdict(list)         # wanted form -> [(normalized word, pos)] it is, or is listed under
    listed_as_variant = set()          # (wanted form, node) pairs that come from an "alternative form" listing
    parents = defaultdict(list)        # (normalized word, pos) -> [(normalized target, pos, is variant)]
    glosses = defaultdict(list)        # (word, pos) -> [gloss], for entries with a meaning of their own
    spellings = defaultdict(list)      # (normalized word, pos) -> [word as Wiktionary heads it]
    entries = 0
    with open(dictionary_path, encoding="utf-8") as handle:
        for line in handle:
            entry = json.loads(line)
            entries += 1
            word = entry.get("word") or ""
            pos = entry.get("pos") or ""
            if not word or pos not in LEXICAL_POS or not is_plain_form(word):
                continue
            key = normalize(word, language)
            node = (key, pos)
            if key in wanted and node not in direct[key]:
                direct[key].append(node)
            for sense in entry.get("senses", ()):
                variant = not sense.get("form_of") and bool(sense.get("alt_of"))
                targets = sense.get("form_of") or sense.get("alt_of")
                if targets:
                    # "nobis" is a form of "nos", itself a form of "ego";
                    # "dicentes" of "dicens", a participle of "dico". Record
                    # the link and follow the chain afterwards.
                    for target in targets:
                        lemma = normalize((target.get("word") or "").strip(), language)
                        if lemma and lemma != key and (lemma, pos, variant) not in parents[node]:
                            parents[node].append((lemma, pos, variant))
                    continue
                texts = sense.get("glosses") or ()
                if texts and "no-gloss" not in (sense.get("tags") or ()):
                    gloss = clean_gloss(texts[-1])
                    if word not in spellings[node]:
                        spellings[node].append(word)
                    if gloss and gloss not in glosses[(word, pos)] and len(glosses[(word, pos)]) < max_glosses:
                        glosses[(word, pos)].append(gloss)
            # The inflection table of any entry lists forms that belong to it.
            for form in entry.get("forms", ()):
                text = form.get("form") or ""
                tags = form.get("tags") or ()
                if not is_plain_form(text) or "table-tags" in tags or "inflection-template" in tags:
                    continue
                form_key = normalize(text, language)
                if form_key in wanted and form_key != key:
                    if node not in direct[form_key]:
                        direct[form_key].append(node)
                        if "alternative" in tags:
                            listed_as_variant.add((form_key, node))
                    elif "alternative" not in tags:
                        listed_as_variant.discard((form_key, node))

    def dictionary_words(node, hops=0, seen=(), variant=False):
        """Entries with a meaning of their own that a node leads to, each
        with whether a variant spelling lies on the way. A node that only
        points elsewhere (a form, a participle, a variant) is followed."""
        if node in seen or hops > max_hops:
            return []
        found = [((word, node[1]), variant) for word in spellings.get(node, ())]
        for target, pos, is_variant in parents.get(node, ()):
            for answer in dictionary_words((target, pos), hops + 1, seen + (node,), variant or is_variant):
                if answer[0] not in [f[0] for f in found]:
                    found.append(answer)
        return found

    out_forms = {}
    used = set()
    for key, nodes in direct.items():
        resolved = {}
        for node in nodes:
            for (word, pos), variant in dictionary_words(node, variant=(key, node) in listed_as_variant):
                if normalize(word, language) == key and node == (key, pos) and not variant:
                    kind = "self"
                else:
                    kind = "alt" if variant else "form"
                rank = {"self": 0, "form": 1, "alt": 2}
                if (word, pos) not in resolved or rank[kind] < rank[resolved[(word, pos)]]:
                    resolved[(word, pos)] = kind
        if resolved:
            out_forms[key] = [[word, pos, kind] for (word, pos), kind in resolved.items()]
            used.update(resolved)
    out_lemmas = {f"{word}\t{pos}": glosses[(word, pos)] for word, pos in sorted(used)}
    return out_forms, out_lemmas, entries


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("dictionary", type=Path)
    parser.add_argument("tokens", type=Path, help="the instance's docs/data/tokens.json")
    parser.add_argument("out", type=Path)
    parser.add_argument("--language", required=True, choices=["la", "de", "it", "grc"])
    parser.add_argument("--url", default="")
    parser.add_argument("--published", default="", help="Last-Modified date of the download")
    args = parser.parse_args()

    tokens = list(json.loads(args.tokens.read_text(encoding="utf-8")))
    forms, lemmas, entries = extract(args.dictionary, tokens, args.language)
    covered = sum(1 for t in tokens if any(k in forms for k in candidates(t, args.language)))
    payload = {
        "source": {
            "name": "English Wiktionary via kaikki.org (Wiktextract)",
            "url": args.url,
            "published": args.published,
            "extracted": datetime.date.today().isoformat(),
            "license": "CC BY-SA 3.0 / GFDL (Wiktionary contributors)",
            "language": args.language,
        },
        "forms": dict(sorted(forms.items())),
        "lemmas": lemmas,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    digest = hashlib.sha256(args.out.read_bytes()).hexdigest()
    print(f"{entries} entries read; {covered} of {len(tokens)} written forms found "
          f"({covered / max(1, len(tokens)):.1%}); {len(lemmas)} dictionary words.")
    print(f"sha256 {digest}  {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
