---
name: wiki-builder
description: Generate or refresh an evidence-based Markdown wiki for a software repository under ./wiki/. Use when Codex is asked to document an entire codebase, create a project wiki, explain repository architecture and execution flows, map important code by concern, or replace stale project documentation with focused domain pages and Mermaid code maps; supports single projects and monorepos without assuming a language or framework.
---

# Wiki Builder

Build a repository-specific wiki only after completing a broad inventory and tracing the important runtime and development flows. Infer the page set from the code instead of starting from a standard architecture checklist.

## Non-negotiable boundaries

- Create, edit, rename, or delete files only inside the target repository's physical `wiki/` directory. Treat repository-root-relative `./wiki/` as the sole write boundary.
- Do not change source, configuration, manifests, lockfiles, root documentation, generated artifacts, or files in another documentation directory.
- Do not install dependencies or run commands that may generate caches, builds, coverage, snapshots, lockfile changes, or other output outside `wiki/`.
- Record the initial worktree state and preserve unrelated user changes. If repository instructions require an edit outside `wiki/`, report the conflict instead of making that edit.
- Do not follow a `wiki/` symlink that resolves outside the repository. Stop and report the unsafe target.
- Read files outside `wiki/` as evidence; never mutate them.

## Workflow

### 1. Establish the repository and constraints

1. Resolve the repository root from the user's target or current directory.
2. Read applicable agent instructions and the primary project documentation before inspecting implementation details.
3. Capture the initial worktree status so pre-existing changes are distinguishable from wiki work.
4. Inspect an existing `wiki/`, if present. Treat it as potentially stale secondary evidence and verify its claims against current project files.
5. Resolve the physical destination path and confirm every planned output remains beneath `<repo-root>/wiki/`.

### 2. Analyze the whole repository before writing

Complete discovery and the page plan before creating or modifying any file.

Perform two passes:

1. **Coverage pass:** enumerate the complete repository tree and classify every non-excluded area. Identify project or workspace roots, source trees, packages, services, applications, libraries, tests, scripts, configuration, infrastructure, CI, migrations, schemas, public assets, and documentation. Note binary or data-only files without trying to parse them as source.
2. **Understanding pass:** read the human-authored files that establish behavior and trace the important paths through implementation. Inspect manifests and lockfile metadata, package/workspace declarations, entrypoints, composition roots, exported APIs, request or command handlers, domain services, persistence adapters, background processes, build/release/deploy definitions, configuration loading, and representative tests that prove behavior.

Follow references across directories rather than documenting folders in isolation. For each important flow, identify the concrete start point, intermediate symbols, boundary crossings, side effects, and end state. Search for definitions and callers of significant symbols. Use repository-native names in notes.

For large repositories, analyze breadth before depth: cover every first-party package or service, then spend detailed attention in proportion to runtime importance, public surface area, and integration complexity. Never equate reading only top-level manifests or a few representative files with whole-repository analysis.

### 3. Exclude noise deliberately

Ignore generated, vendored, dependency, cache, and build-output trees unless the repository demonstrates that one is operationally significant or contains the only available contract needed to explain a flow. Typical exclusions include:

- `.git/`, dependency stores, vendored third-party source, virtual environments, and package-manager caches
- build, distribution, coverage, temporary, generated-site, and framework-cache directories
- minified bundles, compiled objects, generated API clients, copied assets, large fixtures, snapshots, and machine-generated lockfile internals

Inspect the configuration or generator that produces excluded output when available. If an excluded artifact is relevant, explain why it was consulted and avoid presenting generated internals as first-party design.

### 4. Build an evidence model

Before choosing pages, assemble an in-memory evidence ledger containing:

- repository component or workspace
- responsibility demonstrated by the code
- exact file paths
- exact symbols, scripts, targets, routes, schemas, jobs, or configuration keys
- callers, callees, inputs, outputs, side effects, and external dependencies
- tests or configuration that corroborate the behavior
- uncertainties or conflicting evidence

Base every behavioral statement on this ledger. Do not infer behavior solely from filenames, comments, dependency names, framework conventions, or an old wiki. If evidence is incomplete, state the limitation narrowly or omit the claim. Never invent routes, services, deployment topology, database behavior, or security guarantees.

### 5. Infer focused documentation domains

