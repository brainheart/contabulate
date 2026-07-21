#!/usr/bin/env python3
"""Read-only preflight for a Contabulate instance and optional hub entry."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse


CURATED_FIELDS = (
    "id",
    "emoji",
    "title",
    "tagline",
    "language",
    "created",
    "url",
    "source",
    "sample_queries",
)
META_REQUIRED = CURATED_FIELDS + ("text_label", "segment_label")
STAT_FIELDS = (
    "texts",
    "text_label",
    "segments",
    "segment_label",
    "words",
    "distinct_words",
    "commentaries",
    "comments",
)


def load_json(path: Path, errors: list[str]):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing {path}")
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON in {path}: {exc}")
    return None


def iso_date(value, label: str, errors: list[str]):
    try:
        return dt.date.fromisoformat(value)
    except (TypeError, ValueError):
        errors.append(f"{label} must be YYYY-MM-DD, got {value!r}")
        return None


def normalized_base(value: str) -> str:
    return value.rstrip("/") + "/"


def git_output(root: Path, *args: str) -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(root), *args],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("instance", type=Path, help="instance repository root")
    parser.add_argument("--hub-root", type=Path, help="contabulate.org hub repository root")
    parser.add_argument(
        "--require-hub",
        action="store_true",
        help="treat a missing hub URL or README row as an error",
    )
    args = parser.parse_args()

    root = args.instance.expanduser().resolve()
    errors: list[str] = []
    warnings: list[str] = []

    repo_root = git_output(root, "rev-parse", "--show-toplevel")
    if not repo_root:
        errors.append(f"{root} is not a Git repository")
    elif Path(repo_root).resolve() != root:
        errors.append(f"instance path is not its repository root; Git root is {repo_root}")

    meta = load_json(root / "instance-meta.json", errors)
    published = load_json(root / "docs" / "instance.json", errors)

    if isinstance(meta, dict):
        for key in META_REQUIRED:
            if key not in meta:
                errors.append(f"instance-meta.json missing {key}")
        url = meta.get("url", "")
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.netloc or parsed.path not in ("", "/"):
            errors.append(f"instance-meta.json url must be an HTTPS base URL, got {url!r}")
        if url and not url.endswith("/"):
            errors.append("instance-meta.json url must end with /")
        iso_date(meta.get("created"), "instance-meta.json created", errors)
        if not isinstance(meta.get("sample_queries"), list):
            errors.append("instance-meta.json sample_queries must be an array")
        else:
            for index, query in enumerate(meta["sample_queries"]):
                if not isinstance(query, dict) or not query.get("label") or not query.get("url"):
                    errors.append(f"sample_queries[{index}] must have nonempty label and url")
                    continue
                query_url = urlparse(str(query["url"]))
                if query_url.scheme != "https" or query_url.netloc != parsed.netloc:
                    errors.append(f"sample_queries[{index}] must use canonical host {parsed.netloc}")

        cname_path = root / "docs" / "CNAME"
        try:
            cname = cname_path.read_text(encoding="utf-8").strip()
            if cname != parsed.netloc:
                errors.append(f"docs/CNAME is {cname!r}; expected {parsed.netloc!r}")
        except FileNotFoundError:
            errors.append(f"missing {cname_path}")

    if isinstance(published, dict):
        if published.get("schema") != 1:
            errors.append("docs/instance.json schema must be 1")
        if isinstance(meta, dict):
            for key in CURATED_FIELDS:
                if published.get(key) != meta.get(key):
                    errors.append(f"docs/instance.json {key} does not match instance-meta.json")
        created = iso_date(published.get("created"), "docs/instance.json created", errors)
        updated = iso_date(published.get("updated"), "docs/instance.json updated", errors)
        if created and updated and updated < created:
            errors.append("docs/instance.json updated predates created")
        stats = published.get("stats")
        if not isinstance(stats, dict):
            errors.append("docs/instance.json stats must be an object")
        else:
            for key in STAT_FIELDS:
                if key not in stats:
                    errors.append(f"docs/instance.json stats missing {key}")
            for key in ("texts", "segments", "words", "distinct_words", "commentaries", "comments"):
                value = stats.get(key)
                if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                    errors.append(f"docs/instance.json stats.{key} must be a nonnegative integer")
            if isinstance(meta, dict):
                for source_key in ("text_label", "segment_label"):
                    if stats.get(source_key) != meta.get(source_key):
                        errors.append(f"docs/instance.json stats.{source_key} does not match instance-meta.json")

    if args.hub_root:
        hub = args.hub_root.expanduser().resolve()
        hub_repo_root = git_output(hub, "rev-parse", "--show-toplevel")
        if not hub_repo_root or Path(hub_repo_root).resolve() != hub:
            errors.append(f"hub path is not a Git repository root: {hub}")
        urls = load_json(hub / "docs" / "instances.json", errors)
        canonical = normalized_base(meta.get("url", "")) if isinstance(meta, dict) and meta.get("url") else ""
        missing = not isinstance(urls, list) or canonical not in [normalized_base(str(item)) for item in urls]
        if canonical and missing:
            message = f"hub docs/instances.json does not contain {canonical}"
            (errors if args.require_hub else warnings).append(message)
        try:
            readme = (hub / "README.md").read_text(encoding="utf-8")
            host = urlparse(canonical).netloc
            if host and host not in readme:
                message = f"hub README.md does not mention {host}"
                (errors if args.require_hub else warnings).append(message)
        except FileNotFoundError:
            errors.append(f"missing {hub / 'README.md'}")

    branch = git_output(root, "branch", "--show-current") or "(detached/unknown)"
    remote = git_output(root, "remote", "get-url", "origin") or "(no origin)"
    dirty = git_output(root, "status", "--short")
    print(f"Instance: {root}")
    print(f"Git: branch={branch} origin={remote} dirty={'yes' if dirty else 'no'}")
    for warning in warnings:
        print(f"WARN: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        print(f"FAIL: {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"PASS: 0 errors, {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
