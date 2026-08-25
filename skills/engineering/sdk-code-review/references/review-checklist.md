# OMS SDK PR Review Checklist

Load this checklist when reviewing source, architecture, error handling, security, public API behavior, or non-trivial project structure changes.

## Project Structure

- Confirm new files belong in the established module, package, or target.
- Check that test files mirror source ownership and protect the changed behavior.
- Look for duplicated SDK concepts that should share existing primitives.
- Check dependency direction: core SDK code should not depend on demo apps, examples, tests, or platform-specific layers unless that is an established boundary.
- Note generated files, lockfiles, fixtures, and vendored assets separately from hand-written source.

## Public API and SDK Compatibility

- Identify any public symbols, exported types, protocol interfaces, request/response shapes, or package entry points that changed.
- Check source compatibility, binary compatibility where relevant, default behavior changes, and semantic version implications.
- Verify examples, docs, README snippets, and demo app usage still match the API.
- Prefer idiomatic language conventions while preserving cross-SDK conceptual parity.

## Error Handling

- Verify failures are typed or documented enough for SDK consumers to recover.
- Check that low-level errors are not swallowed, over-wrapped, or leaked with unstable implementation details.
- Confirm async callbacks, promises, coroutines, or completion handlers deliver exactly one terminal result.
- Check cancellation, timeout, retry, and cleanup behavior when network or wallet operations fail.
- Ensure validation errors are reported before unsafe side effects.

## Security

- Search changed files for accidental secrets, tokens, private keys, mnemonic phrases, API keys, or test credentials.
- Check wallet/key handling, signing, encryption, randomness, nonce usage, storage, logging, and serialization.
- Verify sensitive values are redacted from logs, thrown errors, analytics, and debug output.
- Check network calls for TLS assumptions, host validation, request signing, replay resistance, and authorization propagation.
- Treat dependency updates, build script changes, generated code, and CI changes as supply-chain review surfaces.

## Testing

- Expect tests for new public behavior, error branches, security-sensitive logic, and regressions.
- Prefer integration tests for cross-module SDK flows and unit tests for deterministic mapping/validation logic.
- Check edge cases: null or missing fields, malformed input, network failure, duplicate callbacks, concurrent calls, cancellation, and platform-specific behavior.
- Note when tests assert implementation details instead of observable SDK behavior.

## Review Smells

- New abstractions with one caller and no clear ownership boundary.
- Error messages that expose secrets or hide the actionable cause.
- Silent fallback behavior in authentication, signing, or transaction paths.
- Public API names that differ from established OMS SDK terminology.
- Large file moves mixed with behavior changes.
- Tests that only cover happy paths after changing error, security, or network code.
