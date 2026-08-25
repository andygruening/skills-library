---
name: design-architect
description: Generate design-system UI components, build new design-system-styled apps, and retrofit existing apps for native iOS SwiftUI, Android Jetpack Compose/Kotlin, and React TypeScript web. Use when Codex needs shared styling wrappers, design tokens, buttons, inputs, labels, dropdowns, badges, alerts, cards, navigation primitives, or app screens that consume generated styling files from a design-system bundle.
---

# Design Architect

## Source

Use this skill to generate and apply the selected design-system theme through the platform-specific styling file: `styling.gen.swift` for iOS, `styling.gen.kt` for Android, and `styling.gen.ts` for React TypeScript web. After generation, that generated styling file is the required implementation source for tokens, component wrappers, variants, recipes, and interaction states. All platform UI must consume tokens and components from the generated styling file whenever the generated file provides them.

Use the `light` theme configuration by default. If the user names another theme configuration, such as `use oms`, read `themes/SPEC.md` plus `themes/<theme-name>.json`. Treat the selected theme JSON as the machine-readable generation source and `themes/SPEC.md` as generic human/agent guidance for applying any theme.

## Proposal Gate

Do not make file changes immediately when this skill is triggered. First inspect enough context to understand the request, read the relevant reference files, and propose all intended changes before editing, generating, or integrating anything.

Only proceed with implementation after the user gives clear approval such as `go ahead`, `integrate all changes`, `do it`, or an equivalent confirmation. If the user approves only part of the proposal, implement only the approved subset.

If the user explicitly asks for code changes in the same message that triggers the skill, still provide the proposal first and wait for approval unless the user also explicitly says to skip the proposal gate.

## Proposal Response Format

Use a polished proposal format with large section titles, emoji in the titles, and horizontal separators. Product UI copy rules still apply to generated app content, but the proposal response itself may use emoji and expressive headings.

Make proposals precise and implementation-ready. Do not present alternatives such as "do this or that", "either X or Y", or open-ended option lists. Choose the best path based on the skill instructions and project context, then state exactly what to integrate. Proposals are used as context for later integration, so every proposed change must be a clear directive.

In the `Theme` and `Design` sections, prioritize every proposal as `P1`, `P2`, or `P3`, and sort proposals in that order. Create one category heading for each priority that has proposals, then put plain bullet points under that heading. Do not prefix every bullet with the priority marker. Use these Markdown-safe visual priority headings:

- P1: required for correctness, navigation integrity, production readiness, accessibility, or core design-system compliance.
- P2: important for usability, layout quality, platform fit, or consistency.
- P3: polish, refinement, or lower-risk improvements.

Structure proposal responses like this:

```markdown
# 🎨 Design proposal

---

## 🧭 What I understand

[Brief summary of the app, platform, audience, and design goal.]

---

## 🌟 Theme

[Evaluate the app against `themes/SPEC.md` and the selected theme configuration's `theme.json`. State the exact theme/component changes to make. Sort proposals under priority headings: "#### P1", then "#### P2", then "#### P3". Omit empty priority headings. Put plain bullet points under each heading. Use direct wording and avoid alternatives.]

---

## 🧱 Design

[Evaluate the app against `designs/web.md` for web or `designs/mobile.md` for iOS/Android. State the exact pages/screens, flows, navigation structures, content placement, and layout changes to implement. Sort proposals under priority headings: "#### P1", then "#### P2", then "#### P3". Omit empty priority headings. Put plain bullet points under each heading. Use direct wording such as "Add X page", "Move Y into Z", or "Remove X".]

---

## ▶️ Next step

Say `go ahead` to integrate all changes, or tell me which proposed changes to do instead.
```

## Default Workflow

1. Identify the trigger mode:
   - **New app from idea**: the user must provide the target platform(s) (`ios`, `android`, and/or `web`) and the app idea. If either is missing, ask for only that missing input. Propose the app structure before building from scratch, including how the idea will use the shared generated styling file for each platform: `styling.gen.swift` for iOS, `styling.gen.kt` for Android, and `styling.gen.ts` for React TypeScript web. State that generated tokens/components are mandatory for colors, typography, spacing, controls, variants, and states. Question the first obvious layout; make the proposal feel modern and organized, using tabs, segmented controls, sidebars, split views, or section navigation when one long page would feel cluttered.
   - **Existing project update**: inspect the current project, identify its platform(s), and propose how to generate or refresh the relevant styling file(s), then replace local one-off styling with semantic usage of the generated wrappers/recipes. Treat app-local colors, radii, typography scales, button/input/card styles, and state styles as migration targets whenever equivalent generated tokens/components exist. Preserve user changes and avoid broad rewrites. Review the existing layout choices and propose modernization when possible, especially by breaking crowded single-page screens into tabs, sections, or clearer navigation.
   - **List theme options**: if the user asks what theme configurations are available, run `python3 /path/to/design-architect/scripts/list_theme_options.py` and use the script output as the source of truth. Respond with a short, polished Markdown list titled `Available theme options`, with each option formatted as `- **<name>**: <description>`.
   - **Create theme config**: if the user asks to create a new theme configuration, inspect `themes/SPEC.md` and `themes/theme.schema.json`, then propose copying `themes/light.json` into `themes/<new-name>.json` and updating it to match the user's new theme specifications and the required theme schema. After approval, copy the default theme JSON, update its metadata with the new `name` and `description`, and keep it valid against `themes/theme.schema.json`.
   - **Create design spec**: if the user asks to create a new design spec, copy `designs/web.md` into `designs/<new-name>.md`. Update the frontmatter `name` and `description`, then revise the scope, design patterns, and validation checklist to match the user's design specifications.
