---
name: Web
description: Mandatory design patterns for web pages, routes, states, navigation, layout frames, and production UI hygiene.
---

# Web Page Design

This document defines mandatory design patterns for web pages.

Read this file first whenever the skill must make web page design decisions. Use it to identify which web page types, states, flows, navigation structures, and layout rules an app needs.

The instructions in this file are mandatory for web design evaluation. Analyze what each web page is doing, then verify whether that page aligns with the relevant patterns below.

## Web Page Design Patterns

### Home / Introduction

Every web app must include a separate `Home`, landing, welcome, or introduction page that explains what the app does and sells the value before the first real product workflow. This page must not be the primary dashboard, list, editor, checkout, chat, or operational surface. Include a clear primary call-to-action button that routes users to the first real page or flow, such as sign-up, login, dashboard, create flow, search, product listing, or onboarding. For existing apps, propose adding this page when the first visible page is already the product workflow.

Relevant page types: landing page, welcome or introduction page, main home page, dashboard or home page.

### Authentication

Common pages include login, sign-up, password recovery, reset password, verification, SSO callback, and session-expired states. These pages need strong validation, clear error handling, password-manager support, and secure redirects.

Relevant page types: login, sign-up, forgot password, reset password, email verification, verification, account security.

### Navigation

Web apps usually use top headers, sidebars, breadcrumbs, tabs, and in-page navigation. Every web app needs a clear current location and predictable paths back to primary work.

For web apps with multiple pages, include a header with navigation buttons or links for each primary page unless the product clearly needs an authenticated app shell with sidebar navigation instead. Keep the header stable across public pages, show the current page when useful, and include authentication or primary action controls on the right.

Every visible button, link, navigation item, CTA, footer link, and in-app route target must resolve to an existing page, route, or flow. During design evaluation, identify controls that point to missing pages. Propose integrating those missing pages when they fit the app's expected flows, or propose removing or retargeting the controls when the destination should not exist.

Relevant page types: landing page, dashboard or home page, main home page, welcome or introduction page, loading or splash page.

### Web App Layout Frame

Web apps should name and evaluate the main layout frame using `Top header`, `Footer`, and `Page width`. Verify that public/multi-page web apps have a `Top header` with logo or product name, navigation buttons or links for each primary page, and right-side authentication/account/CTA controls. Verify that pages needing secondary/legal/support navigation have a `Footer`.

`Page width` is mandatory for web pages. Main page content must use a consistent centered page-width container with `max-width: 1200px` so content stays readable on wide screens instead of stretching edge-to-edge. Apply page width to primary content areas, forms, lists, detail views, dashboards, help/legal pages, and landing-page inner content. Full-width bands are allowed only for deliberate page sections such as hero backgrounds, status bands, or visual separators, and their inner content should still align to the 1200px page-width container.

`Top header` must be sticky to the top of the viewport. The header background must span the full viewport width with no outer page padding constraining the background. Apply the 1200px page-width container only to the header inner content, such as the logo, navigation buttons, account controls, and CTAs. Pages with a sticky top header must reserve top space using padding, margin, scroll padding, or equivalent layout offset so page content never renders underneath the header. Usually contains the logo or product name on the left, page navigation buttons or links in the center/left, and authentication, account, or primary action controls on the right. Use this name instead of vague labels like navbar, topbar, or menu unless matching existing code.

`Footer` must sit at the bottom of the page flow. If page content is taller than the viewport, the footer appears below the last content. If page content is shorter than the viewport, the footer sticks to the very bottom of the viewport. Prefer a min-height page shell with flexible main content for this behavior rather than fixed-position footers that overlap content. Region for secondary navigation, support links, legal links, copyright, status, or low-priority product links. Keep it visually quiet and do not use it for primary app workflows.

Relevant page types: landing page, dashboard or home page, list or index page, detail page, create/edit form page, help or documentation page, legal pages.

### Box Usage

Use boxes, cards, and panels only when content needs structure, separation, repeated comparison, or a framed task surface. Good uses include repeated items, pricing plans, product cards, list rows, dashboard metrics, forms, settings groups, detail panels, modals, popovers, toasts, tables, and framed tools.

Do not put hero text, welcome text, page titles, intro copy, primary marketing messages, short explanatory sections, navigation, headers, or footers inside boxes. These should usually sit directly on the page background with clear spacing, alignment, and page-width constraints. If the content is a single narrative message, keep it unboxed. If there are many sibling items to compare or scan, boxes are appropriate.

Relevant page types: landing page, welcome or introduction page, dashboard or home page, list or index page, detail page, create/edit form page, pricing page.

### Visual Placeholders

Do not generate images for web page visuals unless the user explicitly asks for generated or real images. Use placeholder gradients for hero media, product previews, thumbnails, empty media slots, and illustration areas. Keep placeholder gradients restrained and aligned with OMS tokens rather than using decorative blobs or unrelated stock-like imagery.

Relevant page types: landing page, welcome or introduction page, dashboard or home page, product preview, empty state, media preview.

### Data States

Most pages need loading, empty, error, offline, success, and permission-denied states. These should be designed as part of the page, not added as afterthoughts.

Relevant page types: empty state, error/offline state, error or maintenance page, 404/not found page, status page, permission prompt or setup page.

### Production UI Hygiene

Apps must not expose debug, implementation, test, or environment data in product UI. Remove or replace labels such as `server is ready`, `localhost`, raw API payloads, stack traces, console output, mock data notices, test IDs, internal route names, feature-flag names, sandbox mode labels, dev banners, or similar non-product information. Use product-appropriate loading, empty, error, offline, permission, or status states instead. Only show environment indicators when the user explicitly requires them and the design makes them intentional product UI rather than debug leakage.

Relevant page types: empty state, error/offline state, error or maintenance page, status page, permission prompt or setup page.

### Forms

Forms need labels, required indicators, validation rules, default values, helper text, error messages, save/cancel actions, and unsaved-change handling. Long forms usually need grouping and progress.

Relevant page types: create/edit form page, create or compose page, edit page, onboarding wizard, onboarding flow, contact/support page.

### Tables and Lists

Tables and lists need sorting, filtering, search, pagination or infinite scroll, row actions, selection states, and empty states. Responsive web layouts can replace dense tables with rows or cards on narrow viewports.

Relevant page types: list or index page, list page, search results page, search page, feed or activity page, favorites or saved items page.

### Detail Views

Detail views usually need title, status, metadata, primary actions, secondary actions, related records, history/activity, and edit/delete controls. They often support deep links.

Relevant page types: detail page, profile page, reports or analytics page.

### Settings

Settings pages usually group personal settings, organization settings, notifications, billing, security, integrations, legal links, and destructive actions. Sensitive changes should require confirmation or reauthentication.

Relevant page types: account settings, team or organization settings, settings page, account/security page, billing/subscription page, notifications page.

### Commerce

Commerce apps commonly need product listing, product detail, cart, checkout, payment method, order confirmation, order history, returns, and receipts. Pricing, availability, taxes, fees, and fulfillment status must be explicit.

Relevant page types: pricing page, billing/subscription page, cart page, checkout page, payment method page, order history page.

### Support

Support experiences usually include help search, FAQ/article pages, contact forms, ticket history, live chat, status pages, and escalation paths. Users need confirmation that their issue was received.

Relevant page types: help center or documentation page, contact/support page, help/support page, messages/inbox page, messages/chat page, status page.

### Legal and Compliance

Most products need terms, privacy policy, cookie policy, data consent, unsubscribe preferences, account deletion, and data export flows depending on jurisdiction and product type.

Relevant page types: legal pages, about page, account settings, account/security page.
