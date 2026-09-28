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


@dataclass(frozen=True)
class ProjectFieldOption:
    name: str
    option_id: str | None


@dataclass(frozen=True)
class ProjectField:
    name: str
    data_type: str
    options: dict[str, ProjectFieldOption]


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


def run_json(cmd: list[str]) -> object:
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
    if custom_heading_regex and custom_heading_regex.search(heading.title):
        return True
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

    for heading in headings:
        if not is_task_heading(heading, headings, custom_heading_regex):
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
    if not isinstance(data, dict):
        raise HandoffError("Expected an object from gh project list.")
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
) -> dict[str, ProjectField]:
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
    if not isinstance(data, dict):
        raise HandoffError("Expected an object from gh project field-list.")
    fields = data.get("fields", [])
    result: dict[str, ProjectField] = {}
    for field in fields:
        if not isinstance(field, dict):
            continue
        name = str(field.get("name", ""))
        if not name:
            continue
        options = {
            str(option.get("name", "")).casefold(): ProjectFieldOption(
                name=str(option.get("name", "")),
                option_id=str(option["id"]) if option.get("id") else None,
            )
            for option in field.get("options", [])
            if isinstance(option, dict) and option.get("name")
        }
        result[name.casefold()] = ProjectField(
            name=name,
            data_type=str(field.get("dataType", "")).upper(),
            options=options,
        )
    return result


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
    try:
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
    except HandoffError as error:
        detail = str(error).casefold()
        if "already" in detail and ("item" in detail or "project" in detail):
            return
        raise


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


def resolve_text_field_updates(
    field_names: dict[str, ProjectField],
    *,
    references_field: str | None,
    task_gist_field: str | None,
    adr_spec_gist_field: str | None,
    require_project_fields: bool,
    dry_run: bool,
    skip_verify: bool,
) -> list[str]:
    requested_fields = [
        (references_field, False),
        (task_gist_field, True),
        (adr_spec_gist_field, True),
    ]
    resolved: list[str] = []
    for requested_field, explicitly_requested in requested_fields:
        if not requested_field:
            continue
        field = field_names.get(requested_field.casefold())
        if field is None and dry_run and skip_verify:
            resolved.append(requested_field)
            continue
        message: str | None = None
        if field is None:
            message = f"Project field {requested_field!r} was not found; the Gist links remain in the issue body."
        elif field.data_type != "TEXT":
            message = f"Project field {field.name!r} must be a text field, not {field.data_type or 'an unknown type'}."
        if message:
            if require_project_fields or explicitly_requested:
                raise HandoffError(message)
            print(f"Warning: {message}", file=sys.stderr)
            continue
        resolved.append(field.name)
    return resolved


def resolve_status_field(
    field_names: dict[str, ProjectField],
    *,
    status: str | None,
    dry_run: bool,
    skip_verify: bool,
) -> tuple[str, str] | None:
    if not status:
        return None
    field = field_names.get("status")
    if field is None and dry_run and skip_verify:
        return "Status", status
    if field is None:
        raise HandoffError("Project field 'Status' was not found.")
    if field.data_type != "SINGLE_SELECT":
        raise HandoffError(f"Project field {field.name!r} must be a single-select field, not {field.data_type or 'an unknown type'}.")
    option = field.options.get(status.casefold())
    if option is None:
        available = ", ".join(option.name for option in field.options.values()) or "none"
        raise HandoffError(f"Status value {status!r} is not available for {field.name!r}. Available values: {available}")
    return field.name, option.name