2. Identify the project root for the current task. Default to the current working directory.
3. Read the relevant reference files and present the proposal using the required proposal response format.
4. Evaluate new-project and existing-project proposals in two categories:
   - **Theme**: select a theme configuration, read `themes/SPEC.md` and the selected `themes/<name>.json`, then verify whether the app uses that theme's design system specifications for color, typography, motion, iconography, product voice, and component variants. Use `themes/light.json` by default. If the user says `use oms` or names another available configuration, use `themes/<name>.json` instead. Propose any design-token, component, styling, or interaction changes needed to align the app.
   - **Design**: read `designs/web.md` for web projects and `designs/mobile.md` for iOS or Android projects. If a task covers multiple platforms or named design specs, read each matching `.md` file under `designs/`. Treat the matching design instructions as mandatory. Analyze what each existing or proposed page/screen is doing, verify whether each page/screen aligns with the required design patterns, and propose structural changes based on required flows and page/screen patterns. Always verify that the app has a separate `Home`, landing, welcome, or introduction page/screen that introduces and sells the app before the first real product workflow, with a clear primary CTA that routes to the first real page/screen. Check whether authentication requires sign-in/sign-up/recovery/verification pages or screens, where the main content should live, which dashboard/detail/list/form/settings pages or screens are needed, and whether navigation matches the target platform. Check every visible button, link, nav item, CTA, footer link, toolbar action, tab, list row, and in-app route target; if it points to a page/screen or flow that does not exist, propose integrating that missing page/screen or removing/retargeting the control when the destination should not exist. Evaluate whether the app exposes debug, implementation, or environment data in the UI, such as `server is ready`, raw API responses, localhost URLs, stack traces, test IDs, sandbox mode labels, mock/dev banners, console output, feature-flag names, or similar non-product information; propose removing or replacing it with product-appropriate states unless the user explicitly requires an environment indicator.
5. Make proposals for both categories based on this skill's instructions, even when one category has no major issues. State when no changes are needed for a category. Keep proposals decisive: do not include option lists, unresolved alternatives, or vague recommendations. If several valid approaches exist, choose one and propose that specific implementation.
6. Wait for the user to approve the proposal before running generators, editing files, or integrating changes.
7. For new app and existing project update modes, run the bundled generator only for the requested or detected platform after approval. Always pass `--platform` and the selected theme with `--theme`; use `light` when the user did not name a theme:

   ```bash
   python3 /path/to/design-architect/scripts/generate_components.py <project-root> --platform <swift|kotlin|typescript> --theme <theme-name>
   ```

8. Review the generated file for the selected platform:
   - `styling.gen.swift`: SwiftUI tokens and reusable iOS components.
   - `styling.gen.kt`: Jetpack Compose/Kotlin tokens and reusable Android components.
   - `styling.gen.ts`: TypeScript tokens, typed variants, and React-friendly component recipes for web parity.
9. Integrate the generated styling file as the required design-system boundary:
   - iOS must use `DesignTokens`, generated SwiftUI components, generated variants, and generated `ButtonStyle`/wrapper types from `styling.gen.swift`.
   - Android must use generated `DesignColors`, `DesignTypography`, `DesignSpacing`, generated Compose wrappers, and generated variants from `styling.gen.kt`.
   - React TypeScript must use `designTokens`, generated recipe exports, and generated variant types from `styling.gen.ts`.
   - Do not duplicate generated token values or recreate generated component styling in app files. If a needed primitive is missing from the generated file, update the generator or theme schema instead of hardcoding a parallel design system.
10. If the user explicitly requires a different package name, rerun with:

   ```bash
   python3 /path/to/design-architect/scripts/generate_components.py <project-root> --platform kotlin --theme <theme-name> --kotlin-package com.example.designsystem
   ```

11. Keep generated file names stable. `styling.gen.ts` is the TypeScript design-token/component-recipe output; Kotlin implementation belongs in `styling.gen.kt`.

## Reference Files

