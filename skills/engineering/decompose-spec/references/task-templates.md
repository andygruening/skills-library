# Task Templates

Use these templates when generating Codex task prompts, issue bodies, or implementation tickets. Adapt names, file paths, and test commands to the project.

## Interface Composition Task

```markdown
# Compose/Update Domain Interfaces

## Objective
Read the ADR/spec and project structure, then define or update the public interfaces for each affected domain so implementation tasks can proceed independently.

## Inputs
- Source artifact: <path or pasted title>
- Relevant decisions: <brief bullets>
- Existing architecture/code references: <paths or discovery instructions>
- Existing domain registry or domain layout: <path, if present>

## Deliverables
- Domain map with ownership rationale
- Existing-project delta: reused domains, new domains, changed interfaces, unchanged interfaces, affected tests/stubs/fixtures, and composition-root changes
- Interface registry/manifest covering every affected domain
- Public/assembly/testing/internal layout for each affected provider domain
- Contract test plan and shared fixtures/stubs
- Dependency-injection plan for every cross-domain dependency
- Architecture-enforcement rules implemented or a documented blocker if the project lacks enforcement tooling
- Contract-change protocol for consumers that discover insufficient upstream interfaces
- Dependency graph for follow-up domain integration tasks
- Open questions that block interface stability

## Interface Requirements
For each domain, specify:
- Owner and likely code location
- Whether the domain is existing, new, changed, or unchanged for this ADR/spec
- Consumer-facing public surface and import path: APIs, service methods, events, schemas, package exports, components, CLIs, or adapters
- Application-facing assembly import path for provider factories, real adapters, or DI registration helpers
- Testing helpers path: black-box fixtures, stubs, and reusable contract test suites
- Owner-only white-box helper path when needed, under `internal/testing/`
- Stub/fixture naming convention, including an obvious stub suffix such as `.stub.ts`, `Stub.swift`, or `Stub.kt`
- Confirmation that exported testing helpers do not expose internal storage schemas, private adapters, encryption fields, or implementation-only state
- Forbidden private paths such as internal modules, concrete providers, storage schemas, or database tables
- Inputs, outputs, errors, permissions, idempotency, and lifecycle semantics
- Versioning, backward compatibility, migrations, and rollout notes
- Provider tests and consumer fixtures/stubs
- Dependency-injection guidance for consumers
- Allowed consumers and forbidden coupling paths

## Architecture Enforcement
- Infer the language/platform and choose an enforcement mechanism that fits the repository.
- For TypeScript, prefer existing ESLint, dependency-cruiser, package exports, or monorepo boundary tooling.
- For Swift, prefer Swift Package targets and access control boundaries.
- For Kotlin, prefer Gradle modules, `internal` visibility, and dependency graph checks.
- Enforce that domain production code may import other domains only through `public/`.
- Enforce that only composition roots may import `assembly/`.
- Enforce that no non-owning code imports another domain's `internal/`.
- Allow test code to import `testing/` only when the project's test structure can distinguish test files.
- Forbid production code from importing `testing/`, fixture files, or stub-suffixed files.
- Add a convergence check that scans production build output or package artifacts for stub names/imports when the platform makes that practical.
- Document composition roots and verification commands.

## Constraints
- Do not implement domain internals beyond minimal interface scaffolding unless needed to prove the contract.
- When domains already exist, preserve the existing domain map and import paths unless the ADR/spec introduces a genuinely new ownership boundary.
- Prefer updating existing public contracts over creating parallel replacement contracts for the same capability.
- Identify exact deltas for each affected domain: public interface changes, assembly/provider changes, testing helper changes, contract-test changes, internal implementation changes, composition-root wiring, migrations, and enforcement updates.
- Do not let one domain depend on another domain's private code, storage, or schemas.
- Default to `src/domains/<domain>/public`, `src/domains/<domain>/assembly`, `src/domains/<domain>/testing`, and `src/domains/<domain>/internal` unless the repository has an existing stricter convention.
- Keep `testing/` as the only shared testing entrypoint, and keep it black-box. Put owner-only white-box helpers under `internal/testing/`, and never export that path across the domain boundary.
- Prefer explicit sub-entrypoints. Do not export `public/` and `assembly/` together through a mixed root domain barrel unless the existing package convention requires it.
- Consumers must receive cross-domain ports through constructors, factories, handlers, or the project's DI container.
- Consumers must not edit another domain's public, assembly, testing, or contract-test artifacts unless a separate interface-update task grants that ownership.
- Preserve ADR decisions and clearly label unresolved questions.
```

