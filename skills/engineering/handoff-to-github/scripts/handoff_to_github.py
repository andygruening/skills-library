#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
CHECKBOX_RE = re.compile(r"^\s*[-*+]\s+\[[ xX]\]\s+(.+?)\s*$", re.MULTILINE)
NUMBERED_RE = re.compile(r"^\s*\d+[\.)]\s+(.+?)\s*$", re.MULTILINE)
TASK_CONTAINER_RE = re.compile(
    r"\b(task bodies|tasks|implementation tasks|task graph|ticket bodies|issues)\b",
    re.IGNORECASE,
)
TASK_CONTAINER_TITLES = {
    "task bodies",
    "tasks",
    "implementation tasks",
    "task graph",
    "ticket bodies",
    "issues",
}
TASK_HEADING_RE = re.compile(r"^\s*(task|ticket|issue)\b|^\s*\d+[\.)]\s+", re.IGNORECASE)


@dataclass
class Task:
    title: str
    body: str
    ordinal: int


@dataclass
class Heading:
    level: int
    title: str
    start: int
    body_start: int
    end: int
    parent_index: int | None


class HandoffError(RuntimeError):
    pass


def redact_command(cmd: list[str]) -> str:
    redacted: list[str] = []
    redact_next = False
    for part in cmd:
        if redact_next:
            redacted.append("<redacted>")
            redact_next = False
            continue
        redacted.append(part)
        if part in {"-b", "--body", "--text"}:
            redact_next = True
    return shlex.join(redacted)


def run(cmd: list[str], *, dry_run: bool = False, capture: bool = True) -> str:
    if dry_run:
        print(f"+ {redact_command(cmd)}", file=sys.stderr)
        return ""

    completed = subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise HandoffError(f"Command failed: {redact_command(cmd)}\n{detail}")
    return (completed.stdout or "").strip()


def run_json(cmd: list[str]) -> dict:
    output = run(cmd)
    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise HandoffError(f"Expected JSON from {redact_command(cmd)}") from exc


def strip_markdown_title(value: str) -> str:
    title = value.strip()
    title = re.sub(r"`([^`]+)`", r"\1", title)
    title = re.sub(r"\*\*([^*]+)\*\*", r"\1", title)
    title = re.sub(r"\*([^*]+)\*", r"\1", title)
    title = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", title)
    title = re.sub(r"^#+\s*", "", title)
    title = re.sub(r"\s+", " ", title)
    return title.strip(" :-")


def issue_title(raw_title: str, max_length: int) -> str:
    title = strip_markdown_title(raw_title)
    title = re.sub(r"^(task|ticket|issue)\s*\d*\s*[:.)-]\s*", "", title, flags=re.IGNORECASE)
    title = re.sub(r"^\d+[\.)]\s*", "", title)
    title = title.strip() or strip_markdown_title(raw_title) or "Untitled task"
    if len(title) > max_length:
        return title[: max_length - 1].rstrip() + "..."
    return title


def build_headings(markdown: str) -> list[Heading]:
    matches = list(HEADING_RE.finditer(markdown))
    headings: list[Heading] = []

    for index, match in enumerate(matches):
        level = len(match.group(1))
        end = len(markdown)
        for next_match in matches[index + 1 :]:
            next_level = len(next_match.group(1))
            if next_level <= level:
                end = next_match.start()
                break

        parent_index = None
        for previous_index in range(len(headings) - 1, -1, -1):
            if headings[previous_index].level < level:
                parent_index = previous_index
                break

        headings.append(
            Heading(
                level=level,
                title=strip_markdown_title(match.group(2)),
                start=match.start(),
                body_start=match.end(),
                end=end,
                parent_index=parent_index,
            )
        )

    return headings


def is_task_heading(
    heading: Heading,
    headings: list[Heading],
    custom_heading_regex: re.Pattern[str] | None,
) -> bool:
    if custom_heading_regex:
        return bool(custom_heading_regex.search(heading.title))
    if heading.title.casefold() in TASK_CONTAINER_TITLES:
        return False
    if TASK_HEADING_RE.search(heading.title):
        return True
    if heading.parent_index is not None:
        parent = headings[heading.parent_index]
        if TASK_CONTAINER_RE.search(parent.title):
            return True
    return False


