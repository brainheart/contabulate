# Callback and Watcher Reliability

Use this for any Contabulate task that waits on GitHub Pages, DNS, certificate issuance, long builds, background coding agents, or remote propagation. The lesson generalizes: a job being started is not the same as the user being notified.

## Preferred order

1. **Managed TaskFlow/subagent** for multi-step waits or work that may outlive the chat turn.
2. **OpenClaw background exec with explicit process tracking** for simple watchers.
3. **`nohup` shell watcher** only when necessary; treat it as fragile and prove it is running.

## Start-of-watcher contract

Tell Reinhard, briefly:

- What is being watched.
- Expected deadline or next decision point.
- PID/session id and log path when available.
- What callback path will be used.

Example:

> Watcher started: PID 12345, log `/tmp/foo.log`, deadline ~10:40 ET. It will message when cert approval appears or when it switches to fallback.

## Reliable callback pattern

- Prefer `openclaw system event --mode now --expect-final --text "..."` when sending a completion event from a shell script.
- Avoid identical repeated callback text; prompt dedup can suppress repeated messages within 24h.
- Include concrete result and evidence in the callback text, not just "done".
- After starting a watcher, immediately verify it is alive and has written the first log line.
- If the user later asks, inspect the log before answering.

## Shell watcher hygiene

- Run nontrivial watcher scripts under bash (`#!/usr/bin/env bash`, `set -euo pipefail`).
- Avoid zsh reserved/tied names: `path`, `status`, `options`, etc.
- Log every state transition with timestamp.
- Make irreversible or external changes explicit and reversible. For Cloudflare fallback, record previous DNS state and revert on failed verification.
- Do not log secrets.

## Completion criteria

A watcher is not complete until both are true:

1. The technical condition was verified (e.g., curl/openssl/Pages API).
2. The user notification path was attempted and, when possible, verified.

If notification delivery cannot be verified, say so in the next direct response.
