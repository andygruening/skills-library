---
name: repo-doctor
description: Prepare a software repository for agent-ready development. Use when Codex needs to audit or configure repository instructions, AGENTS.md/CLAUDE.md guidance, setup and test commands, CI workflows, GitHub PR enforcement, branch protection, contributor templates, dependency hygiene, environment examples, or automation guardrails before agents work in the repo.
---

# Repo Doctor

## Overview

Use this skill to make a repository ready for reliable agent work. Audit first, propose the exact change set in a polished summary, and wait for the user to confirm with `go ahead` before editing files or changing GitHub settings.

## Consent Gate

- Start in audit mode unless the user has already said to apply changes now with an explicit phrase such as `go ahead`, `apply it`, or `make the changes`.
- Do not create, edit, delete, commit, push, or mutate GitHub settings during audit mode.
- End the audit response with: `Reply \`go ahead\` to apply these changes.`
- Treat a later user message containing `go ahead` as approval only for the proposed changes. Re-audit if the repository has materially changed since the proposal.
- Separate local file changes from remote GitHub settings in the proposal. If the user approved only local work, do not mutate GitHub settings.
- Preserve user changes in the worktree. Read and work around dirty files; never revert unrelated edits.

## Session Format

Use a modern, scannable format with emoji session titles. Keep the summary first.

Audit response:

```markdown
## 🩺 Repo Doctor Audit

### ✨ Proposed Change Summary
| Area | Finding | Proposed Change |
| --- | --- | --- |
| Agent instructions | ... | ... |

### 📁 Files To Create Or Update
- `AGENTS.md` - ...
- `.github/workflows/ci.yml` - ...

### 🔐 GitHub Enforcement
- Protect `main` and/or `master` from direct pushes.
- Require pull requests, passing status checks, and up-to-date branches where supported.

### 🧪 Verification Plan
- `...`

### ⚠️ Decisions And Risks
- ...

Reply `go ahead` to apply these changes.
```

Applied response:

```markdown
## ✅ Repo Doctor Applied

### ✨ Change Summary
- ...

### 🧪 Verification
- `...` passed
- `...` could not run: ...

### 🔐 Enforcement
- ...
```

## Audit Workflow

