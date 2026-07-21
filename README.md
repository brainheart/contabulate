# Contabulate

**Table-based exploration of literary works.**

Landing page for the Contabulate project at [contabulate.org](https://contabulate.org).

## Instances

| Corpus | Language | URL |
|------|----------|-----|
| Tanakh (Hebrew Bible) | Hebrew | [tanakh.contabulate.org](https://tanakh.contabulate.org) |
| Luther Bible | German | [luther.contabulate.org](https://luther.contabulate.org) |
| King James Bible | English | [kjv.contabulate.org](https://kjv.contabulate.org) |
| Shakespeare (Complete Works) | English | [shakespeare.contabulate.org](https://shakespeare.contabulate.org) |
| Melville (Herman Melville) | English | [melville.contabulate.org](https://melville.contabulate.org) |
| Hawthorne (Nathaniel Hawthorne) | English | [hawthorne.contabulate.org](https://hawthorne.contabulate.org) |
| Kafka (Franz Kafka) | German | [kafka.contabulate.org](https://kafka.contabulate.org) |
| Homer (Iliad & Odyssey) | Greek | [homer.contabulate.org](https://homer.contabulate.org) |
| Aeneid (Virgil) | Latin | [aeneid.contabulate.org](https://aeneid.contabulate.org) |
| Divine Comedy (Dante) | Italian | [dante.contabulate.org](https://dante.contabulate.org) |
| Xenophon | Greek | [xenophon.contabulate.org](https://xenophon.contabulate.org) |
| Thucydides (History of the Peloponnesian War) | Greek | [thucydides.contabulate.org](https://thucydides.contabulate.org) |
| Austen (Jane Austen) | English | [austen.contabulate.org](https://austen.contabulate.org) |

Adding a new instance to the landing page is a one-line change: append its
base URL to [`docs/instances.json`](docs/instances.json). The page fetches
each instance's `/instance.json` at load time for its title, created and
updated dates, stats, and sample queries — nothing else needs to be hand-edited.

## Development

The site is a static HTML page served via GitHub Pages from the `docs/`
directory. `docs/index.html` renders the corpus table entirely client-side
from `docs/instances.json` plus each instance's live `/instance.json`; rows
that fail to load are shown as unavailable rather than breaking the page.

## Codex skills

Reusable Contabulate workflows live in `codex-skills/`. After cloning or
pulling this repository on a development machine, install user-level links so
the skills are available from any project on that machine:

```sh
./codex-skills/install-user-links.sh
```

Invoke them explicitly as `$contabulate-instances` and
`$contabulate-style-tables`.

## Author

[Reinhard Engels](https://everydaysystems.com)
