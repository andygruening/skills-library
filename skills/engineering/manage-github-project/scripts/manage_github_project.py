#!/usr/bin/env python3
"""Manage repository-scoped GitHub Project issue workflows through gh."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any


CANONICAL_STAGES: dict[str, list[str]] = {
    "ready": ["ready", "sprint", "todo", "to do", "selected", "planned", "next up", "queued"],
    "in-progress": ["in progress", "doing", "active", "started", "working", "wip"],
    "blocked": ["blocked", "stuck", "needs input", "needs info", "on hold", "waiting"],
    "in-review": ["in review", "review", "reviewing", "pr open", "pull request", "code review"],
    "finished": ["done", "finished", "complete", "completed", "closed", "shipped"],
}

DEFAULT_STAGE_OPTIONS = ["Ready", "In Progress", "Blocked", "In Review", "Finished"]
STAGE_FIELD_NAMES = ["Codex Status", "Status", "Stage", "State", "Workflow", "Kanban"]
MUTATING_COMMANDS = {"mark-stage", "comment", "react", "edit-issue"}


@dataclass
class ProjectContext:
    project_number: str
    owner: str
    repo: str
    stage_field: str
    stage_options: list[str]


def run_gh(args: list[str], *, parse_json: bool = False) -> Any:
    result = subprocess.run(
        ["gh", *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        command = "gh " + " ".join(args)
        raise SystemExit(f"{command} failed\n{result.stderr.strip()}")
    if parse_json:
        if not result.stdout.strip():
            return None
        return json.loads(result.stdout)
    return result.stdout.rstrip("\n")


def run_git(args: list[str]) -> str | None:
    result = subprocess.run(
        ["git", *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def normalize(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def similarity(left: str, right: str) -> float:
    left_norm = normalize(left)
    right_norm = normalize(right)
    if not left_norm or not right_norm:
        return 0.0
    if left_norm == right_norm:
        return 1.0
    if left_norm in right_norm or right_norm in left_norm:
        return 0.88
    return SequenceMatcher(None, left_norm, right_norm).ratio()


def classify_stage(stage: str | None) -> str:
    best = ("other", 0.0)
    for canonical, aliases in CANONICAL_STAGES.items():
        for alias in aliases:
            score = similarity(stage or "", alias)
            if score > best[1]:
                best = (canonical, score)
    return best[0] if best[1] >= 0.72 else "other"


def best_option_for_stage(canonical_or_value: str, options: list[str]) -> str | None:
    desired = CANONICAL_STAGES.get(canonical_or_value, [canonical_or_value])
    best = (None, 0.0)
    for option in options:
        for alias in desired:
            score = similarity(option, alias)
            if score > best[1]:
                best = (option, score)
    if best[0] and best[1] >= 0.72:
        return best[0]
    if canonical_or_value not in CANONICAL_STAGES:
        return canonical_or_value
    return None


def repo_from_remote(remote_url: str) -> str | None:
    patterns = [
        r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$",
        r"/repos/(?P<owner>[^/]+)/(?P<repo>[^/]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, remote_url)
        if match:
            return f"{match.group('owner')}/{match.group('repo').removesuffix('.git')}"
    return None


def detect_repo(explicit_repo: str | None) -> str:
    if explicit_repo:
        return explicit_repo
    try:
        repo = run_gh(["repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"])
        if repo:
            return repo
    except SystemExit:
        pass
    remote = run_git(["remote", "get-url", "origin"])
    if remote:
        parsed = repo_from_remote(remote)
        if parsed:
            return parsed
    raise SystemExit("Could not infer repository. Run inside a git checkout or pass --repo OWNER/REPO.")


def owner_repo_issue_from_url(url: str) -> tuple[str, str]:
    match = re.search(r"github\.com/([^/]+/[^/]+)/issues/([0-9]+)", url)
    if not match:
        raise SystemExit(f"Could not parse GitHub issue URL: {url}")
    return match.group(1), match.group(2)


def split_repo_issue(repo: str | None, issue: str | None, url: str | None) -> tuple[str, str]:
    if url:
        return owner_repo_issue_from_url(url)
    if not repo or not issue:
        raise SystemExit("Pass --url or both --repo and --issue.")
    return repo, str(issue)


def as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def field_records(raw: Any) -> list[dict[str, Any]]:
    if isinstance(raw, dict):
        for key in ("fields", "nodes", "items"):
            if isinstance(raw.get(key), list):
                return raw[key]
    if isinstance(raw, list):
        return raw
    return []


def field_options(field: dict[str, Any]) -> list[str]:
    options = field.get("options") or field.get("singleSelectOptions") or []
    names = []
    for option in as_list(options):
        if isinstance(option, dict):
            name = option.get("name")
            if name:
                names.append(str(name))
        elif isinstance(option, str):
            names.append(option)
    return names


def field_name(field: dict[str, Any]) -> str:
    return str(field.get("name") or field.get("fieldName") or "")


def choose_stage_field(fields: list[dict[str, Any]]) -> tuple[str | None, list[str]]:
    best_field: dict[str, Any] | None = None
    best_score = 0.0
    for field in fields:
        name = field_name(field)
        options = field_options(field)
        name_score = max(similarity(name, candidate) for candidate in STAGE_FIELD_NAMES)
        option_hits = sum(1 for canonical in CANONICAL_STAGES if best_option_for_stage(canonical, options))
        score = name_score + (option_hits * 0.35)
        if score > best_score:
            best_field = field
            best_score = score
    if best_field and best_score >= 0.72:
        return field_name(best_field), field_options(best_field)
    return None, []


def create_codex_status_field(project_number: str, owner: str, *, apply: bool) -> tuple[str, list[str]]:
    args = [
        "project",
        "field-create",
        project_number,
        "--owner",
        owner,
        "--name",
        "Codex Status",
        "--data-type",
        "SINGLE_SELECT",
        "--single-select-options",
        ",".join(DEFAULT_STAGE_OPTIONS),
    ]
    if not apply:
        print("DRY RUN: would run gh " + " ".join(args), file=sys.stderr)
        return "Codex Status", DEFAULT_STAGE_OPTIONS
    run_gh(args)
    return "Codex Status", DEFAULT_STAGE_OPTIONS


def project_context(args: argparse.Namespace, *, allow_create_field: bool = False) -> ProjectContext:
    repo = detect_repo(getattr(args, "repo", None))
    fields = field_records(
        run_gh(
            ["project", "field-list", str(args.project_number), "--owner", args.owner, "--format", "json"],
            parse_json=True,
        )
    )
    requested_field = getattr(args, "stage_field", None)
    if requested_field:
        matched = next((field for field in fields if field_name(field) == requested_field), None)
        return ProjectContext(str(args.project_number), args.owner, repo, requested_field, field_options(matched or {}))

    stage_field, options = choose_stage_field(fields)
    if stage_field:
        return ProjectContext(str(args.project_number), args.owner, repo, stage_field, options)

    existing_codex = next((field for field in fields if field_name(field) == "Codex Status"), None)
    if existing_codex:
        return ProjectContext(str(args.project_number), args.owner, repo, "Codex Status", field_options(existing_codex))

    if allow_create_field:
        stage_field, options = create_codex_status_field(str(args.project_number), args.owner, apply=args.apply)
        return ProjectContext(str(args.project_number), args.owner, repo, stage_field, options)

    raise SystemExit("Could not find a usable Status/Stage field. Re-run scan with --apply to create Codex Status.")


def project_items(ctx: ProjectContext, limit: int) -> list[dict[str, Any]]:
    query = f"repo:{ctx.repo} is:issue"
    raw = run_gh(
        [
            "project",
            "item-list",
            ctx.project_number,
            "--owner",
            ctx.owner,
            "--query",
            query,
            "--field",
            ctx.stage_field,
            "--limit",
            str(limit),
            "--format",
            "json",
        ],
        parse_json=True,
    )
    if isinstance(raw, dict):
        return as_list(raw.get("items") or raw.get("nodes"))
    return as_list(raw)


def item_content(item: dict[str, Any]) -> dict[str, Any]:
    content = item.get("content")
    if isinstance(content, dict):
        return content
    return item


def item_url(item: dict[str, Any]) -> str | None:
    content = item_content(item)
    return content.get("url") or item.get("url")


def item_title(item: dict[str, Any]) -> str:
    content = item_content(item)
    return str(content.get("title") or item.get("title") or "")


def item_number(item: dict[str, Any]) -> str | None:
    content = item_content(item)
    number = content.get("number") or item.get("number")
    return str(number) if number is not None else None


def item_stage(item: dict[str, Any], stage_field: str) -> str | None:
    candidates = [
        item.get(stage_field),
        item.get(stage_field.lower()),
        item.get(normalize(stage_field).replace(" ", "_")),
        item.get("status"),
        item.get("stage"),
    ]
    for candidate in candidates:
        if isinstance(candidate, str) and candidate:
            return candidate
        if isinstance(candidate, dict) and candidate.get("name"):
            return str(candidate["name"])
    for key in ("fieldValues", "fields"):
        values = item.get(key)
        if isinstance(values, dict):
            value = values.get(stage_field) or values.get(stage_field.lower())
            if isinstance(value, str):
                return value
            if isinstance(value, dict) and value.get("name"):
                return str(value["name"])
        for value in as_list(values):
            if not isinstance(value, dict):
                continue
            if value.get("name") == stage_field or value.get("fieldName") == stage_field:
                raw = value.get("value") or value.get("name") or value.get("text")
                if isinstance(raw, dict):
                    raw = raw.get("name")
                if raw:
                    return str(raw)
    return None


def issue_view(repo: str, issue: str) -> dict[str, Any]:
    data = run_gh(
        [
            "issue",
            "view",
            issue,
            "--repo",
            repo,
            "--json",
            "number,title,body,url,state,author,assignees,labels",
        ],
        parse_json=True,
    )
    data["comments"] = issue_comments(repo, issue)
    return data


def issue_comments(repo: str, issue: str) -> list[dict[str, Any]]:
    raw = run_gh(
        [
            "api",
            f"repos/{repo}/issues/{issue}/comments",
            "--paginate",
            "-H",
            "Accept: application/vnd.github+json",
        ],
        parse_json=True,
    )
    return as_list(raw)


def compact_comment(comment: dict[str, Any]) -> dict[str, Any]:
    reactions = comment.get("reactions") or {}
    return {
        "id": comment.get("id"),
        "author": (comment.get("user") or {}).get("login"),
        "created_at": comment.get("created_at"),
        "thumbs_up_count": reactions.get("+1", 0),
        "body": comment.get("body") or "",
    }


def issue_summary_from_item(item: dict[str, Any], stage_field: str) -> dict[str, Any]:
    url = item_url(item)
    number = item_number(item)
    return {
        "number": number,
        "title": item_title(item),
        "url": url,
        "stage": item_stage(item, stage_field),
        "stage_class": classify_stage(item_stage(item, stage_field)),
    }


def scan(args: argparse.Namespace) -> None:
    ctx = project_context(args, allow_create_field=True)
    items = project_items(ctx, args.limit)
    buckets: dict[str, list[dict[str, Any]]] = {
        "ready_items": [],
        "blocked_items": [],
        "other_items": [],
        "comments_needing_attention": [],
    }
    observed_options = set(ctx.stage_options)

    for item in items:
        summary = issue_summary_from_item(item, ctx.stage_field)
        if summary["stage"]:
            observed_options.add(summary["stage"])
        stage_class = summary["stage_class"]
        if stage_class == "ready":
            repo, issue = owner_repo_issue_from_url(summary["url"])
            detail = issue_view(repo, issue)
            summary["body"] = detail.get("body", "")
            buckets["ready_items"].append(summary)
            continue
        if stage_class == "blocked":
            repo, issue = owner_repo_issue_from_url(summary["url"])
            detail = issue_view(repo, issue)
            summary["body"] = detail.get("body", "")
            summary["comments"] = [compact_comment(comment) for comment in detail.get("comments", [])]
            buckets["blocked_items"].append(summary)
            continue

        buckets["other_items"].append(summary)
        if summary["url"]:
            repo, issue = owner_repo_issue_from_url(summary["url"])
            for comment in issue_comments(repo, issue):
                compact = compact_comment(comment)
                if compact["thumbs_up_count"] == 0:
                    buckets["comments_needing_attention"].append(
                        {
                            "issue_number": summary["number"],
                            "issue_title": summary["title"],
                            "issue_url": summary["url"],
                            "issue_stage": summary["stage"],
                            **compact,
                        }
                    )

    output = {
        "project": {
            "number": ctx.project_number,
            "owner": ctx.owner,
            "repo": ctx.repo,
            "stage_field": ctx.stage_field,
            "stage_options": sorted(observed_options),
            "stage_mappings": {
                canonical: best_option_for_stage(canonical, sorted(observed_options))
                for canonical in CANONICAL_STAGES
            },
        },
        **buckets,
    }
    emit(output, args.format)


def mark_stage(args: argparse.Namespace) -> None:
    ctx = project_context(args, allow_create_field=True)
    options = ctx.stage_options or DEFAULT_STAGE_OPTIONS
    value = best_option_for_stage(args.stage, options) or args.stage
    command = [
        "project",
        "item-edit",
        ctx.project_number,
        "--owner",
        ctx.owner,
        "--url",
        args.url,
        "--field",
        ctx.stage_field,
        "--value",
        value,
    ]
    if not args.apply:
        emit({"dry_run": True, "command": ["gh", *command], "stage_value": value}, args.format)
        return
    run_gh(command)
    emit({"updated": True, "url": args.url, "field": ctx.stage_field, "value": value}, args.format)


def add_comment(args: argparse.Namespace) -> None:
    repo, issue = split_repo_issue(args.repo, args.issue, args.url)
    body = args.body
    if args.body_file:
        with open(args.body_file, "r", encoding="utf-8") as handle:
            body = handle.read()
    if not body:
        raise SystemExit("Pass --body or --body-file.")
    command = ["issue", "comment", issue, "--repo", repo, "--body", body]
    if not args.apply:
        emit({"dry_run": True, "command": ["gh", "issue", "comment", issue, "--repo", repo, "--body", body]}, args.format)
        return
    run_gh(command)
    emit({"commented": True, "repo": repo, "issue": issue}, args.format)


def react(args: argparse.Namespace) -> None:
    repo = detect_repo(args.repo)
    command = [
        "api",
        "--method",
        "POST",
        f"repos/{repo}/issues/comments/{args.comment_id}/reactions",
        "-H",
        "Accept: application/vnd.github+json",
        "-f",
        "content=+1",
    ]
    if not args.apply:
        emit({"dry_run": True, "command": ["gh", *command]}, args.format)
        return
    run_gh(command)
    emit({"reacted": True, "repo": repo, "comment_id": args.comment_id, "content": "+1"}, args.format)


def edit_issue(args: argparse.Namespace) -> None:
    repo, issue = split_repo_issue(args.repo, args.issue, args.url)
    command = ["issue", "edit", issue, "--repo", repo]
    if args.title:
        command.extend(["--title", args.title])
    if args.body_file:
        command.extend(["--body-file", args.body_file])
    if len(command) == 5:
        raise SystemExit("Pass --title and/or --body-file.")
    if not args.apply:
        emit({"dry_run": True, "command": ["gh", *command]}, args.format)
        return
    run_gh(command)
    emit({"edited": True, "repo": repo, "issue": issue}, args.format)


def fetch_issue(args: argparse.Namespace) -> None:
    repo, issue = split_repo_issue(args.repo, args.issue, args.url)
    emit(issue_view(repo, issue), args.format)


def emit(data: Any, fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(data, indent=2, sort_keys=True))
        return
    if isinstance(data, dict) and "ready_items" in data:
        project = data["project"]
        print(f"Project {project['owner']}/{project['number']} for {project['repo']}")
        print(f"Stage field: {project['stage_field']}")
        print("\nReady/Sprint items")
        for item in data["ready_items"]:
            print(f"- #{item.get('number')} {item.get('title')} [{item.get('stage')}]")
            print(f"  {item.get('url')}")
        print("\nBlocked items")
        for item in data["blocked_items"]:
            print(f"- #{item.get('number')} {item.get('title')} [{item.get('stage')}]")
            print(f"  {item.get('url')}")
        print("\nComments needing attention")
        for comment in data["comments_needing_attention"]:
            first_line = (comment.get("body") or "").strip().splitlines()[0:1]
            preview = first_line[0] if first_line else ""
            print(f"- comment {comment.get('id')} on #{comment.get('issue_number')} by {comment.get('author')}: {preview}")
        return
    print(json.dumps(data, indent=2, sort_keys=True))


def add_format(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--format", choices=["text", "json"], default="text")


def add_common(parser: argparse.ArgumentParser) -> None:
    add_format(parser)
    parser.add_argument("--apply", action="store_true", help="Perform GitHub mutations. Without this flag, print a dry run.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage GitHub Project issue workflows through gh.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="Scan repository-scoped project items.")
    scan_parser.add_argument("--project-number", required=True)
    scan_parser.add_argument("--owner", required=True)
    scan_parser.add_argument("--repo")
    scan_parser.add_argument("--stage-field")
    scan_parser.add_argument("--limit", type=int, default=1000)
    add_common(scan_parser)
    scan_parser.set_defaults(func=scan)

    issue_parser = subparsers.add_parser("issue", help="Fetch one issue with comments and reactions.")
    issue_parser.add_argument("--repo")
    issue_parser.add_argument("--issue")
    issue_parser.add_argument("--url")
    add_format(issue_parser)
    issue_parser.set_defaults(func=fetch_issue)

    mark_parser = subparsers.add_parser("mark-stage", help="Move a project item to a stage.")
    mark_parser.add_argument("--project-number", required=True)
    mark_parser.add_argument("--owner", required=True)
    mark_parser.add_argument("--repo")
    mark_parser.add_argument("--stage-field")
    mark_parser.add_argument("--url", required=True)
    mark_parser.add_argument("--stage", required=True, help="Canonical stage or exact option value.")
    add_common(mark_parser)
    mark_parser.set_defaults(func=mark_stage)

    comment_parser = subparsers.add_parser("comment", help="Add an issue comment.")
    comment_parser.add_argument("--repo")
    comment_parser.add_argument("--issue")
    comment_parser.add_argument("--url")
    comment_parser.add_argument("--body")
    comment_parser.add_argument("--body-file")
    add_common(comment_parser)
    comment_parser.set_defaults(func=add_comment)

    react_parser = subparsers.add_parser("react", help="Add a thumbs-up reaction to an issue comment.")
    react_parser.add_argument("--repo")
    react_parser.add_argument("--comment-id", required=True)
    add_common(react_parser)
    react_parser.set_defaults(func=react)

    edit_parser = subparsers.add_parser("edit-issue", help="Edit an issue title and/or body.")
    edit_parser.add_argument("--repo")
    edit_parser.add_argument("--issue")
    edit_parser.add_argument("--url")
    edit_parser.add_argument("--title")
    edit_parser.add_argument("--body-file")
    add_common(edit_parser)
    edit_parser.set_defaults(func=edit_issue)
    return parser


def main() -> int:
    if not os.environ.get("GH_TOKEN") and not os.environ.get("GITHUB_TOKEN"):
        # gh also supports stored auth; this note is intentionally non-fatal.
        pass
    parser = build_parser()
    args = parser.parse_args()
    if args.command in MUTATING_COMMANDS and not getattr(args, "apply", False):
        print("DRY RUN: pass --apply to mutate GitHub.", file=sys.stderr)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