1. Identify the repository root, default branch, remotes, and dirty state.
2. Read existing repository guidance: `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, `README.md`, `CONTRIBUTING.md`, package docs, architecture docs, and task/spec files when present.
3. Detect language, platform, package manager, lockfiles, test framework, formatter, linter, type checker, build tool, container setup, and deployment target.
4. Inspect CI and repository automation: `.github/workflows/`, `.github/dependabot.yml`, PR templates, issue templates, CODEOWNERS, pre-commit hooks, Makefile/taskfile scripts, and release automation.
5. Inspect GitHub enforcement when possible with `gh`: default branch, branch protections or rulesets, required checks, merge settings, and whether direct pushes to `main`/`master` are blocked.
6. Produce the audit response using the session format. Include only changes that are appropriate for the actual repository.
7. After `go ahead`, implement the approved local files, then apply approved GitHub settings if the CLI is authenticated and the scope is clear.
8. Run validation commands and report exact pass/fail results.

## Agent Instructions

Ensure the repository has a clear root-level `AGENTS.md`. Add `CLAUDE.md` only when the user asks for Claude compatibility or the repository already uses it. Prefer one source of truth with short cross-links to avoid drift.

`AGENTS.md` should include:

- Project purpose and high-level architecture.
- Setup commands, required runtimes, package manager, and lockfile rules.
- Daily development commands for install, dev server, tests, lint, format, typecheck, build, and database migrations when relevant.
- Required validation before finalizing agent work.
- Directory map with owned areas, generated files, and files agents should avoid editing.
- Coding standards that are specific to the repo.
- Testing strategy, fixture rules, and where new tests belong.
- Environment variable policy with `.env.example` as the public template and no secrets in git.
- PR workflow: work on branches, keep changes scoped, run checks, link issues, and avoid direct commits to `main`/`master`.
- Safety rules for destructive commands, migrations, data deletion, credentials, production deploys, and remote settings.
- Any project-specific Spellbook, skill, or automation instructions that must be preserved.

When updating existing instructions:

- Preserve accurate project-specific guidance.
- Remove stale commands only after verifying replacement commands.
- Prefer concrete commands over vague advice.
- Keep instructions short enough for agents to load quickly.

## Testing Environment

Make tests discoverable and CI-friendly. Infer the smallest reliable test command from existing project structure before adding new tooling.

Common discovery paths:

- JavaScript/TypeScript: `package.json` scripts, lockfile package manager, Vitest/Jest/Playwright/Cypress, `tsconfig.json`, framework build commands.
- Python: `pyproject.toml`, `pytest.ini`, `tox.ini`, `noxfile.py`, `requirements*.txt`, `uv.lock`, Poetry, Hatch, Ruff, Mypy.
- Go: `go.mod`, `go test ./...`, `golangci-lint`, generated code commands.
- Rust: `Cargo.toml`, `cargo test`, `cargo clippy`, `cargo fmt --check`.
- JVM: Gradle/Maven test, check, formatting, and wrapper scripts.
- Ruby/PHP/.NET/Swift/Kotlin: use the repository's native package and test conventions.

Prefer:

- A single documented local test command.
- Separate lint, format check, typecheck, unit test, integration test, and build commands when the repo already supports them.
- Minimal smoke tests only when a repo has no tests. Do not introduce a large framework migration during repo-doctor work.
- Stable package-manager use from lockfiles: `npm ci`, `pnpm install --frozen-lockfile`, `yarn install --immutable`, `bun install --frozen-lockfile`, `uv sync --frozen`, etc.

## GitHub Workflows

Ensure `.github/workflows/` contains a PR-oriented verification workflow for the detected stack.

Baseline CI expectations:

- Trigger on `pull_request` and on pushes to default branches for post-merge confidence.
- Use pinned official setup actions where practical.
- Install dependencies from lockfiles.
- Run lint, format check, typecheck, tests, and build according to the repository's real commands.
- Use cache keys based on lockfiles.
- Add concurrency to cancel stale runs for the same branch.
- Keep check names stable so branch protection can require them.
- Avoid secrets on untrusted pull request code. Use `pull_request` instead of `pull_request_target` unless there is a specific, reviewed reason.

If the repo already has CI, improve it in place rather than creating a parallel duplicate workflow.

## Pull Request Enforcement

Protect default branches so agent work must go through pull requests.

Required policy:

- Forbid direct commits and direct pushes to `main` and `master` when either branch exists.
- Require pull requests before merging.
- Require the CI status checks that this repo actually runs.
- Require branch to be up to date before merge when the repository uses linear or high-confidence merge queues.
- Dismiss stale reviews or require review from CODEOWNERS when the project has owners.
- Block force pushes and branch deletion.
- Allow administrators to bypass only when the user explicitly wants that policy.

Implementation guidance:

- Use GitHub repository rulesets or branch protection, depending on what the repository already uses.
- Inspect current settings before proposing changes.
- Apply remote changes only after approval and only when `gh` is authenticated to the correct repository.
- If remote enforcement cannot be changed from the environment, write exact manual steps in the applied response.

## Additional Readiness Checks

Evaluate these items and propose them when they fit the repository:

- `CONTRIBUTING.md` with branch, PR, test, review, and release expectations.
- `.github/pull_request_template.md` with summary, tests, risk, and rollout fields.
- `.github/CODEOWNERS` when ownership is obvious or already documented.
- `.github/dependabot.yml` or Renovate config for dependency updates.
- `.env.example` with required variables and safe placeholder values.
- `.editorconfig` for basic whitespace consistency.
- `.gitignore` coverage for local env files, build outputs, dependency directories, coverage, and OS/editor files.
- Secret scanning guidance or workflow if the repository already uses a scanning tool.
- Pre-commit or pre-push hooks only when the repo already uses that ecosystem or the added tool is lightweight and justified.
- Makefile, Taskfile, Justfile, or package scripts that wrap common commands when existing command discovery is fragmented.
- License, security policy, release notes, and changelog only when relevant to the repository's distribution model.

## Implementation Rules

- Match existing tools and conventions. Do not add a new package manager, formatter, or test framework when the repo already has one.
- Keep changes small and reversible. Prefer documentation and CI glue over broad project restructuring.
- Do not fabricate commands. If a command cannot be verified from project files, mark it as a decision or add a conservative placeholder with clear instructions.
- Do not commit, push, or open PRs unless the user asks for that explicitly.
- Do not edit generated lockfiles unless dependency installation or tool setup requires it and the user approved that change.
- Treat production deploy configuration as out of scope unless the user asks for deployment readiness.

## Verification

After applying approved changes:

- Validate `AGENTS.md`/`CLAUDE.md` instructions against real files and commands.
- Run formatting or lint checks for edited workflow/config/docs when available.
- Run the documented test command or the quickest meaningful subset if full tests are expensive.
- Validate GitHub workflow syntax where a local validator exists; otherwise inspect YAML structure and command names.
- Confirm GitHub branch protection/ruleset status with `gh` when remote enforcement was changed.
- Report any skipped verification with the exact reason.