## Domain Integration Task

```markdown
# Integrate <Domain Name>

## Objective
Implement or update <Domain Name> behind its public interface, then route internal callers through that interface or an explicit adapter/facade.

## Inputs
- ADR/spec excerpt: <relevant summary>
- Domain contract: <interface registry excerpt or path>
- Existing domain implementation: <paths or discovery instructions, if present>
- Upstream interfaces allowed for consumption: <list>
- Downstream consumers to support: <list>

## Scope
Allowed:
- <domain-owned modules/files>
- <domain public interface artifacts>
- <domain assembly provider factories or DI registration helpers>
- <domain tests/fixtures>
- <domain DI registration/composition root when needed>
- Existing boundary violations touched by this ADR/spec, only when owned by this domain

Out of scope:
- Other domains' internals
- Other domains' public/assembly/testing contracts unless this task explicitly includes an interface-update handoff for that provider
- Cross-domain database or schema reach-through
- Instantiating another domain's concrete provider directly from this domain
- Importing another domain's assembly entrypoint outside an approved composition root
- Behavior not required by the ADR/spec

## Implementation Requirements
- Provide the public interface exactly as specified or update the interface registry if a contract change is unavoidable.
- In an existing project, implement this task as a delta against the current domain. Update this domain's own public interface artifacts, provider tests, fixtures, stubs, internal tests, assembly providers, and domain-local boundary fixes when affected.
- Internally integrate through the public interface, facade, port, or adapter.
- Consume other domains only through their public interfaces or generated stubs/fixtures.
- Receive consumed domain interfaces through dependency injection or the existing DI container.
- Keep provider factories in this domain's assembly entrypoint when the real implementation must be wired by the application.
- If an upstream interface is insufficient, stop at a contract-change request instead of editing the provider domain. Include provider domain, missing capability, consuming use case, proposed interface shape, fixtures/stubs/contract tests affected, and urgency.
- Preserve backward compatibility or document the migration path.
- Add observability, rollout flags, or migration scripts when the ADR/spec requires them.

## Tests
- Provider contract tests for this domain's public interface
- Consumer-oriented black-box fixtures or stubs
- Stub files use the agreed obvious suffix and live under this domain's testing entrypoint.
- Owner-only white-box helper tests stay under this domain's internal/testing path and are not imported by other domains.
- Unit tests for internal behavior
- Integration tests for allowed upstream/downstream interactions
- Regression tests for compatibility and error behavior

## Acceptance Criteria
- Other domains can use <Domain Name> without private imports or storage access.
- Existing behavior and existing public imports remain compatible unless the ADR/spec explicitly changes them.
- This domain imports only approved public or testing entrypoints from other domains.
- Shared testing imports are black-box and do not rely on another domain's private schema, adapter, encryption, or implementation state.
- No other domain imports this domain's internal/testing helpers.
- Cross-domain collaborators are injected rather than constructed from private implementations.
- Architecture-enforcement checks pass for this domain's import boundaries.
- Any upstream contract gaps are documented as interface-update requests rather than patched across ownership boundaries.
- Test commands pass: <commands>
- Open questions or contract deviations are documented.
```

## Final Convergence Task

```markdown
# Converge Domain Integrations

## Objective
Wire completed domain implementations together and validate the ADR/spec end to end.

## Inputs
- Interface registry/manifest: <path>
- Completed domain tasks: <links or identifiers>
- Rollout/migration notes: <paths>

## Work
- Replace temporary stubs with real providers where appropriate.
- Run cross-domain acceptance tests and migration checks.
- Verify compatibility, observability, permissions, and rollback paths.
- Verify architecture-enforcement commands pass and catch forbidden internal/assembly imports where feasible.
- Verify no testing entrypoint, fixture file, or stub-suffixed file is imported by production code or present in production build artifacts where scanning is practical.
- Remove temporary scaffolding only after equivalent contract coverage exists.

## Acceptance Criteria
- End-to-end flows from the ADR/spec pass.
- No cross-domain private coupling was introduced.
- Consumer domains import other domains through public entrypoints, and composition roots alone import assembly entrypoints.
- Production code is free of `testing/`, fixture, and stub-suffixed imports.
- Interface registry reflects the final implemented state.
- Remaining risks are documented with owners.
```
