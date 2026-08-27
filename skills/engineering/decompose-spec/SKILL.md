---
name: decompose-spec
description: Split a software product spec, technical design, RFC, or ADR into domain-owned implementation tasks written to TASKS.md, prioritizing SPEC.md as the source artifact when present, with explicit public interfaces, dependency order, contract tests, and integration prompts for new or existing projects. Use when Codex needs to decompose architecture work across bounded contexts/modules/services, create parallel task prompts, design or update domain contracts, reuse an existing domain structure for a new ADR/spec, prevent cross-domain coupling, or coordinate one interface-composition task followed by per-domain integration tasks.
---

# Decompose Spec

## Overview

Turn a product spec, technical design, RFC, or ADR into a domain task plan. First define or update each domain's public interface, then create separate integration tasks so each domain can implement internally while other domains consume only that interface. Use the skill both to design domains for a new project and to plan changes against an existing domain structure.

## File Conventions

- Treat an explicitly supplied source path, linked artifact, or pasted source content as authoritative. Otherwise, look first for a project file named exactly `SPEC.md` before considering other spec, ADR, RFC, README, issue, or design files.
- When multiple files named exactly `SPEC.md` exist, prefer the one nearest the target project root or the current working directory, and state which file was used.
- When writing the generated Markdown plan or manifest to disk, write it to a file named exactly `TASKS.md`. Do not use alternate filenames such as `tasks.md`, `TASK_PLAN.md`, or `domain-tasks.md`.
- If `SPEC.md` is the selected source artifact, write `TASKS.md` in the same directory unless the user specifies another target directory.
- If `TASKS.md` already exists, update that file instead of creating a second task-plan file. Preserve unrelated user-authored content when practical; if the existing file cannot be updated safely, report the conflict instead of writing an alternate filename.

## Core Rules

- Treat a domain as an owned behavioral boundary, not just a folder. Prefer existing product language, services, modules, data ownership, and team boundaries over invented categories.
- Reuse existing domains when a project already has domain boundaries. Treat the current domain map, import paths, public contracts, tests, stubs, fixtures, and enforcement rules as the starting point.
- Create a new domain only when the ADR/spec introduces a new ownership boundary. Do not redesign the domain map just because a new feature touches several existing domains.
- Define public interfaces before implementation tasks. Interfaces may be API routes, service methods, event contracts, database access ports, schemas, package exports, UI component contracts, CLI commands, or typed adapters.
- Require each domain to internally integrate its own public interface. The domain should route internal callers through the same facade/port/adapter, or provide an explicit reason when that is impractical.
- Let other domains consume only public interfaces. Forbid direct imports, schema reach-through, shared mutable state, or database table access across domain boundaries unless the ADR explicitly requires it.
- Make contracts testable. Every interface needs provider tests, consumer-facing fixtures or stubs, error semantics, compatibility expectations, and an owner.
- Prefer dependency injection for cross-domain use. Consumers should receive another domain's port through constructors, factories, handlers, or the project's DI container; they should not instantiate another domain's concrete provider.
- Distinguish consumer-facing ports from application-facing provider factories. Consumer domains import only another domain's `public/` contracts; composition roots may import `assembly/`; test code may import `testing/`; no code outside the owning domain may import `internal/`.
- Enforce boundaries with project tooling. The interface-composition task should implement lint/build/package/module rules that prevent invalid cross-domain imports whenever the repository has a suitable enforcement mechanism.
- Preserve interface ownership. A domain integration task may change its own public contract, but it must not edit another domain's `public/`, `assembly/`, `testing/`, or contract tests unless the task explicitly owns an interface-update handoff for that provider domain.
- Preserve uncertainty. If the ADR does not decide a boundary or contract, name the open question and isolate work behind a provisional interface.

## Default Interface Layout

Prefer this provider-owned layout unless the repository already has a stricter convention:

```text
src/domains/<domain>/
  index.ts
  public/
    index.ts
    <capability>.port.ts
  assembly/
    index.ts
    <capability>.provider.ts
  testing/
    <capability>.fixtures.ts
    <capability>.stub.ts
    describe-<capability>-contract.ts
  internal/
    testing/
      <implementation>.test-helper.ts
    <implementation>.ts
```

