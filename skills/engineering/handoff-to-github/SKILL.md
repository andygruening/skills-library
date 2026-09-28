---
name: handoff-to-github
description: Create GitHub issue handoffs from Markdown task documents. Use when Codex needs to read tasks from a file, upload the task file and related ADR/spec Markdown file to GitHub Gists, create one GitHub issue per task in the current repository, and add each issue to a GitHub Project selected by user-provided project name, number, or ID.
---

# Handoff to GitHub

## Overview

Turn a Markdown task document into GitHub issues and GitHub Project items. Use the bundled script so Gist creation, issue creation, project lookup, project item creation, and project item edits happen consistently through `gh`.

## Workflow

1. Locate the source files:
   - Task document: the Markdown file containing task bodies.
   - ADR/spec document: the Markdown file that explains the decision or feature context.

2. Resolve the target repository from the current project.
   - Run from the repository root when possible.
   - Let the script detect `OWNER/REPO` using `gh repo view`, falling back to the git `origin` remote.
   - Pass `--repo OWNER/REPO` only when the current checkout is not the intended GitHub repository.

3. Require the user to provide a GitHub Project selector.
   - Accept a project name, project number, project URL, or GraphQL project ID.
   - The script runs `gh project list --owner PROJECT_OWNER` and resolves the selector to the verified `PROJECT_NUMBER`.
   - `PROJECT_OWNER` defaults to the repository owner; pass `--project-owner` only when the project is owned elsewhere.

4. Run a dry run first unless the user explicitly asked to create live GitHub objects now:

```bash
python3 <skill-dir>/scripts/handoff_to_github.py path/to/tasks.md path/to/adr-or-spec.md --project "Project Name" --dry-run
```

5. Run the live handoff after confirming the resolved repository, project owner, project number, and task count:

```bash
python3 <skill-dir>/scripts/handoff_to_github.py path/to/tasks.md path/to/adr-or-spec.md --project "Project Name"
```

## Script Behavior

Before any GitHub mutation, the script parses the task file and verifies requested project fields, their types, and the requested Status option. It then performs this sequence:

1. Upload the task Markdown file to a GitHub Gist.
2. Upload the ADR/spec Markdown file to a separate GitHub Gist.
3. Parse the task document into individual tasks.
4. For each task:
   - Create a GitHub issue in the current repository.
   - Include both Gist URLs in the issue body.
   - Add the issue URL to the verified GitHub Project.
   - Edit project item fields when matching fields are available.

The script records completed Gists, issues, project additions, and field updates in a local state file (by default beside the task file). Re-run the same command after a failure to resume it. Each issue body also contains a stable hidden marker, so a retry can find an already-created issue even if interruption happened before the state file was updated.

The core `gh` calls are inside `scripts/handoff_to_github.py`:

```bash
issue_url=$(gh issue create -R OWNER/REPO -t "Issue title" -b "Issue body")

gh project item-add PROJECT_NUMBER \
  --owner PROJECT_OWNER \
  --url "$issue_url"

gh project item-edit PROJECT_NUMBER \
  --owner PROJECT_OWNER \
  --url "$issue_url" \
  --field "References" \
  --text "Task gist: ...\nADR/spec gist: ..."
```

By default, Gists are secret. Pass `--public-gists` only when the user explicitly wants publicly listed Gists.

## Task Parsing

Prefer task files with one task per Markdown heading, especially under headings such as `Tasks`, `Task Bodies`, or `Implementation Tasks`.

The script also detects:

- Headings beginning with `Task`, `Ticket`, or `Issue`.
- Numbered task headings such as `### 1. Add billing adapter`.
- GitHub checklist items as a fallback when no task headings are found.

If the document uses an unusual structure, pass `--task-heading-regex` to match only the intended task headings.

## Project Fields

Every created issue body includes both Gist links, so the project item content references the uploaded source documents.

If the project has a text field named `References`, the script also writes both links to that field using `gh project item-edit`. Override the field names when needed:

```bash
python3 <skill-dir>/scripts/handoff_to_github.py tasks.md adr.md \
  --project 3 \
  --references-field "Source Links" \
  --status "Ready"
```

Use `--task-gist-field` and `--adr-spec-gist-field` when the project has separate text fields for those URLs.

## Requirements

- `gh` must be installed and authenticated.
- GitHub Project operations require the `project` auth scope. If project commands fail with an auth-scope error, run `gh auth refresh -s project`.
- Creating issues and Gists is a live side effect. Dry-run first when the prompt does not explicitly authorize creation.
