---
name: code-review-loop
description: Iterative code review workflow that repeatedly scans a repository, branch, pull request, or working tree for bugs, regressions, missing tests, design issues, maintainability improvements, and spec mismatches until the review converges. Use when the user asks for a continuous, exhaustive, looped, repeated, or "keep looking until nothing is left" code review, or asks to prioritize all review findings and write them into a Markdown report.
---

# Code Review Loop

## Overview

Run an iterative code review that keeps searching for new substantiated improvements until the review converges. Finish by writing every finding, prioritized by severity and confidence, into a Markdown file.

## Workflow

### 1. Establish Scope

Identify exactly what is being reviewed:

- Prefer the user's explicit scope: PR, branch, commit range, fixed point, directory, file list, or working tree.
- If the user says "current changes" or gives no base, inspect `git status`, branch name, and likely default branches. Ask only when no reasonable review target can be inferred.
- If a fixed point is supplied, review `git diff <fixed-point>...HEAD`. If not, review tracked and untracked working-tree changes with appropriate `git diff`, `git diff --staged`, and file inspection.
- Record the exact scope and commands used in the report.

Gather context before judging:

- Read nearby code, tests, public interfaces, migrations, configuration, docs, and project standards that affect the changed behavior.
- Run fast static checks or targeted tests when they materially increase confidence and are safe in the repo.
- Use existing review skills or repo-specific instructions when they apply, then continue the loop with the findings ledger below.

### 2. Maintain a Findings Ledger

Keep one deduplicated ledger throughout the loop. For each candidate finding, record:

- `id`: stable short ID such as `F-001`.
- `priority`: `P0`, `P1`, `P2`, or `P3`.
- `category`: bug, regression, security, data loss, performance, accessibility, test gap, maintainability, spec mismatch, or scope creep.
- `location`: file and line when possible.
- `evidence`: code, behavior, failing test, spec line, or reasoning that substantiates the issue.
- `impact`: user-visible, operational, developer, or risk impact.
- `recommendation`: concrete fix or improvement.
- `confidence`: high, medium, or low.
- `status`: confirmed, likely, or needs follow-up.

Do not add speculative notes to the final ledger unless they have clear evidence and practical value. Merge duplicates instead of listing the same root cause multiple times.

### 3. Review Loop

Run passes until convergence. Vary each pass so it can discover different classes of issues:

1. Breadth pass: scan every changed file and public interface for obvious correctness, integration, and regression risks.
2. Behavior pass: trace important user flows, API contracts, state transitions, data transformations, error paths, and boundary conditions.
3. Test pass: inspect existing and changed tests, identify missing assertions for risky behavior, and run targeted checks when useful.
4. Design pass: look for duplication, leaky abstractions, unnecessary complexity, brittle coupling, naming problems, and maintainability issues.
5. Standards/spec pass: compare against repo instructions, coding standards, issue text, RFCs, ADRs, or user-provided requirements.
6. Priority pass: re-read the ledger and changed code from highest-risk areas down; validate that every finding is real and that no higher-priority issue is hidden behind lower-priority noise.

After each pass:

- Add only new substantiated findings to the ledger.
- Upgrade, downgrade, merge, or remove ledger entries based on new evidence.
- Note which pass was run and what changed in the ledger.

Convergence is reached only when both are true:

- One complete pass over the scoped code adds no new substantiated findings.
- One additional focused pass over the highest-risk files, edge cases, and existing ledger adds no new substantiated findings.

If tool failures, missing credentials, absent specs, or unavailable dependencies prevent full convergence, continue with the evidence available and clearly mark the limitation in the report.

### 4. Prioritize

Assign priorities consistently:

- `P0`: Breaks core functionality, causes data loss, creates a severe security issue, blocks release, or makes the system unusable.
- `P1`: Likely user-visible bug, serious regression, correctness issue, major performance problem, or important missing test around risky behavior.
- `P2`: Maintainability, reliability, accessibility, edge-case, or moderate test issue that should be addressed but does not block most usage.
- `P3`: Low-risk cleanup, naming, minor duplication, small ergonomics improvement, or optional hardening.

Within the same priority, sort by user impact, blast radius, confidence, and ease of verification.

### 5. Write the Markdown Report

Write the final report to the path requested by the user. If no path is requested, use `code-review-loop-findings.md` in the current working directory.

Use this structure:

```markdown
# Code Review Loop Findings

## Review Scope
- Target: ...
- Base/ref: ...
- Commands/context used: ...
- Convergence: ...
- Limitations: ...

## Priority Summary
| Priority | Count |
| --- | ---: |
| P0 | 0 |
| P1 | 0 |
| P2 | 0 |
| P3 | 0 |

## Findings

### F-001: Short Title
- Priority: P1
- Category: bug
- Location: path/to/file.ext:123
- Confidence: high
- Status: confirmed
- Evidence: ...
- Impact: ...
- Recommendation: ...

## Review Passes
- Pass 1, breadth: ...
- Pass 2, behavior: ...
- Final convergence pass: ...
```

If there are no findings, still write the file with the scope, passes performed, convergence statement, and `No findings.` under `## Findings`.

## Operating Rules

- Prioritize correctness, security, data integrity, release blockers, regressions, and missing high-value tests before style or cleanup.
- Prefer precise file and line references. If exact line numbers are unavailable, cite the smallest useful symbol, hunk, or file section.
- Keep reviewing until convergence, not until an arbitrary pass count.
- Do not fix code unless the user explicitly asks for fixes; this skill's default output is a prioritized review report.
- Be candid about residual risk. "Nothing left to improve" means no further substantiated findings after the convergence passes, not a proof of perfection.
