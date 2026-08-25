# Decompose Spec

`decompose-spec` is a Codex skill for turning a product spec, technical design, RFC, or ADR into domain-owned implementation tasks.

The operational agent instructions live in `SKILL.md`. This README is human-facing: it explains the concepts, rules, and design decisions so the skill is easier to share and discuss.

The skill is built around one idea:

> A domain should promise a public capability that other domains can use, while hiding every detail of how that capability works internally.

This makes it easier to split a large software change across multiple agents or developers. One agent can define or update the domain interfaces. Then separate agents can implement each domain without reaching into each other's private code.

## What This Skill Produces

Given a spec or ADR, the skill produces:

- A domain map
- A public interface registry
- A dependency graph
- One interface-composition task
- One integration task per domain
- Optional final convergence work
- Architecture enforcement rules where the project supports them

The goal is not just to split work into smaller tickets. The goal is to split work along ownership boundaries so parallel agents can work safely.

## New Projects And Existing Projects

The skill works in two modes.

### New Project Mode

Use this mode when the project does not have clear domain boundaries yet.

In this mode, the skill designs the first version of the domain structure:

- Which domains exist
- What each domain owns
- What public interfaces each domain exposes
- Which testing helpers prove those interfaces
- Where dependency injection and composition happen
- Which architecture rules should prevent boundary leaks

This is the mode for turning an ADR or product spec into a first clean domain map.

### Existing Project Mode

Use this mode when the project already has the domain structure.

In this mode, the skill should not redesign the architecture casually. It should inspect the existing domains and produce a delta plan for the new ADR/spec.

It should look for:

- Existing `public/` contracts
- Existing `assembly/` providers
- Existing `testing/` fixtures, stubs, and contract tests
- Existing `internal/` implementations
- Existing UI public components and views
- Existing composition roots
- Existing boundary enforcement rules
- Existing interface registry or architecture docs

Then it should answer:

- Which existing interfaces need to change?
- Which domains need implementation work?
- Which fixtures, stubs, or contract tests need updates?
- Which UI elements or views need updates?
- Which composition-root wiring needs updates?
- Which boundaries need enforcement changes?
- Is a new domain actually justified?

The default answer should be "reuse the existing domains." A new domain should appear only when the ADR/spec introduces a genuinely new ownership boundary.

Example:

```text
Existing domains:
  auth
  storage
  ui

New ADR:
  Add Google sign-in.
```

The skill should usually produce updates to existing domains:

```text
auth:
  update public auth interface
  implement Google sign-in internally
  update auth contract tests and stubs

storage:
  update only if token storage needs a new storage capability

ui:
  add or update shared sign-in elements/views

composition root:
  wire UI events to auth behavior
  inject real auth/storage providers
```

It should not create a separate `google-sign-in` domain unless the spec gives that capability its own independent ownership, lifecycle, data model, or reason to change.

## The Core Model

### Domains

A domain is an owned behavioral boundary.

Good domains usually own at least one of these:

- A business capability
- A runtime lifecycle
- A data model
- A set of permissions or policies
- A vocabulary from the product spec
- A reason to change independently from the rest of the system

Examples:

- `auth`
- `storage`
- `billing`
- `notifications`
- `search`
- `ui`

A domain is not just a folder. It is a promise that some part of the system owns a capability and exposes it deliberately.

### Public Interfaces

Each core domain exposes a public interface that other domains are allowed to use.

Depending on the platform, an interface may be:

- A TypeScript port
- A Swift protocol
- A Kotlin interface
- An API route
- An event contract
- A CLI command
- A package export
- A schema
- A typed adapter

The interface must be stable enough that another domain agent can build against it without knowing the implementation.

Example:

```ts
export interface SecretStorePort {
  storeSecret(input: StoreSecretInput): Promise<StoredSecret>;
  readSecret(id: SecretId): Promise<StoredSecret | null>;
}
```

The consumer should know what behavior is promised, what errors can happen, what data is required, and what compatibility expectations exist. The consumer should not know where the secret is stored, how it is encrypted, what table exists, or which SDK is used.

## Core Domain Layout

For core domains, prefer this shape unless the project already has a stricter convention:

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

### `public/`

`public/` is the consumer-facing production interface.

Other domains may import this.

Example:

```ts
import type { SecretStorePort } from "@/domains/storage/public";
```

### `assembly/`