- Select the theme configuration before reading theme files. Default to `themes/light.json`. If the user says `use oms`, read `themes/oms.json`. If they name another available theme configuration, read `themes/<name>.json`.
- Read `themes/SPEC.md` before applying visual foundations, typography, color, motion, icon, product voice, component usage, state handling, or layout patterns. Its frontmatter must define `name` and `description`, and its guidance applies generically to every theme.
- Each theme configuration must be a JSON file directly under `themes/`, such as `themes/light.json`, `themes/dark.json`, or `themes/oms.json`.
- Read the selected theme JSON as the source of truth for generated design tokens. It must conform to `themes/theme.schema.json`.
- Read `designs/web.md` whenever making web page design decisions to identify required page types, states, navigation structure, and page-level layout rules.
- Read `designs/mobile.md` whenever making iOS or Android app design decisions to identify required screen types, states, navigation structure, and screen-level layout rules.
- When creating a new design spec, copy `designs/web.md` into `designs/<new-name>.md`, then update it for the requested design.

## Theme Commands

- To list available theme options, run:

  ```bash
  python3 /path/to/design-architect/scripts/list_theme_options.py
  ```

  Use the script output as the source of truth, then respond in this format:

  ```markdown
  **Available theme options**
  - **<name>**: <description>
  - **<name>**: <description>
  ```
- To create a new theme configuration, inspect `themes/SPEC.md` and `themes/theme.schema.json`, copy `themes/light.json` into `themes/<new-name>.json`, then update the copied file based on the user's theme specifications. Keep the theme JSON valid against `themes/theme.schema.json`; do not create a per-theme directory or per-theme `SPEC.md`.
- To create a new design spec, copy `designs/web.md` into `designs/<new-name>.md`, then update the copied file based on the user's design specifications. Keep frontmatter concise and include only `name` and `description`.
- To generate components for a selected theme, run:

  ```bash
  python3 /path/to/design-architect/scripts/generate_components.py <project-root> --platform <swift|kotlin|typescript> --theme <theme-name>
  ```

  The generator reads `themes/<theme-name>.json`, validates it, and renders only the selected platform file from that theme. If the user does not name a theme, pass `--theme light`.

## Product Rules

- Use sentence case. No Title Case, emoji, exclamation marks, or marketing CTA language.
- Use functional labels such as `Save`, `Cancel`, `Documentation`, and `Create deposit address`.
- Use precise financial formatting and tabular numerals for money, counts, percentages, addresses, and timestamps.
- Do not introduce new hex values when a selected theme token exists.
- Do not use gradient backgrounds except the sandbox/live status banner and explicitly defined data-viz gradients.
- Do not add decorative icons; every icon labels an action or state.

## Implementation Rules

- Put generated implementation files at the project root.
- For new app mode, build only the requested platform apps: iOS means SwiftUI, Android means Jetpack Compose/Kotlin, and web means React TypeScript. The generated styling file for that platform is the source of component styling. Once generated, use `styling.gen.swift`, `styling.gen.kt`, or `styling.gen.ts` as the implementation source for tokens, components, variants, recipes, and interaction states.
- Using generated styling is mandatory for all platforms. App code must import and consume generated tokens, generated component wrappers, generated variants, and generated interaction-state recipes whenever those exports exist.
- Do not hardcode colors, spacing, radii, typography, borders, shadows, motion values, button styles, input styles, badge styles, card styles, or selected/hover/focus/disabled states in app code when a generated token, component, variant, or recipe exists.
- If generated styling is insufficient, extend the selected theme JSON, `themes/theme.schema.json`, or `scripts/generate_components.py` so the missing token/component becomes generated. Do not create a second app-local design system.
- React TypeScript apps must include interaction styling for hover, active/click/pressed, focus-visible, and disabled states for buttons, icon buttons, fields, dropdowns, tabs, and other interactive controls where applicable. Derive those states from `styling.gen.ts` recipes and tokens.
- Keep app call sites semantic. App screens should consume generated component variants, not restyle them or reimplement their token values locally.
- Prefer SwiftUI `ButtonStyle` and composable wrappers for Swift.
- Prefer Jetpack Compose Material 3 wrappers for Kotlin.
- TypeScript should export tokens, typed variants, and React-friendly component style recipes rather than raw prose.
- Do not introduce network-dependent setup unless the user asks to build or run the apps.
- If generated files already exist, inspect them first and preserve user changes unless the task clearly asks to regenerate.

## Verification

After generation, run:

```bash
python3 /path/to/design-architect/scripts/generate_components.py <project-root> --platform <swift|kotlin|typescript> --theme <theme-name> --check
```

Use available local build tools when present:

- iOS: run the project or package's local Xcode build command when Xcode and an iOS SDK are available.
- Android: use the project's Gradle wrapper or installed Gradle if present. Do not download Gradle or Android dependencies without user approval.
- Web: run the project's local build command only when dependencies are already installed. Do not run `npm install` or download web dependencies without user approval.
