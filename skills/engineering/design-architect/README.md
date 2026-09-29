# Design Architect

Design Architect is a Codex skill for generating and applying design-system UI components across:

- Native iOS with SwiftUI
- Android with Jetpack Compose and Kotlin
- React TypeScript web apps

The skill uses theme specifications from `themes/` and platform design guidance from `designs/` to produce shared styling files and app design proposals.

## How it works

Design Architect turns a selected theme and platform design spec into generated design-system code, then uses that generated code as the styling boundary for app implementation.

1. **Select the mode.** The skill identifies whether the request is for a new app, an existing project update, theme discovery, a new theme configuration, or a new design spec.
2. **Read the source material.** It loads the relevant platform guidance from `designs/`, the generic theme guidance from `themes/SPEC.md`, and the selected machine-readable theme JSON from `themes/`.
3. **Propose changes first.** For app work, the skill inspects the target project and presents a concrete proposal before editing files or running generators.
4. **Generate platform styling.** After approval, `scripts/generate_components.py` writes the platform-specific styling file into the target project root:
   - `styling.gen.swift` for SwiftUI
   - `styling.gen.kt` for Jetpack Compose/Kotlin
   - `styling.gen.ts` for React TypeScript
5. **Integrate through generated APIs.** App code should consume generated tokens, components, variants, recipes, and interaction states instead of duplicating colors, spacing, typography, or control styles locally.
6. **Verify the result.** The generator can run in `--check` mode to confirm generated files are current, and local platform build tools should be used when available.

The selected theme JSON is the machine-readable source of truth for tokens. `themes/SPEC.md` explains how agents should apply those tokens, while `designs/web.md` and `designs/mobile.md` define the platform-level layout and navigation expectations.

## Repository layout

```text
.
├── SKILL.md
├── agents/
│   └── openai.yaml
├── designs/
│   ├── mobile.md
│   └── web.md
├── scripts/
│   ├── generate_components.py
│   ├── generate_example_themes.py
│   ├── validate_themes.py
│   └── list_theme_options.py
├── themes/
│   ├── dark.json
│   ├── light.json
│   ├── oms.json
│   ├── SPEC.md
│   └── theme.schema.json
└── example/
```

## Installation

The local Codex skill path should point at this repository:

```bash
ln -s /Users/agruning/Documents/GitHub/design-architect-skill /Users/agruning/.codex/skills/design-architect
```

After installation, invoke the skill as:

```text
$design-architect
```

## Themes

Theme configurations live directly under `themes/` as JSON files:

- `themes/light.json`
- `themes/dark.json`
- `themes/oms.json`

The generic human-readable theme contract is documented in `themes/SPEC.md`. The machine-readable generation contract is each theme JSON file, validated against `themes/theme.schema.json`.

List available themes with:

```bash
python3 scripts/list_theme_options.py
```

The skill uses `themes/light.json` by default. Users can select another theme by naming it in the prompt, such as `use oms` or `use dark`.

Validate every theme config with:

```bash
python3 scripts/validate_themes.py
```

## Component generation

Generate one platform styling file into a target project root:

```bash
python3 scripts/generate_components.py <project-root> --platform typescript --theme light
```

Available platforms:

- `swift`: writes `styling.gen.swift`
- `kotlin`: writes `styling.gen.kt`
- `typescript`: writes `styling.gen.ts`

The generator reads the selected `themes/<theme-name>.json` file, validates it, and renders the selected platform file from that theme's machine-readable tokens.

Generate another theme with:

```bash
python3 scripts/generate_components.py <project-root> --platform swift --theme dark
python3 scripts/generate_components.py <project-root> --platform kotlin --theme oms
```

Use a custom Kotlin package name when needed:

```bash
python3 scripts/generate_components.py <project-root> --platform kotlin --theme light --kotlin-package com.example.designsystem
```

Check whether generated files are stale:

```bash
python3 scripts/generate_components.py <project-root> --platform typescript --theme light --check
```

## Example app

The `example/` directory contains a Vite React TypeScript app that showcases the current theme options. Generated theme modules are tracked so the example works immediately; dependencies and build output are ignored by git.

The example imports generated TypeScript theme modules from `example/src/generated/themes/`. Refresh them with:

```bash
cd example
npm run generate:themes
```

Run it locally only when dependencies are already installed:

```bash
cd example
npm run dev
```