`assembly/` contains real provider factories, adapters, and dependency-injection registration helpers.

Only composition roots may import this.

Example:

```ts
import { createSecretStore } from "@/domains/storage/assembly";
```

A consumer domain should not import another domain's assembly entrypoint. It should receive the provider through dependency injection.

### `testing/`

`testing/` contains shared black-box testing helpers for the public interface:

- Fixtures
- Stubs
- Contract test suites

Other domains may use these from tests, but production code must not import them.

Example:

```ts
import { createSecretStoreStub } from "@/domains/storage/testing/secret-store.stub";
import { validStoredSecret } from "@/domains/storage/testing/secret-store.fixtures";
```

These helpers must not expose private storage schemas, encryption internals, private adapters, or implementation-only state.

### `internal/`

`internal/` contains the real implementation and owner-only internals.

No other domain may import this.

`internal/testing/` is allowed only for white-box tests owned by the same domain.

## Interface Ownership

Each domain owns its own public contract.

An auth-domain agent may consume a storage interface, but it may not invent or edit storage internals. If auth needs something storage does not expose yet, auth should create a contract-change request for the storage owner.

The request should include:

- Provider domain
- Missing capability
- Consuming use case
- Proposed interface shape
- Fixture or stub impact
- Contract test impact
- Urgency

Until the provider is ready, the consumer may use a provider-owned or interface-composition-owned stub. The stub must be clearly marked and excluded from production wiring.

## Dependency Injection

Cross-domain use should happen through dependency injection.

Good:

```ts
export function createAuthService(deps: {
  secretStore: SecretStorePort;
}) {
  return {
    async storeAuthSecret(secret: AuthSecret) {
      return deps.secretStore.storeSecret({ value: secret.value });
    },
  };
}
```

Bad:

```ts
import { createSecretStore } from "@/domains/storage/internal/encrypted-secret-store";
```

The auth domain should not construct storage's concrete implementation. The composition root should wire the real storage provider into auth.

## Frontend And UI Domains

Frontend/UI should be treated differently from core business domains.

The UI domain is a presentation capability domain. It owns reusable presentation building blocks, not business workflows.

It may expose:

- Elements such as buttons, labels, inputs, selects, toggles, and icons
- Shared views such as cancel dialogs, info views, empty states, and reusable form shells
- Theme tokens, layout primitives, and interaction conventions

It should not import core domains like `auth`, `storage`, or `billing`.

Prefer this shape:

```text
src/domains/ui/
  public/
    elements/
      button.tsx
      input.tsx
      label.tsx
    views/
      cancel-popup.tsx
      info-view.tsx
      sign-in-form.tsx
    index.ts
  internal/
    theme/
    layout/
    tokens/
```

Each element or view should live in its own file. The public UI interface is made of props, callbacks, slots, render contracts, accessibility behavior, and styling conventions.

Example:

```ts
export interface SignInFormProps {
  errorMessage?: string;
  pending?: boolean;
  onSubmit(credentials: { email: string; password: string }): void;
  onCancel(): void;
}
```

The UI component exposes events. It does not execute auth logic.

## Composition Root

The composition root connects everything.

It is the only layer that may import both:

- UI public components and views
- Core domain public interfaces and assembly providers

It owns:

- Application startup
- Windows
- Screens
- Routes
- State containers
- Navigation
- Dependency injection
- Real provider construction
- Wiring UI events to domain behavior

Example:

```text
src/app/
  composition-root.ts
  windows/
    sign-in.window.tsx
  state/
    sign-in.state.ts
```

Example:

```tsx
import { SignInForm } from "@/domains/ui/public/views/sign-in-form";
import type { AuthPort } from "@/domains/auth/public/auth.port";

export function createSignInWindow(deps: { auth: AuthPort }) {
  return (
    <SignInForm
      pending={false}
      onSubmit={(credentials) => deps.auth.signIn(credentials)}
      onCancel={() => deps.auth.cancelSignIn()}
    />
  );
}
```

The sign-in form does not know auth exists. The composition root does.

## Dependency Direction

The intended dependency direction is:

```text
composition root -> ui public
composition root -> core domain public
composition root -> core domain assembly

core domain -> other core domain public interfaces only

ui domain -> no core domain imports
```

Forbidden:

```text
core domain -> ui domain
ui domain -> auth/storage/billing domain
core domain -> another domain's internal/
core domain -> another domain's assembly/
production code -> testing/ or *.stub.*
```