- Put consumer-facing contracts in `public/`; this is the only production entrypoint other domains may import.
- Put application-facing provider factories, real adapters, and DI registration helpers in `assembly/`; only composition roots may import this entrypoint.
- Put reusable black-box test fixtures, stubs, and contract suites in `testing/`; allow test code to import them, but keep production code on the public entrypoint. Name stubs with an obvious suffix such as `<capability>.stub.ts`, `<capability>Stub.swift`, or `<Capability>Stub.kt` so enforcement can catch them by path and filename. Do not export helpers that expose internal storage schemas, private adapters, encryption fields, or implementation-only state.
- Put concrete providers, private implementation details, and owner-only white-box test helpers in `internal/`; forbid other domains from importing this directory, including `internal/testing/`.
- Have consumers depend on provider-owned ports by injection, e.g. `createAuthService({ secretStore }: { secretStore: SecretStorePort })`.
- Prefer explicit sub-entrypoints such as `domains/storage/public` and `domains/storage/assembly`. Do not use a root `domains/storage` barrel that mixes consumer contracts with provider factories unless an existing package convention requires it.
- Record each public import path, assembly import path, testing import path, allowed importer class, and forbidden private path in the interface registry.
- Keep `testing/` as the only shared testing entrypoint. Use `internal/testing/` only for owner-domain white-box helpers, and never export it across the domain boundary.

## New Project vs Existing Project Mode

Use new-project mode when the repository has no clear domain boundaries yet. In this mode, propose the domain map, default layout, interface registry, enforcement rules, and first integration tasks from the ADR/spec and local project context.

Use existing-project mode when domains, ports, package boundaries, modules, services, or an interface registry already exist. In this mode:

- Preserve the existing domain map unless the ADR/spec introduces a genuinely new ownership boundary.
- Inspect existing `public/`, `assembly/`, `testing/`, `internal/`, composition roots, task conventions, architecture docs, and enforcement rules.
- Produce a delta plan against the current architecture: interfaces to update, tests to add or adjust, stubs/fixtures to update, implementation work per domain, composition-root wiring, migrations, and convergence checks.
- Prefer updating existing public contracts over creating parallel replacement contracts for the same capability.
- Assign each domain task responsibility for its own public interface artifacts, assembly providers, testing helpers, contract tests, internal implementation, and domain-local boundary fixes.
- Create separate interface-update tasks when a consumer needs a provider-domain contract change that the consumer task does not own.
- Treat unrelated preexisting boundary violations as out of scope unless they block the ADR/spec; when touched by the change, assign the fix to the owning domain task instead of doing a broad migration.
- Mark domains as `existing`, `new`, `changed`, or `unchanged` in the output when that helps the user review the plan.

## Workflow

1. Read the source artifact and local project context.
   - If the user did not provide a source artifact, prioritize a file named exactly `SPEC.md` and use it as the source before other candidate spec or architecture files.
   - Identify the decision, goals, non-goals, constraints, rollout assumptions, and affected user or system flows.
   - Inspect existing architecture docs, interface registries, code boundaries, and composition roots when a repo is available.
   - Use the project's existing task, issue, or thread conventions when present.

2. Discover candidate domains.
   - For existing projects, start from the current domain structure and classify affected domains as existing/new/changed/unchanged.
   - For new projects, group by owned data, business behavior, vocabulary, runtime lifecycle, and change reasons.
   - Keep domains coarse enough to own meaningful behavior; avoid creating a domain for every class, endpoint, or table.
   - Note current owners or likely code locations when discoverable.

3. Compose the domain-interface update task.
   - Make this the first task unless interfaces already exist and are current.
   - Ask that task to produce or update an interface registry/manifest.
   - In existing projects, require this task to diff the ADR/spec against existing interfaces and identify exactly which public, assembly, testing, and enforcement artifacts need changes.
   - Require each domain interface to specify owner, public surface, public import path, assembly import path when provider factories exist, testing helpers path, forbidden private paths, schemas/types, commands/queries/events, permissions, errors, versioning, test fixtures, compatibility rules, and consumers.
   - Require dependency-injection wiring guidance for every cross-domain dependency.
   - Require an architecture-enforcement deliverable. Infer the language/framework and create or update suitable lint/build/package/module rules when possible; if enforcement cannot be implemented, document the blocker and the best available review check.
   - Require cross-domain dependency decisions to be documented in the registry before integration begins.

4. Create one integration task per domain.
   - Give each task the relevant ADR excerpts, the assigned domain contract, upstream interfaces it may consume, and downstream consumers it must support.
   - Scope the task to that domain's internals plus its public interface artifacts and tests.
   - In existing projects, scope the task as a delta from the current domain implementation and require it to update that domain's own interface artifacts, provider tests, fixtures, stubs, internal tests, and assembly providers when affected.
   - Require internal integration through the public interface or a named adapter/facade.
   - Require cross-domain dependencies to be accepted through dependency injection or the project's existing DI container.
   - Require contract tests proving the domain provides its interface and consumer tests or fixtures proving other domains can use it without internal knowledge.
   - Require a contract-change request when the domain needs behavior missing from another domain's public interface. The request should name the provider domain, missing capability, consuming use case, proposed interface shape, fixture/test impact, and urgency.