def state_signature(
    *,
    repo: str,
    project_owner: str,
    project_number: str,
    task_file: Path,
    adr_spec_file: Path,
    title_prefix: str,
) -> str:
    digest = hashlib.sha256()
    for value in (
        repo,
        project_owner,
        project_number,
        title_prefix,
        task_file.read_text(encoding="utf-8"),
        adr_spec_file.read_text(encoding="utf-8"),
    ):
        digest.update(value.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def default_state_path(tasks_file: Path) -> Path:
    return tasks_file.with_name(f".{tasks_file.stem}.github-handoff-state.json")


def load_state(path: Path, *, signature: str, dry_run: bool) -> dict:
    if dry_run:
        return {"version": 1, "signature": signature, "tasks": {}}
    if not path.exists():
        return {"version": 1, "signature": signature, "tasks": {}}
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HandoffError(f"State file is not valid JSON: {path}") from exc
    if not isinstance(state, dict) or state.get("version") != 1 or not isinstance(state.get("tasks"), dict):
        raise HandoffError(f"State file has an unsupported format: {path}")
    if state.get("signature") != signature:
        raise HandoffError(
            f"State file {path} belongs to a different handoff. Pass --state-file with a new path or remove the stale state file."
        )
    return state


def save_state(path: Path, state: dict, *, dry_run: bool) -> None:
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def task_marker(task: Task, *, signature: str) -> str:
    digest = hashlib.sha256()
    for value in (signature, str(task.ordinal), task.title, task.body):
        digest.update(value.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()[:20]


def find_existing_issue(*, repo: str, marker: str, dry_run: bool) -> str | None:
    if dry_run:
        return None
    data = run_json(
        [
            "gh",
            "issue",
            "list",
            "-R",
            repo,
            "--state",
            "all",
            "--search",
            f"handoff-to-github:{marker} in:body",
            "--json",
            "url,body",
            "--limit",
            "10",
        ]
    )
    if not isinstance(data, list):
        raise HandoffError("Expected a list from gh issue list.")
    matches = [
        str(issue["url"])
        for issue in data
        if isinstance(issue, dict) and f"handoff-to-github:{marker}" in str(issue.get("body", "")) and issue.get("url")
    ]
    if len(matches) > 1:
        raise HandoffError(f"Found multiple existing issues for handoff marker {marker}; resolve the duplicates before resuming.")
    return matches[0] if matches else None


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
    parser.add_argument(
        "--state-file",
        type=Path,
        help="Local progress file for safe resume. Defaults beside the task file.",
    )
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

    text_field_names = resolve_text_field_updates(
        field_names,
        references_field=args.references_field,
        task_gist_field=args.task_gist_field,
        adr_spec_gist_field=args.adr_spec_gist_field,
        require_project_fields=args.require_project_fields,
        dry_run=args.dry_run,
        skip_verify=args.skip_project_verify,
    )
    status_update = resolve_status_field(
        field_names,
        status=args.status,
        dry_run=args.dry_run,
        skip_verify=args.skip_project_verify,
    )
    signature = state_signature(
        repo=repo,
        project_owner=project_owner,
        project_number=project_number,
        task_file=args.tasks_file,
        adr_spec_file=args.adr_spec_file,
        title_prefix=args.title_prefix,
    )
    state_path = args.state_file or default_state_path(args.tasks_file)
    state = load_state(state_path, signature=signature, dry_run=args.dry_run)

    print(f"Repository: {repo}")
    print(f"Project owner: {project_owner}")
    print(f"Project: {project_title} ({project_number})")
    print(f"Tasks: {len(tasks)}")
    if not args.dry_run:
        print(f"State file: {state_path}")

    task_gist_url = state.get("task_gist_url")
    if not task_gist_url:
        task_gist_url = create_gist(
            args.tasks_file,
            description=f"Task handoff source for {repo}",
            public=args.public_gists,
            dry_run=args.dry_run,
        )
        state["task_gist_url"] = task_gist_url
        save_state(state_path, state, dry_run=args.dry_run)

    adr_spec_gist_url = state.get("adr_spec_gist_url")
    if not adr_spec_gist_url:
        adr_spec_gist_url = create_gist(
            args.adr_spec_file,
            description=f"ADR/spec handoff source for {repo}",
            public=args.public_gists,
            dry_run=args.dry_run,
        )
        state["adr_spec_gist_url"] = adr_spec_gist_url
        save_state(state_path, state, dry_run=args.dry_run)

    references_text = f"Task gist: {task_gist_url}\nADR/spec gist: {adr_spec_gist_url}"
    text_field_updates = [(field, references_text) for field in text_field_names if field.casefold() == args.references_field.casefold()]
    text_field_updates.extend((field, task_gist_url) for field in text_field_names if args.task_gist_field and field.casefold() == args.task_gist_field.casefold())
    text_field_updates.extend((field, adr_spec_gist_url) for field in text_field_names if args.adr_spec_gist_field and field.casefold() == args.adr_spec_gist_field.casefold())

    for task in tasks:
        marker = task_marker(task, signature=signature)
        task_state = state["tasks"].setdefault(str(task.ordinal), {"marker": marker, "fields_applied": []})
        if task_state.get("marker") != marker:
            raise HandoffError(f"State for task {task.ordinal} does not match the current task document.")
        issue_body = build_issue_body(
            task,
            task_file=args.tasks_file,
            adr_spec_file=args.adr_spec_file,
            task_gist_url=task_gist_url,
            adr_spec_gist_url=adr_spec_gist_url,
        )
        issue_body = f"{issue_body}\n\n<!-- handoff-to-github:{marker} -->"
        issue_url = task_state.get("issue_url") or find_existing_issue(repo=repo, marker=marker, dry_run=args.dry_run)
        if not issue_url:
            issue_url = create_issue(
                task,
                repo=repo,
                body=issue_body,
                title_prefix=args.title_prefix,
                labels=args.label,
                assignees=args.assignee,
                dry_run=args.dry_run,
            )
        task_state["issue_url"] = issue_url
        save_state(state_path, state, dry_run=args.dry_run)

        if not task_state.get("project_item_added"):
            add_project_item(
                project_number=project_number,
                project_owner=project_owner,
                issue_url=issue_url,
                dry_run=args.dry_run,
            )
            task_state["project_item_added"] = True
            save_state(state_path, state, dry_run=args.dry_run)

        applied_updates = set(task_state.get("fields_applied", []))
        for actual_field, value in text_field_updates:
            update_key = f"text\0{actual_field}\0{value}"
            if update_key in applied_updates:
                continue
            edit_project_item(
                project_number=project_number,
                project_owner=project_owner,
                issue_url=issue_url,
                field=actual_field,
                value=value,
                value_kind="text",
                dry_run=args.dry_run,
            )
            applied_updates.add(update_key)
            task_state["fields_applied"] = sorted(applied_updates)
            save_state(state_path, state, dry_run=args.dry_run)

        if status_update:
            status_key = f"single-select\0{status_update[0]}\0{status_update[1]}"
        else:
            status_key = None
        if status_update and status_key not in applied_updates:
            edit_project_item(
                project_number=project_number,
                project_owner=project_owner,
                issue_url=issue_url,
                field=status_update[0],
                value=status_update[1],
                value_kind="single-select",
                dry_run=args.dry_run,
            )
            applied_updates.add(status_key)
            task_state["fields_applied"] = sorted(applied_updates)
            save_state(state_path, state, dry_run=args.dry_run)

        print(f"Created or resumed: {issue_url}")

    if args.dry_run:
        print("Dry run complete; no GitHub objects were created.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except HandoffError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