Allowed:

```text
composition root -> ui/public
composition root -> core/public
composition root -> core/assembly
core domain -> another core domain public port, injected
test code -> another domain's testing helpers
owning domain -> its own internal/
```

## Testing And Verification

Core domains should have reliable tests for their public interfaces.

The provider domain should own:

- Provider contract tests
- Black-box fixtures
- Stubs
- Error behavior examples
- Compatibility expectations

Consumer domains may use another domain's fixtures and stubs to validate their own behavior against that public interface.

UI is different. UI domains are not expected to have the same contract-test shape as core business domains. UI verification should be adapted to the project:

- Build checks
- Type checks
- Render checks
- Accessibility checks
- Screenshot or visual checks
- Story or preview compilation

If the UI cannot be verified without a runnable build, the task should say that explicitly and include the build or preview command as the acceptance gate.

## How Tasks Should Be Split

For a new project, the skill usually creates work in this order:

1. Compose or update the domain interfaces.
2. Add architecture enforcement.
3. Create one integration task per core domain.
4. Create one frontend/UI task when UI primitives or shared views are affected.
5. Create one composition-root task when screens, windows, routes, state, or real wiring are affected.
6. Create a final convergence task when end-to-end behavior must be verified.

This prevents agents from building around imaginary contracts or coupling to private code.

For an existing project, the task graph should be a delta:

1. Inspect the current domain map, interface registry, tests, fixtures, stubs, assembly providers, UI public exports, and composition roots.
2. Compose or update only the interfaces affected by the ADR/spec.
3. Assign each affected domain its own update task.
4. Keep unchanged domains out of the work except as consumed public interfaces.
5. Add separate provider-owned interface-update tasks when a consumer needs another domain to expose a missing capability.
6. Add a composition-root task when real wiring, screens, windows, routes, states, or dependency injection must change.
7. Add convergence only when end-to-end behavior, migrations, rollout, or external flows need final verification.

## Example: Auth Uses Storage

Suppose the spec says:

> During sign in, auth must store a refresh token securely.

The decomposition should not ask the auth agent to implement storage.

Instead:

- Storage owns `SecretStorePort`.
- Storage owns the real encrypted secret store implementation.
- Storage owns storage fixtures, stubs, and contract tests.
- Auth consumes `SecretStorePort`.
- Auth receives the storage port through dependency injection.
- The composition root wires the real storage provider into auth.

Sketch:

```ts
// domains/storage/public/secret-store.port.ts
export interface SecretStorePort {
  storeSecret(input: StoreSecretInput): Promise<StoredSecret>;
}
```

```ts
// domains/auth/internal/auth.service.ts
export function createAuthService(deps: {
  secretStore: SecretStorePort;
}) {
  return {
    async signIn(credentials: Credentials) {
      const session = await authenticate(credentials);
      await deps.secretStore.storeSecret({ value: session.refreshToken });
      return session;
    },
  };
}
```

```ts
// app/composition-root.ts
const secretStore = createSecretStore(storageConfig);
const auth = createAuthService({ secretStore });
```

Auth knows what storage promises. Auth does not know how storage works.

## Example: UI Sign-In Window

Suppose the spec also says:

> The app needs a sign-in window with email, password, cancel, and submit behavior.

The UI domain can own reusable pieces:

```text
domains/ui/public/elements/input.tsx
domains/ui/public/elements/button.tsx
domains/ui/public/views/sign-in-form.tsx
```

The composition root owns the actual product flow:

```text
app/windows/sign-in.window.tsx
app/state/sign-in.state.ts
```

The UI domain renders the form and emits callbacks. The composition root decides that submitting the form calls `auth.signIn`.

## Why This Matters

This structure helps agents work independently because each task has a clear ownership boundary.

It also avoids common decomposition failures:

- One domain secretly imports another domain's internals
- A consumer invents a provider implementation it does not own
- UI components become coupled to business services
- Tests rely on private schemas instead of public behavior
- Stubs accidentally ship in production
- The final integration task has to untangle hidden dependencies

The intended result is a project where each domain can be implemented, tested, replaced, or reviewed through its public contract.

## Design Principle

A good decomposition should make the following statement true:

> Another agent can implement this domain using only the spec, this task, the interface registry, and the public interfaces of upstream domains.

If that is not true, the skill should produce a better interface task before asking agents to integrate the domains.
