---
name: sdk-code-review
description: Review SDK code in OMS Wallet SDK repositories. Use when Codex is asked to review an SDK PR, local branch, current project changes, an entire SDK source tree, or SDK parity against a named peer such as typescript-sdk, swift-sdk, or kotlin-sdk; covers project structure, API design, error handling, security, tests, docs, compatibility, changed-file inventory, and parity gaps.
---

# SDK Code Review

## Overview

Review SDK code with the scope implied by the user request. Route explicitly:

- If the request asks to review a current PR, branch, diff, or current changes, perform a PR review.
- If the request asks to review this SDK against a named peer SDK, such as `typescript-sdk`, `swift-sdk`, or `kotlin-sdk`, perform an SDK parity review against that target SDK.
- If neither PR/diff wording nor parity-against-peer wording applies, review the entire source code of the current SDK repository.

Do not run a parity review just because sibling SDKs exist. Only use the parity workflow when the user explicitly asks for consistency, parity, comparison, or review against a named SDK/repository.

## Shared Orientation

1. Locate the repository.
   - Start from the current working directory. Use `git rev-parse --show-toplevel` when available.
   - Read repo instructions first when present: `AGENTS.md`, `CLAUDE.md`, `CONTEXT.md`, `README*`, `docs/adr/*`, package manifests, build manifests, and test configuration.
   - Identify the SDK language and conventions from files such as `Package.swift`, `package.json`, `build.gradle*`, `pom.xml`, `Sources/`, `src/`, `Tests/`, or `test/`.
   - Prefer local project patterns over generic style preferences.

2. Apply the core SDK review lenses.
   - Use `references/review-checklist.md` for detailed OMS SDK review prompts when the review touches source code, architecture, error handling, security, or public API behavior.
   - Check project structure, naming, module boundaries, API consistency, dependency direction, and whether tests live near the behavior they protect.
   - Check error handling paths, typed errors, thrown exceptions, async cancellation, retry behavior, validation, and whether callers can recover.
   - Check security-sensitive areas: authentication, signatures, wallet/key material, secrets, logging, storage, network transport, serialization, dependency updates, and input validation.
   - Check SDK compatibility: source/binary compatibility, public API changes, platform support, semantic version implications, and docs/examples alignment.

3. Broaden issue searches.
   - Whenever you find a concrete or plausible issue, search the repo for similar suspicious patterns that could cause the same issue.
   - Do not edit files during the review unless the user explicitly asks for fixes.
   - Return a `Related Patterns` section using stacked entries instead of a wide table so the review stays readable on narrow screens.
   - For each related pattern, include `File`, `Suspicious Pattern`, `Why It May Be Related`, `Confidence`, and when useful, `Status` (`Confirmed`, `Likely`, or `Needs verification`), `Suggested Mitigation`, and `Test Gap`.
   - Group related patterns by area when there are many, such as `Auth`, `Wallet API`, `Tests`, `Docs`, `Security`, or `SDK Parity`.
   - Keep each related-pattern entry compact: short headings, brief prose, and no horizontally wide tables.
   - When a related pattern touches public API behavior, security-sensitive code, release risk, docs/examples alignment, generated files, or SDK parity, call that out inside the entry rather than creating a separate overflow-prone table.
   - For SDK parity-related patterns, include compact target-vs-peer evidence and explain why the difference matters for consistency.
   - If a related pattern has an obvious small fix, include a short suggested patch snippet or concrete mitigation.
   - If validation was run specifically for a related pattern, include the command and whether it was targeted or full-suite.
   - If no similar suspicious patterns are found, say that and include enough detail about what was searched to make the absence meaningful.

4. Validate.
   - Run the most relevant existing tests or build checks when feasible.
   - Prefer repository commands already documented in manifests, scripts, or CI config.
   - Do not install dependencies or contact external services unless needed and approved.
   - Report any command that could not be run and why.

## PR Review Workflow

Use this workflow for prompts like `review the current PR`, `review this branch`, `review these changes`, or `review the local diff`.

1. Establish PR context.
   - Run `git status --short` and distinguish committed PR changes from uncommitted working tree changes.
   - Run `python3 <skill-dir>/scripts/collect_pr_context.py` from the target repository. Pass `--base <ref>` if the base branch is known.
   - If base detection looks wrong, check likely targets such as `origin/main`, `origin/master`, `main`, or `master` before reviewing.

2. Inspect the PR.
   - Review every changed file from the context report.
   - For each changed source file, inspect the full file and relevant callers, callees, tests, and public API surfaces.
   - Use `git diff <base>...HEAD -- <path>` for PR changes and `git diff -- <path>` for uncommitted changes.
   - For large diffs, still enumerate every changed file; group related generated or fixture files only after confirming they are low risk.

## SDK Parity Review Workflow

Use this workflow only when the user asks to review the current SDK against a peer SDK or asks for SDK parity/consistency, for example `review this SDK against the typescript-sdk`.

1. Locate target and peer repositories.
   - Treat the current repository as the target under review.
   - Find the requested peer repository by exact directory name first, such as `typescript-sdk`, `swift-sdk`, or `kotlin-sdk`.
   - Expect peer SDK repositories to be siblings under the same parent directory. If the requested peer is missing, search one parent level up, then report the unresolved repository instead of guessing.
   - If the user requests comparison against all sibling SDKs, compare against every available sibling and report any missing siblings.

