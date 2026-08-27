# Skills Library

Reusable agent skills organized by category.

## Skills

### Engineering

| Skill | Path | Summary |
| --- | --- | --- |
| `decompose-spec` | `skills/engineering/decompose-spec` | Splits `SPEC.md` or another supplied spec/RFC/ADR into domain-owned implementation tasks written to `TASKS.md`, with explicit public interfaces, dependency ordering, contract tests, and integration prompts. |
| `design-architect` | `skills/engineering/design-architect` | Generates and applies design-system UI components, tokens, wrappers, variants, and layouts for iOS SwiftUI, Android Jetpack Compose/Kotlin, and React TypeScript web apps. |
| `handoff-to-github` | `skills/engineering/handoff-to-github` | Creates GitHub issue handoffs from Markdown task documents, uploads task and ADR/spec files to Gists, and adds each issue to a verified GitHub Project. |
| `sdk-code-review` | `skills/engineering/sdk-code-review` | Reviews OMS Wallet SDK code, PRs, local changes, full source trees, and parity against peer SDKs across API design, errors, security, tests, docs, and compatibility. |

### Productivity

| Skill | Path | Summary |
| --- | --- | --- |
| `interview-me` | `skills/productivity/interview-me` | Conducts adaptive one-question-at-a-time interviews on a user-specified topic, ramps difficulty based on answers, and provides a final performance evaluation. |

## Installation

List the available skills in this repository:

```sh
npx skills add andygruening/skills-library --list --full-depth
```

Install every skill into the current project:

```sh
npx skills add andygruening/skills-library --all --full-depth
```

Install one skill into the current project:

```sh
npx skills add andygruening/skills-library --skill design-architect --full-depth -y
```

Install globally by adding `--global`:

```sh
npx skills add andygruening/skills-library --skill design-architect --full-depth --global -y
```

## Publishing

`npx skills` installs and updates skills from the source repository. It does not upload packages itself. To publish a new version, merge the change to `main` and push it to GitHub:

```sh
git checkout main
git pull --ff-only origin main
git merge --ff-only <branch-name>
git push origin main
```

After publishing, update one installed skill:

```sh
npx skills update design-architect --project -y
npx skills update design-architect --global -y
```

Update multiple named skills at once:

```sh
npx skills update decompose-spec design-architect handoff-to-github sdk-code-review interview-me --project -y
```

Update all installed project skills:

```sh
npx skills update --project -y
```

Update all installed global skills:

```sh
npx skills update --global -y
```

## Maintenance

When adding, updating, renaming, moving, or deleting a skill under `skills/`, update the Skills section in this README in the same change.