def parse_heading_tasks(
    markdown: str,
    *,
    custom_heading_regex: re.Pattern[str] | None,
    max_title_length: int,
) -> list[Task]:
    headings = build_headings(markdown)
    tasks: list[Task] = []
    seen_ranges: set[tuple[int, int]] = set()

    candidate_indexes = {
        index
        for index, heading in enumerate(headings)
        if is_task_heading(heading, headings, custom_heading_regex)
    }

    for index, heading in enumerate(headings):
        if index not in candidate_indexes:
            continue

        # A task's subsections belong in that issue body; only the outermost
        # matching heading should create an issue.
        parent_index = heading.parent_index
        while parent_index is not None:
            if parent_index in candidate_indexes:
                break
            parent_index = headings[parent_index].parent_index
        if parent_index is not None:
            continue

        section_range = (heading.start, heading.end)
        if section_range in seen_ranges:
            continue
        seen_ranges.add(section_range)

        body = markdown[heading.body_start : heading.end].strip()
        task_body = f"## {heading.title}\n\n{body}".strip()
        tasks.append(
            Task(
                title=issue_title(heading.title, max_title_length),
                body=task_body,
                ordinal=len(tasks) + 1,
            )
        )

    return tasks


def parse_list_tasks(markdown: str, *, max_title_length: int) -> list[Task]:
    matches = list(CHECKBOX_RE.finditer(markdown)) or list(NUMBERED_RE.finditer(markdown))
    tasks: list[Task] = []
    for match in matches:
        raw_title = match.group(1).strip()
        tasks.append(
            Task(
                title=issue_title(raw_title, max_title_length),
                body=raw_title,
                ordinal=len(tasks) + 1,
            )
        )
    return tasks


def parse_tasks(
    task_file: Path,
    *,
    task_heading_regex: str | None,
    max_title_length: int,
) -> list[Task]:
    markdown = task_file.read_text(encoding="utf-8")
    custom_regex = re.compile(task_heading_regex, re.IGNORECASE) if task_heading_regex else None
    tasks = parse_heading_tasks(
        markdown,
        custom_heading_regex=custom_regex,
        max_title_length=max_title_length,
    )
    if not tasks:
        tasks = parse_list_tasks(markdown, max_title_length=max_title_length)
    if not tasks:
        raise HandoffError(
            f"No tasks found in {task_file}. Use one task per heading or pass --task-heading-regex."
        )
    return tasks


def parse_remote_url(remote_url: str) -> str | None:
    patterns = [
        r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$",
        r"github\.com/([^/]+)/([^/]+?)(?:\.git)?$",
    ]
    for pattern in patterns:
        match = re.search(pattern, remote_url.strip())
        if match:
            return f"{match.group(1)}/{match.group(2)}"
    return None


def detect_repo() -> str:
    try:
        repo = run(["gh", "repo", "view", "--json", "owner,name", "-q", ".owner.login + \"/\" + .name"])
        if repo:
            return repo
    except HandoffError:
        pass

    for remote_name in ("origin", "upstream"):
        try:
            remote_url = run(["git", "remote", "get-url", remote_name])
        except HandoffError:
            continue
        repo = parse_remote_url(remote_url)
        if repo:
            return repo

    raise HandoffError("Could not detect OWNER/REPO. Pass --repo OWNER/REPO.")


def extract_project_number(value: str) -> str | None:
    if value.isdigit():
        return value
    match = re.search(r"/projects/(\d+)(?:\b|$)", value)
    if match:
        return match.group(1)
    return None


def list_projects(owner: str, limit: int) -> list[dict]:
    data = run_json(["gh", "project", "list", "--owner", owner, "--format", "json", "-L", str(limit)])
    return data.get("projects", [])


def resolve_project(
    project_selector: str,
    *,
    project_owner: str,
    limit: int,
    dry_run: bool,
    skip_verify: bool,
) -> tuple[str, str]:
    number_from_selector = extract_project_number(project_selector)
    if dry_run and skip_verify:
        return number_from_selector or project_selector, "dry-run project"

    projects = list_projects(project_owner, limit)
    selector_lower = project_selector.casefold()
    matches: list[dict] = []

    if number_from_selector:
        matches = [project for project in projects if str(project.get("number")) == number_from_selector]
    if not matches:
        matches = [project for project in projects if str(project.get("id", "")) == project_selector]
    if not matches:
        matches = [project for project in projects if str(project.get("title", "")).casefold() == selector_lower]

    if not matches:
        titles = ", ".join(f"{project.get('number')}:{project.get('title')}" for project in projects) or "none"
        raise HandoffError(
            f"Project {project_selector!r} was not found for owner {project_owner}. "
            f"Visible projects: {titles}"
        )
    if len(matches) > 1:
        options = ", ".join(f"{project.get('number')}:{project.get('title')}" for project in matches)
        raise HandoffError(f"Project selector {project_selector!r} matched multiple projects: {options}")

    project = matches[0]
    return str(project["number"]), str(project.get("title") or project["number"])


def load_project_fields(
    project_number: str,
    *,
    project_owner: str,
    limit: int,
    dry_run: bool,
    skip_verify: bool,
) -> dict[str, str]:
    if dry_run and skip_verify:
        return {}

    data = run_json(
        [
            "gh",
            "project",
            "field-list",
            project_number,
            "--owner",
            project_owner,
            "--format",
            "json",
            "-L",
            str(limit),
        ]
    )
    fields = data.get("fields", [])
    return {str(field.get("name", "")).casefold(): str(field.get("name", "")) for field in fields}


