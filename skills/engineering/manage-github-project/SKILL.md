---
name: manage-github-project
description: Manage GitHub Projects boards with GitHub CLI for repository-scoped issue workflows. Use when Codex needs to scan GitHub Project items by stage/status, list Ready/Sprint tickets for integration, move project items between In Progress/Blocked/In Review/Finished-like stages, inspect Blocked tickets for non-repeated proposed solutions, process issue comments without thumbs-up reactions, or keep GitHub issues and Project statuses synchronized.
---

# Manage GitHub Project

## Overview

Use this skill to coordinate a GitHub Project board as the issue tracker for the current local git repository. The bundled script uses `gh` to read project items, infer repository identity from the current checkout, normalize stage names, and perform explicit GitHub mutations only when `--apply` is provided.

## Prerequisites

- Run from the local git repository whose issues should be managed, or pass `--repo OWNER/REPO`.
- Require `gh` authentication with repository and project access:

```bash
gh auth refresh -s repo,project
```

- Know the GitHub Project owner and number. Use `--owner "@me"` for the current user.

## Core Workflow

1. Scan the board with the helper script:

```bash
python3 <skill-dir>/scripts/manage_github_project.py scan \
  --project-number PROJECT_NUMBER \
  --owner PROJECT_OWNER
```

2. Review the script output:

- `ready_items`: tickets whose project stage is closest to Ready/Sprint. The script does not start agents. The harness or current Codex session should start integration agents from this queue.
- `blocked_items`: tickets whose project stage is closest to Blocked. Read their issue body and comments; add a new proposed fix only when it adds meaningfully new information.
- `comments_needing_attention`: comments on non-Ready/Sprint items that have no thumbs-up reaction. Decide whether to update the issue description/title, answer with a comment, or take another non-integration action.

3. Apply GitHub mutations only after deciding the action is correct. Every mutating helper command requires `--apply`.

## Stage Handling

Map project stages by closest semantic match, not exact spelling:

- Ready/Sprint: `Ready`, `Sprint`, `Todo`, `To Do`, `Selected`, `Planned`, `Next Up`
- In Progress: `In Progress`, `Doing`, `Active`, `Started`, `Working`
- Blocked: `Blocked`, `Stuck`, `Needs Input`, `Needs Info`, `On Hold`
- In Review: `In Review`, `Review`, `PR Open`, `Pull Request`, `Reviewing`
- Finished: `Done`, `Finished`, `Complete`, `Completed`, `Closed`

Prefer an existing single-select field named like `Status`, `Stage`, `State`, `Workflow`, or `Codex Status`. If no usable stage/status field exists, run `scan --apply` to create a `Codex Status` field with the canonical options. The GitHub CLI can create a new single-select field, but it does not provide a safe simple command to add missing options to an existing field; if an existing field is missing needed options, report that limitation or use `Codex Status`.

## Ready/Sprint Integration Queue

For each `ready_items` entry:

1. Read the issue title, body, and relevant comments from the scan output or with `issue`:

```bash
python3 <skill-dir>/scripts/manage_github_project.py issue \
  --repo OWNER/REPO \
  --issue ISSUE_NUMBER
```

2. When the harness starts an integration agent, immediately mark the item In Progress:

```bash
python3 <skill-dir>/scripts/manage_github_project.py mark-stage \
  --project-number PROJECT_NUMBER \
  --owner PROJECT_OWNER \
  --url ISSUE_URL \
  --stage in-progress \
  --apply
```

3. The integrating agent must create a PR when done and link the project item/ticket in the PR body:

```bash
gh pr create \
  --repo OWNER/REPO \
  --title "Implement #ISSUE_NUMBER: ISSUE_TITLE" \
  --body "Implements https://github.com/OWNER/REPO/issues/ISSUE_NUMBER"
```

4. When the PR is created, mark the item In Review. If the agent is blocked, add a clear issue comment explaining the blocker and proposed next step, then mark the item Blocked.

## Blocked Items

For each `blocked_items` entry, read the issue description and comments. Add a proposed fix or solution only when there is something substantively new to say. Do not rely on hashes or markers for this decision; compare the existing discussion semantically and avoid restating the same recommendation in different words.

Use:

```bash
python3 <skill-dir>/scripts/manage_github_project.py comment \
  --repo OWNER/REPO \
  --issue ISSUE_NUMBER \
  --body-file /path/to/comment.md \
  --apply
```

Then mark the item Blocked if it is not already there.

## Comments Without Thumbs-Up

For all non-Ready/Sprint stages, inspect comments that have no thumbs-up reaction:

```bash
python3 <skill-dir>/scripts/manage_github_project.py scan \
  --project-number PROJECT_NUMBER \
  --owner PROJECT_OWNER \
  --format json
```

Handle each comment according to its content:

- Update the issue description/title if the comment asks for ticket metadata changes.
- Answer questions with an issue comment.
- Ignore requests to integrate, implement, start work, or code changes unless the item is in Ready/Sprint.
- After handling or intentionally ignoring the comment, add a thumbs-up reaction:

```bash
python3 <skill-dir>/scripts/manage_github_project.py react \
  --repo OWNER/REPO \
  --comment-id COMMENT_ID \
  --apply
```

## Script Reference

The helper script is `scripts/manage_github_project.py`.

- `scan`: list repository-scoped project issues grouped into ready, blocked, and comments needing attention.
- `issue`: fetch one issue with comments and comment reactions.
- `mark-stage`: set the project item's status/stage by canonical or exact value.
- `comment`: add an issue comment.
- `react`: add a thumbs-up reaction to an issue comment.
- `edit-issue`: update an issue title and/or body from a file.

Use `--format json` for harnesses and `--apply` for live mutations. Without `--apply`, mutating subcommands print what they would do.