5. Build the dependency plan.
   - Place the interface-composition task first.
   - Allow domain integration tasks to run in parallel after contract artifacts exist.
   - Mark tasks that can start with stubs/mocks and tasks that need a provider contract finalized first.
   - Add a final convergence task when end-to-end wiring, migrations, rollout flags, or cross-domain acceptance tests are needed.
   - Add separate interface-update tasks when integration work reveals a cross-domain contract gap. Assign them to the provider domain owner or the interface-composition owner, then unblock consumers through the updated registry.

6. Deliver or create tasks.
   - Unless the user requests chat-only output or task/thread creation, write the single Markdown plan document to `TASKS.md` exactly.
   - If the user asks for task prompts only, output copy-ready task bodies.
   - If the user explicitly asks to create Codex tasks/threads and the environment exposes thread tools, create the interface-composition task first. Wait for or inspect its interface registry before creating domain integration tasks unless the user explicitly wants draft tasks based only on the original ADR/spec.
   - After the registry exists, create one task per domain integration and optionally one final convergence task. Follow the app's thread-tool instructions.
   - If no task system is available, write issue-ready Markdown to `TASKS.md` when a writable project directory is available; otherwise provide it in chat and state that `TASKS.md` could not be written.

## Required Output Shape

Produce these sections unless the user requests a different format. When writing to disk, these sections belong in `TASKS.md`:

- `Domain Map`: table with domain, ownership rationale, likely code locations, owned data/behavior, and external dependencies.
- `Existing Project Delta`: when a project already has domains, summarize reused domains, new domains, changed interfaces, unchanged interfaces, touched tests/stubs/fixtures, and composition-root changes.
- `Interface Registry`: table with domain, public interface artifact/import path, assembly import path, testing helpers path, forbidden private paths, contract summary, consumers, allowed importers, DI guidance, compatibility/versioning, and required tests.
- `Architecture Enforcement`: language/platform, chosen enforcement mechanism, files to create/update, allowed import rules, forbidden import rules, composition roots, and verification commands.
- `Task Graph`: ordered task list with dependencies and parallelization notes.
- `Task Bodies`: one body for `Compose/Update Domain Interfaces`, one per domain integration, and an optional final convergence task.
- `Contract Change Protocol`: what a domain agent should do when another domain's interface is insufficient.
- `Open Questions`: only questions that materially affect interface shape, ownership, rollout, or data compatibility.

For reusable task-body templates, read `references/task-templates.md`.

## Task Quality Bar

Every generated task must include:

- Objective and non-goals
- Inputs from the ADR/spec
- Owned files/modules or discovery instructions
- Existing-project delta when applicable
- Public interface changes allowed by the task
- Internal integration requirement
- Other domain interfaces it may consume
- Dependency-injection wiring for consumed domain interfaces
- Architecture-enforcement changes or checks that protect the domain boundary
- Stub/fixture naming and production-exclusion checks
- Contract-change protocol for insufficient upstream interfaces
- Contract tests, unit/integration tests, and acceptance criteria
- Explicit coupling constraints
- Migration, rollout, observability, and backward-compatibility notes when relevant

## Review Checklist

Before finishing, verify:

- No domain task depends on another domain's private implementation.
- Every cross-domain dependency has a named public interface.
- Every consumed cross-domain interface is injected or provided through an existing DI mechanism.
- Consumer domains import other domains only through approved `public/` entrypoints.
- Composition roots are the only non-owning production code allowed to import `assembly/`.
- Boundary enforcement is implemented in available project tooling, or the blocker is explicit.
- Production code and production bundles cannot import `testing/`, fixture files, or stub-suffixed files.
- No non-owning domain imports `internal/` or `internal/testing/`.
- Integration tasks do not mutate other domains' contracts without a separate interface-update handoff.
- Existing projects reuse current domain ownership unless a new boundary is justified by the ADR/spec.
- Existing-project tasks are deltas against current public interfaces, tests, fixtures, stubs, assembly, internals, and enforcement rules.
- Every provider interface has tests or fixtures that consumers can use.
- The interface-composition task creates enough artifacts for parallel work.
- `SPEC.md` was prioritized as the source artifact when the user did not explicitly supply a different source.
- The generated file is named exactly `TASKS.md` whenever output is written to disk.
- Integration tasks are scoped so independent agents can execute them without hidden context.
- Open questions are separated from decided contract details.