def create_gist(path: Path, *, description: str, public: bool, dry_run: bool) -> str:
    cmd = ["gh", "gist", "create", str(path), "--desc", description]
    if public:
        cmd.append("--public")
    if dry_run:
        run(cmd, dry_run=True)
        digest = hashlib.sha1(str(path.resolve()).encode("utf-8")).hexdigest()[:10]
        return f"https://gist.github.com/dry-run/{digest}"
    return run(cmd)


def create_issue(
    task: Task,
    *,
    repo: str,
    body: str,
    title_prefix: str,
    labels: list[str],
    assignees: list[str],
    dry_run: bool,
) -> str:
    title = f"{title_prefix}{task.title}" if title_prefix else task.title
    cmd = ["gh", "issue", "create", "-R", repo, "-t", title, "-b", body]
    for label in labels:
        cmd.extend(["--label", label])
    for assignee in assignees:
        cmd.extend(["--assignee", assignee])

    if dry_run:
        run(cmd, dry_run=True)
        return f"https://github.com/{repo}/issues/dry-run-{task.ordinal}"
    return run(cmd)


def add_project_item(
    *,
    project_number: str,
    project_owner: str,
    issue_url: str,
    dry_run: bool,
) -> None:
    run(
        [
            "gh",
            "project",
            "item-add",
            project_number,
            "--owner",
            project_owner,
            "--url",
            issue_url,
        ],
        dry_run=dry_run,
        capture=False,
    )


def edit_project_item(
    *,
    project_number: str,
    project_owner: str,
    issue_url: str,
    field: str,
    value: str,
    value_kind: str,
    dry_run: bool,
) -> None:
    if value_kind == "text":
        value_flag = "--text"
    elif value_kind == "single-select":
        value_flag = "--value"
    else:
        raise HandoffError(f"Unsupported project field value kind: {value_kind}")

    cmd = [
        "gh",
        "project",
        "item-edit",
        project_number,
        "--owner",
        project_owner,
        "--url",
        issue_url,
        "--field",
        field,
        value_flag,
        value,
    ]

    attempts = 1 if dry_run else 3
    for attempt in range(1, attempts + 1):
        try:
            run(cmd, dry_run=dry_run, capture=False)
            return
        except HandoffError:
            if attempt == attempts:
                raise
            time.sleep(2)


def build_issue_body(
    task: Task,
    *,
    task_file: Path,
    adr_spec_file: Path,
    task_gist_url: str,
    adr_spec_gist_url: str,
) -> str:
    return "\n\n".join(
        [
            task.body.strip(),
            "---",
            "## Handoff References",
            f"- Task document gist: {task_gist_url}",
            f"- ADR/spec gist: {adr_spec_gist_url}",
            f"- Source task file: `{task_file}`",
            f"- Source ADR/spec file: `{adr_spec_file}`",
        ]
    )


