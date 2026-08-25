---
name: Theme system
description: Generic theme guidance for applying any design-architect theme JSON file across SwiftUI, Jetpack Compose, and React TypeScript.
---

# Theme guidance

Use this spec with the selected `themes/<theme-name>.json` file, such as `themes/light.json`, `themes/dark.json`, or `themes/oms.json`. The selected JSON file is the source of truth for concrete colors, typography, spacing, radii, borders, shadows, motion, and component values. This spec explains how to apply those values consistently for any theme.

# Color and typography

- Use the selected theme's page/background tokens for page and app-shell backgrounds. Do not invent page colors outside the selected theme JSON file.
- Use surface tokens for cards, panels, forms, modals, drawers, popovers, and toasts.
- Use primary text tokens for headings, titles, important labels, and main content. Use secondary and placeholder text tokens for supporting copy, metadata, empty fields, and disabled states.
- Use brand tokens sparingly for links, focus rings, selected states, active navigation, and branded emphasis. Do not use brand color as the default CTA fill unless the selected theme defines it that way.
- Use semantic tokens only for status communication: success, warning, info, danger, destructive fields, alerts, transaction states, and validation.
- Use the selected theme's typography family, weights, line height, and scale. Use tabular numerals for balances, counts, percentages, timestamps, addresses, IDs, and table columns where the platform supports it.

# Components

- Use primary buttons for the main action in a view, form, dialog, or workflow step.
- Use secondary buttons for supporting actions, toolbar controls, filters, cancel-like actions, and lower-priority commands.
- Use selected button styling for active tabs, segmented controls, selected filters, active navigation items, selected rows, and selected resource states.
- Use danger buttons only for destructive, irreversible, or security-sensitive actions. Use danger secondary when the destructive action exists but should not dominate the workflow.
- Use inputs for search, filters, form fields, labels, amounts, addresses, IDs, and editable configuration. Keep labels, helper text, focus states, disabled states, and destructive states aligned with the selected theme tokens.
- Use dropdowns when the user chooses one value from a closed set. Style dropdowns like inputs and add a trailing affordance.
- Use badges for compact state labels, counts, categories, table states, row metadata, chain/network labels, risk labels, and status indicators.
- Use alerts for persistent messages, form-level validation, security warnings, empty-state blockers, operational notices, and system feedback that needs a title plus supporting text.
- Use cards and panels for repeated items, structured groups, modals, resource summaries, settings groups, and tool surfaces. Do not wrap hero text, page headings, welcome copy, or primary marketing messages in cards.
- Use icon buttons for toolbar actions, row actions, close controls, copy actions, overflow menus, and compact navigation. Icons must identify an action or state.

# States

- Hover states must be derived from the selected theme's hover, surface hover, button hover, border hover, or semantic hover tokens.
- Active and pressed states should be stronger than hover states without shifting layout.
- Focus-visible states must use the selected theme's focus token and remain visible on the theme's page and surface backgrounds.
- Disabled states must use disabled or muted tokens and remain legible. Do not rely on opacity alone.
- Destructive states must use danger tokens only when the field, action, or message is actually destructive or invalid.
- Selected states must be visually distinct from hover and active states and must use selected or brand-related theme tokens.

# Layout patterns

- Use the selected theme's spacing scale for page sections, cards, control groups, and compact toolbar layouts.
- Keep app pages unframed unless the selected design spec requires a framed tool surface.
- Prefer product-oriented layouts: tables, filter bars, sidebars, split views, tabs, section headers, details panes, compact cards, and structured forms.
- Avoid nested cards, decorative gradients, decorative icons, and one-off colors that are not present in the selected theme.
- Keep navigation clear and operational. Do not expose debug state, raw implementation details, localhost URLs, stack traces, environment internals, or generated file metadata in the product UI unless explicitly required.