2. Build a compact map of available SDKs.
   - Read top-level docs, package/build manifests, source roots, test roots, examples, and demo apps.
   - Use `rg --files` first to inspect file structure quickly.
   - Identify public entry points, exported APIs, models, services, error types, configuration surfaces, and demo/example flows.

3. Infer each SDK's local conventions before judging mismatches.
   - TypeScript: package exports, async Promise flows, type/interface naming, error propagation, test style.
   - Swift: Swift API Design Guidelines, async/await or completion conventions, `Error`, `Codable`, structs/enums, access control, demo app patterns.
   - Kotlin: coroutines, suspend functions, sealed/data classes, nullability, exception or result conventions, Android/demo patterns.

4. Compare product concepts, not just text.
   - Match equivalent features even when names differ idiomatically.
   - Trace whether a feature is implemented, exported, documented, tested, and exercised by demos/examples.
   - Check both directions: target missing peer functionality, and target-only functionality that may need peer follow-up.

5. Inspect likely parity risks.
   - Public API naming, grouping, and discoverability.
   - Model/type shape, enum cases, defaults, option names, and serialization behavior.
   - Error handling, validation, retry/network behavior, cancellation, logging, and async behavior.
   - Initialization/configuration flows, auth/session handling, environment selection, and dependency injection seams.
   - Missing exports or package registration where implementation exists but is not integrated.
   - Tests absent for target functionality that peers cover, including negative/error cases.
   - Demo app or example flows missing target functionality that peers demonstrate.
   - Documentation drift that would make equivalent SDK usage feel different without a language-specific reason.

6. Judge mismatches carefully.
   - Classify a difference as a finding only when it creates a real parity, reliability, or discoverability problem.
   - Do not flag idiomatic differences by themselves.
   - Before reporting, check whether the target has an equivalent implementation under a different idiomatic name, whether the peer behavior is experimental/deprecated/generated/non-public, or whether platform constraints explain the divergence.

Use these labels when helpful: `Missing in target`, `Not integrated`, `Naming drift`, `Structural drift`, `Behavior drift`, and `Coverage gap`.

## Full Source Review Workflow

Use this workflow when the user invokes the skill without PR/diff wording and without parity-against-peer wording.

1. Build a source inventory.
   - Use `rg --files` to map production source, tests, examples, docs, generated code, package/build config, and demo apps.
   - Identify public API surfaces and critical workflows before inspecting internals.

2. Review high-risk areas first.
   - Public API types and exports.
   - Initialization, configuration, auth/session, networking, serialization, storage, and error handling.
   - Test coverage around public behavior, failure paths, and compatibility guarantees.

3. Sample broadly after high-risk inspection.
   - Inspect representative files across modules, tests, examples, and demos.
   - Call out any important directories or generated files that were intentionally sampled rather than exhaustively reviewed.

## Output

Use a polished, visually structured review layout that is pleasant to scan:

- Use large Markdown section titles for major sections, such as `## 🔎 Findings`, `## ✅ Validation`, and `## ➡️ Next Steps`.
- Add simple section separators, such as `---`, between major sections when the review is longer than a few paragraphs.
- Use tasteful, relevant emojis in section headings and short status callouts. Keep emojis sparse enough that the review still feels professional.
- Prefer compact tables only when they improve readability. Avoid wide tables for related patterns; use stacked entries as described above.
- Keep the layout polished and easy to skim, but do not let presentation weaken review precision, severity ordering, file references, or required content.

Lead with review findings, ordered by severity. Treat concrete bugs, security issues, regressions, missing tests for risky behavior, API compatibility hazards, and material SDK parity gaps as findings.

For each finding, include:

- Severity such as `P0`, `P1`, `P2`, or `P3`
- File and line reference when possible
- Impact
- Specific fix or mitigation

For parity findings, also include peer evidence from the requested SDK repository and explain why the difference matters for SDK consistency.

Separate lower-confidence or style-oriented ideas under `Improvements` so they do not look like confirmed defects.

Always include:

- `Review Scope`: PR review, parity review, or full source review; include base ref or peer SDK when relevant
- `Change Summary For Review`: exact end-user behavior, files changed, internal behavior changed, tests added or updated, commands run, risks, and anything not verified; only include this for PR reviews
- `Changed Files`: every changed PR file with status and one concise summary; only include this for PR reviews
- `Project Structure Notes`: only when structure or module boundaries are relevant
- `Validation`: commands run and results
- `Residual Risk`: important areas not fully checked
- `Next Steps`: a short section that asks the user whether the agent can go ahead and find concrete approaches for fixes. If findings exist, mention that the next pass can identify fix options, affected files, test strategy, and likely risk. If there are no findings, ask whether the user wants a deeper pass, parity check, or targeted area review.

If there are no findings, say that clearly, then still include scope, validation, and residual risks.

## Fixing After Review

If the user asks to fix issues, edit the current target SDK by default. Do not modify sibling SDKs unless explicitly requested. Preserve existing user changes and avoid broad refactors unrelated to the finding.
