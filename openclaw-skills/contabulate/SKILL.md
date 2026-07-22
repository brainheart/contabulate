---
name: contabulate
description: Build, modify, publish, debug, or add corpora to Reinhard's Contabulate literary text exploration sites on GitHub Pages/Cloudflare. Use for Contabulate repos, corpus ingestion, JSON/static data generation, UI terminology, Unicode tokenization/search bugs, GitHub Pages custom domains/HTTPS cert issues, Cloudflare DNS for contabulate.org, and post-deploy verification/callbacks.
---

# Contabulate

## Core rule

Make it feel like magic, not devops archaeology. Prefer a complete verified publish over a plan. Use small, evidence-backed steps; write down what changed.

## Reasoning effort

For complex Contabulate work involving corpus generation, Unicode/tokenization, search semantics, deployment, HTTPS/DNS, or coordinated cross-repo changes, prefer the highest available reasoning effort or delegate to a high-reasoning coding agent. For small copy, styling, or single-file UI tweaks, keep the default effort and move quickly.

## Known system

- Owner/org: `brainheart`.
- Sites are GitHub Pages, usually `main` branch publishing `/docs`.
- DNS zone: `contabulate.org` on Cloudflare, zone id `fc4b35b6a9eb82e69f58afeeca7987f5`.
- Cloudflare token path: `~/.config/cloudflare/credentials.json`; never echo token values.
- Data layer preference: static JSON + gzip/incremental loading. Do not revive sql.js/WASM unless Reinhard explicitly asks.
- Current repo/domain map and project lessons: read `references/contabulate-workflow.md` when doing anything more than a tiny edit.
- Callback/watch reliability: read `references/callbacks.md` before starting watchers, detached jobs, waits, or long certificate checks.

## Standard workflow

1. **Inspect first**
   - Find the target repo/domain from the user request or `gh repo list brainheart`.
   - Check git status before editing.
   - For public-site issues, inspect live HTTP/HTTPS and GitHub Pages API state, not just local files.

2. **Implement with delegation when bounded**
   - For mechanical corpus parsing, UI porting, cross-repo refactors, or test writing, delegate to Codex/Claude Code rather than burning direct-chat context.
   - Keep direct chat for judgment: terminology, corpus choices, odd verification results.

3. **Verify locally**
   - Prefer existing tests (`npm test`, `npx playwright test`, build scripts) if present.
   - For search/tokenization changes, manually test representative accented/non-Latin terms.
   - For UI changes, inspect generated `/docs` artifacts and, when practical, run a local static server.

4. **Publish deliberately**
   - Commit with a plain descriptive message.
   - When a corpus changes or a new corpus is released, update and publish the main `contabulate.org` landing table too.
   - Update footer build timestamps on changed corpus sites and on the main landing page when its table changes.
   - Push to GitHub.
   - Check GitHub Pages state and live site. Verify HTTP and HTTPS separately.
   - If the site uses a custom domain, verify the CNAME file after publish.

5. **Report evidence**
   - Include repo, commit, tests/builds run, live URL, and any remaining caveat.
   - Do not paste log walls; summarize the surprising bit.

## GitHub Pages HTTPS playbook

When a Contabulate custom domain shows browser HTTPS warnings:

1. Confirm live cert:
   ```bash
   HOST=thucydides.contabulate.org
   echo | openssl s_client -connect "$HOST:443" -servername "$HOST" 2>/dev/null | openssl x509 -noout -subject -issuer -dates -ext subjectAltName
   curl -sSI "https://$HOST" | sed -n '1,12p'
   ```
2. Confirm GitHub Pages state:
   ```bash
   gh api repos/brainheart/<repo>/pages --jq '{status,cname,https_certificate,https_enforced}'
   ```
3. Confirm DNS:
   ```bash
   dig +short CNAME "$HOST" @1.1.1.1
   dig +short A "$HOST" @1.1.1.1
   dig +short AAAA "$HOST" @1.1.1.1
   dig +short CAA "$HOST" @1.1.1.1
   ```
4. Check no duplicate repo claims the same CNAME.
5. If GitHub is stuck on the generic `*.github.io` cert, do a clean reset: remove custom domain, wait for Pages to build with no CNAME, re-add it, then watch.
6. If still stuck in `authorization_created`, Cloudflare proxied mode can be a reversible fallback for the single subdomain. Record clearly that this is Cloudflare-edge HTTPS, not GitHub cert recovery.

Use `scripts/github-pages-https-rescue.sh` for steps 1-6 when appropriate.

## Pitfalls

- In zsh, avoid variable names like `path` and `status`; they can mutate `PATH` or be read-only. Use bash for nontrivial scripts.
- GitHub Pages API `PUT pages -f cname=...` creates commits like `Create CNAME`/`Delete CNAME`; pull afterward if maintaining a local clone.
- Browser cache may hide certificate changes; trust `openssl`/`curl` first.
- GitHub Pages `https_enforced=false` with Cloudflare proxied HTTPS can still look secure to users; state the distinction.
- Unicode bugs are common: normalize terms (NFC), use Unicode property escapes like `[\p{L}]+` with `u`, and test Hebrew nikud, Greek accents, and Latin diacritics.