Derive domains from clusters of related behavior, ownership, data, lifecycle, and execution flow found in the evidence ledger. A domain may be a product capability or a cross-cutting runtime concern, but it must be materially represented in this repository.

Use these sizing rules:

- Give a concern its own page when it has a coherent flow or boundary and enough concrete artifacts to explain usefully.
- Split a page when it mixes independently understandable flows, ownership boundaries, or operational lifecycles.
- Merge candidates that would otherwise repeat the same artifacts or yield only a thin list with no meaningful flow.
- Avoid one page per file, package, class, route, or table.
- Avoid generic catch-all pages such as `architecture-and-everything-else.md`.
- Do not create pages for common topics merely because they usually exist. For example, create an authentication, deployment, database, testing, or background-jobs page only when repository evidence justifies it.

For a monorepo, first map workspaces and their integration points. Choose system-wide pages for genuinely shared flows and package-specific pages for distinct behavior. Make package ownership explicit and avoid duplicating shared material across every package page.

Finalize a page plan with a unique kebab-case filename, scope, evidence set, and cross-links for every domain. Resolve overlaps before writing.

### 6. Write `wiki/index.md`

Create `wiki/index.md` as the concise entry point. Include:

- what the repository demonstrably does
- its major applications, services, packages, or workspaces
- the primary entrypoints and high-level execution paths
- a linked list or table of every generated domain page with a precise one-sentence scope
- a short navigation guide for readers who want to understand, run, test, or operate the project, but only for activities supported by repository evidence

Use relative Markdown links. Keep detailed implementation explanations in domain pages rather than turning the index into a catch-all page.

### 7. Write one page per inferred domain

Use a consistent, evidence-oriented shape while adapting headings to the concern. Each domain page must:

- define its scope, responsibilities, and boundaries
- name the relevant applications or workspaces in a monorepo
- explain important files and directories using exact repository-relative paths
- explain important modules, classes, functions, methods, routes, commands, scripts, schemas, jobs, configuration keys, and entrypoints using exact names
- trace the main execution or data flows in order, including meaningful boundary crossings and side effects
- identify internal and external dependencies and why they participate
- cite tests, fixtures, CI, or configuration that substantiate important behavior when present
- cross-link related domain pages instead of duplicating their contents
- distinguish verified behavior from unresolved or conditional behavior

Prefer short prose, ordered flows, and compact tables such as `Artifact | Role | Evidence`. Put paths and symbols in backticks. Explain why an artifact matters; do not dump directory listings, import inventories, or symbol catalogs.

### 8. End every domain page with a Mermaid code map

The final section of every domain page must be `## Code map`, followed by one fenced `mermaid` block. The Mermaid block must be the final nonblank content in the file.

Build each map from the same evidence as the page:

- Show the domain's meaningful entrypoints, orchestration steps, boundaries, stateful components, and outputs.
- Use directional edges to represent verified invocation, routing, data flow, event flow, or dependency relationships.
- Label nodes with concise human-readable names and concrete paths or symbols when useful.
- Label edges when the relationship is not obvious.
- Group components only when subgraphs materially improve comprehension.
- Keep the graph readable. Prefer the smallest graph that preserves the main flow, usually roughly 4–12 nodes; split the domain rather than drawing an unreadable graph.
- Do not draw every import, helper, class, or function call.
- Use Mermaid-safe node identifiers and quote labels containing punctuation. Avoid unsupported experimental syntax.

### 9. Validate before finishing

Verify all of the following:

- Every planned domain has exactly one focused Markdown page.
- `wiki/index.md` links every domain page, every relative link resolves, and filenames are unique and kebab-case.
- Every documented path exists, and every named symbol, script, route, job, schema, or configuration key is present in repository evidence.
- Behavioral descriptions match the traced control or data flow and do not overstate tests, security, reliability, or deployment guarantees.
- Every domain page ends with a useful Mermaid block and contains no content after it.
- Mermaid nodes and edges describe meaningful verified relationships rather than exhaustive imports.
- Monorepo pages identify ownership and cross-workspace boundaries without duplicating explanations.
- The final changed-file set introduced by this task is contained entirely within the physical `wiki/` directory. Do not count unrelated pre-existing worktree changes as task output.

Fix validation failures only inside `wiki/`. Report the created or updated pages and any important evidence gaps. Do not invoke unrelated project integration, publishing, or deployment workflows.
