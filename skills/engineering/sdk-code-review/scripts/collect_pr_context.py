#!/usr/bin/env python3
"""Collect local PR context for an OMS SDK code review."""

from __future__ import annotations

import argparse
import collections
import json
import subprocess
import sys
from pathlib import Path


def git(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def git_stdout(args: list[str], cwd: Path, check: bool = True) -> str:
    result = git(args, cwd, check=check)
    return result.stdout.strip()


def git_root(cwd: Path) -> Path:
    result = git(["rev-parse", "--show-toplevel"], cwd, check=False)
    if result.returncode != 0:
        raise SystemExit("Not inside a git repository.")
    return Path(result.stdout.strip())


def valid_ref(repo: Path, ref: str) -> bool:
    result = git(["rev-parse", "--verify", f"{ref}^{{commit}}"], repo, check=False)
    return result.returncode == 0


def remote_head(repo: Path) -> str | None:
    result = git(["symbolic-ref", "refs/remotes/origin/HEAD", "--short"], repo, check=False)
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def choose_base(repo: Path, explicit_base: str | None) -> tuple[str, str]:
    candidates: list[str] = []
    if explicit_base:
        candidates.append(explicit_base)
    head = remote_head(repo)
    if head:
        candidates.append(head)
    candidates.extend(["origin/main", "origin/master", "origin/develop", "main", "master", "develop"])

    seen: set[str] = set()
    for ref in candidates:
        if ref in seen or not valid_ref(repo, ref):
            continue
        seen.add(ref)
        merge_base = git_stdout(["merge-base", ref, "HEAD"], repo, check=False)
        if merge_base:
            return ref, merge_base

    raise SystemExit(
        "Could not detect a base branch. Re-run with --base <ref>, for example --base origin/main."
    )


def parse_name_status(raw: str) -> list[dict[str, str]]:
    if not raw:
        return []
    parts = raw.split("\0")
    if parts and parts[-1] == "":
        parts.pop()

    files: list[dict[str, str]] = []
    i = 0
    while i < len(parts):
        status = parts[i]
        code = status[:1]
        if code in {"R", "C"}:
            old_path = parts[i + 1]
            path = parts[i + 2]
            files.append({"status": status, "path": path, "old_path": old_path})
            i += 3
        else:
            path = parts[i + 1]
            files.append({"status": status, "path": path})
            i += 2
    return files


def extension_bucket(path: str) -> str:
    name = Path(path).name
    if "." not in name:
        return "[no extension]"
    return Path(path).suffix.lower()


def collect(repo: Path, base_ref: str | None) -> dict[str, object]:
    base, merge_base = choose_base(repo, base_ref)
    branch = git_stdout(["branch", "--show-current"], repo, check=False) or "(detached HEAD)"
    head_sha = git_stdout(["rev-parse", "--short", "HEAD"], repo)
    base_sha = git_stdout(["rev-parse", "--short", merge_base], repo)
    status = git_stdout(["status", "--short"], repo, check=False)
    stat = git_stdout(["diff", "--stat", f"{merge_base}...HEAD"], repo, check=False)
    shortstat = git_stdout(["diff", "--shortstat", f"{merge_base}...HEAD"], repo, check=False)
    commits = git_stdout(["log", "--oneline", "--decorate", f"{merge_base}..HEAD"], repo, check=False)
    raw_files = git_stdout(["diff", "--name-status", "-z", f"{merge_base}...HEAD"], repo, check=False)
    files = parse_name_status(raw_files)
    buckets = collections.Counter(extension_bucket(file["path"]) for file in files)
    directories = collections.Counter(Path(file["path"]).parts[0] if Path(file["path"]).parts else "." for file in files)

    return {
        "repo": str(repo),
        "branch": branch,
        "base_ref": base,
        "base_sha": base_sha,
        "head_sha": head_sha,
        "changed_file_count": len(files),
        "changed_files": files,
        "extension_counts": dict(sorted(buckets.items())),
        "top_level_directory_counts": dict(sorted(directories.items())),
        "shortstat": shortstat,
        "stat": stat,
        "commits": commits,
        "working_tree_status": status,
    }


def emit_markdown(data: dict[str, object]) -> str:
    files = data["changed_files"]
    assert isinstance(files, list)
    lines = [
        "# PR Context",
        "",
        f"- Repository: `{data['repo']}`",
        f"- Branch: `{data['branch']}`",
        f"- Base: `{data['base_ref']}` at `{data['base_sha']}`",
        f"- Head: `{data['head_sha']}`",
        f"- Changed files: {data['changed_file_count']}",
    ]
    if data["shortstat"]:
        lines.append(f"- Diff summary: {data['shortstat']}")

    lines.extend(["", "## Changed Files", ""])
    if files:
        for item in files:
            assert isinstance(item, dict)
            status = item["status"]
            path = item["path"]
            if "old_path" in item:
                lines.append(f"- {status} `{item['old_path']}` -> `{path}`")
            else:
                lines.append(f"- {status} `{path}`")
    else:
        lines.append("- No committed changes detected against the selected base.")

    lines.extend(["", "## File Type Counts", ""])
    for ext, count in data["extension_counts"].items():  # type: ignore[union-attr]
        lines.append(f"- `{ext}`: {count}")

    lines.extend(["", "## Top-Level Areas", ""])
    for area, count in data["top_level_directory_counts"].items():  # type: ignore[union-attr]
        lines.append(f"- `{area}`: {count}")

    lines.extend(["", "## Commits", ""])
    if data["commits"]:
        lines.extend(str(data["commits"]).splitlines())
    else:
        lines.append("- No commits detected against the selected base.")

    lines.extend(["", "## Diff Stat", ""])
    if data["stat"]:
        lines.extend(str(data["stat"]).splitlines())
    else:
        lines.append("- Empty diff stat.")

    lines.extend(["", "## Working Tree Status", ""])
    if data["working_tree_status"]:
        lines.extend(str(data["working_tree_status"]).splitlines())
    else:
        lines.append("- Clean working tree.")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect local PR context for review.")
    parser.add_argument("--base", help="Base branch or commit to compare against.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of Markdown.")
    args = parser.parse_args()

    repo = git_root(Path.cwd())
    data = collect(repo, args.base)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print(emit_markdown(data), end="")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(exc.stderr or str(exc))
        raise SystemExit(exc.returncode)
