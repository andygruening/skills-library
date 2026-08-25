---
name: Mobile
description: Mandatory design patterns for iOS and Android screens, states, navigation, layout frames, and production UI hygiene.
---

# Mobile App Design

This document defines mandatory design patterns for iOS and Android app screens.

Read this file first whenever the skill must make mobile app design decisions. Use it to identify which mobile screen types, states, flows, navigation structures, and layout rules an app needs.

The instructions in this file are mandatory for mobile design evaluation. Analyze what each iOS or Android screen is doing, then verify whether that screen aligns with the relevant patterns below.

## Mobile App Design Patterns

### Home / Introduction

Every mobile app must include a separate welcome, introduction, or home screen that explains what the app does and sells the value before the first real product workflow. This screen must not be the primary dashboard, list, editor, checkout, chat, or operational surface. Include a clear primary call-to-action button that routes users to the first real screen or flow, such as sign-up, login, onboarding, dashboard, create flow, search, or product listing. For existing apps, propose adding this screen when the first visible screen is already the product workflow.

Relevant screen types: welcome or introduction screen, main home screen, dashboard or home screen, onboarding entry screen.

### Authentication

Common screens include login, sign-up, password recovery, reset password, verification, biometric prompt, SSO handoff, and session-expired states. These screens need strong validation, clear error handling, password-manager support, secure redirects, and platform-appropriate keyboard behavior.

Relevant screen types: login, sign-up, forgot password, reset password, email/SMS verification, OTP verification, biometric unlock, account security.

### Navigation

Mobile apps usually use bottom navigation, top app bars, back buttons, stacked navigation, tab views, segmented controls, and modal sheets. Every mobile app needs a clear current location and predictable paths back to primary work.

Use bottom navigation for three to five primary destinations. Use a top app bar for screen title, back navigation, and one or two high-priority actions. Use tabs or segmented controls for peer views within the same screen. Avoid burying primary navigation in overflow menus.

Every visible button, link, list row, tab, CTA, toolbar action, and route target must resolve to an existing screen or flow. During design evaluation, identify controls that point to missing screens. Propose integrating those missing screens when they fit the app's expected flows, or propose removing or retargeting the controls when the destination should not exist.

Relevant screen types: welcome or introduction screen, main home screen, dashboard or home screen, search screen, list screen, detail screen, settings screen.

### Mobile App Layout Frame

Mobile apps should name and evaluate the main layout frame using `Top app bar`, `Bottom navigation`, `Screen content`, and `Safe area`. Verify that screens respect platform safe areas, keyboard insets, status bars, gesture areas, and bottom navigation height.

`Screen content` should use readable horizontal padding and avoid edge-to-edge text unless the platform pattern calls for media, maps, camera, or full-bleed visual content. Primary content should be vertically scannable, with stable spacing and no overlap with sticky top or bottom app chrome.

`Top app bar` usually contains the screen title, back button when the screen is nested, and a small set of high-priority actions. Avoid cramming many actions into the app bar.

`Bottom navigation` should be sticky to the bottom of the viewport when used. Screen content must reserve bottom space so lists, forms, buttons, and tab content do not render underneath it.

Relevant screen types: main home screen, dashboard or home screen, list screen, detail screen, create/edit screen, profile screen, settings screen.

### Box Usage

Use boxes, cards, and panels only when content needs structure, separation, repeated comparison, or a framed task surface. Good uses include repeated list rows, product cards, dashboard metrics, forms, settings groups, detail panels, bottom sheets, dialogs, snackbars, and framed tools.

Do not put welcome text, screen titles, intro copy, primary marketing messages, short explanatory sections, top app bars, or bottom navigation inside boxes. These should usually sit directly on the screen background with clear spacing, alignment, and safe-area constraints. If the content is a single narrative message, keep it unboxed. If there are many sibling items to compare or scan, boxes are appropriate.

Relevant screen types: welcome or introduction screen, dashboard or home screen, list screen, detail screen, create/edit screen, pricing or plan screen.

### Visual Placeholders

Do not generate images for mobile screen visuals unless the user explicitly asks for generated or real images. Use placeholder gradients for welcome visuals, product previews, thumbnails, empty media slots, and illustration areas. Keep placeholder gradients restrained and aligned with OMS tokens rather than using decorative blobs or unrelated stock-like imagery.

Relevant screen types: welcome or introduction screen, dashboard or home screen, product preview, empty state, media preview.

### Data States

Most screens need loading, empty, error, offline, success, permission-denied, and retry states. These should be designed as part of the screen, not added as afterthoughts.

Relevant screen types: empty state, error/offline state, permission prompt, maintenance state, status screen.

### Production UI Hygiene

Apps must not expose debug, implementation, test, or environment data in product UI. Remove or replace labels such as `server is ready`, `localhost`, raw API payloads, stack traces, console output, mock data notices, test IDs, internal route names, feature-flag names, sandbox mode labels, dev banners, or similar non-product information. Use product-appropriate loading, empty, error, offline, permission, or status states instead. Only show environment indicators when the user explicitly requires them and the design makes them intentional product UI rather than debug leakage.

Relevant screen types: empty state, error/offline state, maintenance state, status screen, permission prompt.

### Forms

Forms need labels, required indicators, validation rules, default values, helper text, error messages, save/cancel actions, and unsaved-change handling. Mobile forms also need keyboard-aware layout, suitable input types, focus order, large touch targets, and clear submit placement. Long forms usually need grouping and progress.

Relevant screen types: create/edit screen, compose screen, onboarding flow, contact/support screen, checkout screen, settings screen.

### Lists

Lists need search, filtering, sorting when useful, pagination or infinite scroll, row actions, selection states, swipe actions only when discoverable, and empty states. Dense data should become readable mobile rows or cards instead of desktop-style tables.

Relevant screen types: list screen, search screen, feed or activity screen, favorites or saved items screen, order history screen.

### Detail Views

Detail views usually need title, status, metadata, primary actions, secondary actions, related records, history/activity, and edit/delete controls. They often support deep links and should have reliable back navigation.

Relevant screen types: detail screen, profile screen, reports or analytics screen, order detail screen.

### Settings

Settings screens usually group personal settings, organization settings, notifications, billing, security, integrations, legal links, and destructive actions. Sensitive changes should require confirmation, biometric confirmation, or reauthentication.

Relevant screen types: settings screen, account/security screen, billing/subscription screen, notifications screen.

### Commerce

Commerce apps commonly need product listing, product detail, cart, checkout, payment method, order confirmation, order history, returns, and receipts. Pricing, availability, taxes, fees, and fulfillment status must be explicit.

Relevant screen types: product list screen, product detail screen, cart screen, checkout screen, payment method screen, order history screen.

### Support

Support experiences usually include help search, FAQ/article screens, contact forms, ticket history, live chat, status screens, and escalation paths. Users need confirmation that their issue was received.

Relevant screen types: help/support screen, contact/support screen, messages/chat screen, status screen.

### Legal and Compliance

Most products need terms, privacy policy, data consent, notification permission rationale, account deletion, and data export flows depending on jurisdiction and product type.

Relevant screen types: legal screen, about screen, account settings, account/security screen.