def ensure_existing_markdown(path: Path, label: str) -> None:
    if not path.exists():
        raise HandoffError(f"{label} does not exist: {path}")
    if not path.is_file():
        raise HandoffError(f"{label} is not a file: {path}")
    if path.suffix.lower() not in {".md", ".markdown"}:
        raise HandoffError(f"{label} must be a Markdown file: {path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create GitHub issues from a Markdown task file and add them to a GitHub Project."
    )
    parser.add_argument("tasks_file", type=Path, help="Markdown file containing tasks.")
    parser.add_argument("adr_spec_file", type=Path, help="Related ADR or spec Markdown file.")
    parser.add_argument(
        "--project",
        required=True,
        help="GitHub Project title, number, URL, or GraphQL ID. Verified with gh project list.",
    )
    parser.add_argument("--repo", help="GitHub repository as OWNER/REPO. Defaults to current repo.")
    parser.add_argument("--project-owner", help="GitHub Project owner. Defaults to the repository owner.")
    parser.add_argument("--public-gists", action="store_true", help="Create publicly listed Gists.")
    parser.add_argument("--title-prefix", default="", help="Prefix to prepend to each issue title.")
    parser.add_argument("--label", action="append", default=[], help="Label to add to every issue.")
    parser.add_argument("--assignee", action="append", default=[], help="Assignee to add to every issue.")
    parser.add_argument("--status", help='Optional project Status value, such as "Ready".')
    parser.add_argument(
        "--references-field",
        default="References",
        help='Project text field for both Gist URLs. Defaults to "References" when that field exists.',
    )
    parser.add_argument("--task-gist-field", help="Optional project text field for the task Gist URL.")
    parser.add_argument("--adr-spec-gist-field", help="Optional project text field for the ADR/spec Gist URL.")
    parser.add_argument(
        "--require-project-fields",
        action="store_true",
        help="Fail when a requested project field is missing instead of warning and continuing.",
    )
    parser.add_argument(
        "--task-heading-regex",
        help="Case-insensitive regex for headings that should be treated as tasks.",
    )
    parser.add_argument("--max-title-length", type=int, default=180, help="Maximum issue title length.")
    parser.add_argument("--project-list-limit", type=int, default=100, help="Maximum projects to list.")
    parser.add_argument("--field-list-limit", type=int, default=100, help="Maximum project fields to list.")
    parser.add_argument("--dry-run", action="store_true", help="Print gh commands without creating anything.")
    parser.add_argument(
        "--skip-project-verify",
        action="store_true",
        help="Skip gh project list/field-list lookup. Intended only for offline dry runs.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_existing_markdown(args.tasks_file, "Task file")
    ensure_existing_markdown(args.adr_spec_file, "ADR/spec file")

    repo = args.repo or detect_repo()
    repo_owner = repo.split("/", 1)[0]
    project_owner = args.project_owner or repo_owner

    tasks = parse_tasks(
        args.tasks_file,
        task_heading_regex=args.task_heading_regex,
        max_title_length=args.max_title_length,
    )
    project_number, project_title = resolve_project(
        args.project,
        project_owner=project_owner,
        limit=args.project_list_limit,
        dry_run=args.dry_run,
        skip_verify=args.skip_project_verify,
    )

    field_names = load_project_fields(
        project_number,
        project_owner=project_owner,
        limit=args.field_list_limit,
        dry_run=args.dry_run,
        skip_verify=args.skip_project_verify,
    )

    print(f"Repository: {repo}")
    print(f"Project owner: {project_owner}")
    print(f"Project: {project_title} ({project_number})")
    print(f"Tasks: {len(tasks)}")

    task_gist_url = create_gist(
        args.tasks_file,
        description=f"Task handoff source for {repo}",
        public=args.public_gists,
        dry_run=args.dry_run,
    )
    adr_spec_gist_url = create_gist(
        args.adr_spec_file,
        description=f"ADR/spec handoff source for {repo}",
        public=args.public_gists,
        dry_run=args.dry_run,
    )

    references_text = f"Task gist: {task_gist_url}\nADR/spec gist: {adr_spec_gist_url}"
    text_field_updates = [
        (args.references_field, references_text, False),
        (args.task_gist_field, task_gist_url, True),
        (args.adr_spec_gist_field, adr_spec_gist_url, True),
    ]
    resolved_text_field_updates: list[tuple[str, str]] = []
    for requested_field, value, explicitly_requested in text_field_updates:
        if not requested_field:
            continue
        actual_field = field_names.get(requested_field.casefold())
        if not actual_field and args.dry_run and args.skip_project_verify:
            actual_field = requested_field
        if not actual_field:
            message = (
                f"Project field {requested_field!r} was not found; "
                "the Gist links remain in the issue body."
            )
            if args.require_project_fields or explicitly_requested:
                raise HandoffError(message)
            print(f"Warning: {message}", file=sys.stderr)
            continue
        resolved_text_field_updates.append((actual_field, value))

    status_field = None
    if args.status:
        status_field = field_names.get("status")
        if not status_field and args.dry_run and args.skip_project_verify:
            status_field = "Status"
        if not status_field:
            raise HandoffError("Project field 'Status' was not found.")

    for task in tasks:
        issue_body = build_issue_body(
            task,
            task_file=args.tasks_file,
            adr_spec_file=args.adr_spec_file,
            task_gist_url=task_gist_url,
            adr_spec_gist_url=adr_spec_gist_url,
        )
        issue_url = create_issue(
            task,
            repo=repo,
            body=issue_body,
            title_prefix=args.title_prefix,
            labels=args.label,
            assignees=args.assignee,
            dry_run=args.dry_run,
        )
        add_project_item(
            project_number=project_number,
            project_owner=project_owner,
            issue_url=issue_url,
            dry_run=args.dry_run,
        )

        for actual_field, value in resolved_text_field_updates:
            edit_project_item(
                project_number=project_number,
                project_owner=project_owner,
                issue_url=issue_url,
                field=actual_field,
                value=value,
                value_kind="text",
                dry_run=args.dry_run,
            )

        if args.status and status_field:
            edit_project_item(
                project_number=project_number,
                project_owner=project_owner,
                issue_url=issue_url,
                field=status_field,
                value=args.status,
                value_kind="single-select",
                dry_run=args.dry_run,
            )

        print(f"Created: {issue_url}")

    if args.dry_run:
        print("Dry run complete; no GitHub objects were created.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except HandoffError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
