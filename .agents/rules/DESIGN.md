## Project Design System
Project: صفقات ذكية
Type: Enterprise Arabic RTL procurement platform
Tone: institutional, premium, restrained, trustworthy, operational

---

## Design Intent

This product is not a startup marketing app.
It is a high-trust institutional system for procurement workflows, restricted access procedures, executive dashboards, and committee-driven actions.

The interface must feel:
- serious
- modern
- calm
- dense but readable
- secure
- audit-aware
- premium without visual noise

Avoid all generic AI UI aesthetics.

---

## Layout Philosophy

- Arabic RTL first
- desktop-first for operations, mobile-safe adaptation
- modular dashboard structure
- clear horizontal and vertical hierarchy
- state and action always above decorative detail
- progressive disclosure for sensitive content
- tables and panels over playful cards
- side rails and drawers for audit/activity where appropriate

Preferred structure:
1. page identity
2. state banner
3. action region
4. main record data
5. support panels
6. activity / audit

---

## Color System

### Base Palette
- Background: deep graphite or soft institutional off-white depending on theme
- Surface 1: dark slate / clean white
- Surface 2: slightly raised neutral layer
- Border: soft cool gray
- Primary: restrained institutional blue
- Success: controlled green
- Warning: muted amber
- Danger: controlled red
- Info: cool blue-gray

### Rules
- no purple-blue AI gradients
- no neon
- no rainbow dashboards
- use color for state, not decoration
- every status must also include text/icon

---

## Typography

Arabic-first UI typography.
Use a modern Arabic sans-serif with excellent clarity.
Style target:
- compact
- high readability
- strong section labels
- clear table text
- medium-density interface copy

Rules:
- no oversized headings
- no excessive stylistic contrast
- no decorative display fonts
- page titles: strong but compact
- labels and statuses: concise
- body text: neutral and readable

---

## Spacing

- compact enterprise spacing
- enough breathing room for legibility
- avoid oversized padding
- tables should feel dense but not cramped
- action bars and banners should feel structured, not crowded

Spacing rules:
- smaller spacing inside data-dense components
- medium spacing between sections
- larger spacing only around critical transitions or state banners

---

## Components

Preferred component library patterns:
- page header with breadcrumb
- state banner
- summary cards
- dense tables
- filter bars
- side drawers
- audit timelines
- warning callouts
- approval tracker
- permission notice
- empty state
- loading skeleton
- confirmation modal
- printable record view

Avoid:
- decorative feature cards
- marketing blocks
- oversized stat tiles
- floating promotional widgets

---

## Tables

Tables are a core UI pattern in this product.

Rules:
- identifier first
- state and date near the front
- hide sensitive fields until authorized
- use contextual row actions only
- support filtering visibly
- no icon-only ambiguity for important actions
- badges must include text labels

---

## States

Each major screen must define:
- default
- loading
- empty
- warning
- blocked
- success
- error
- insufficient permissions

Blocked states should:
- explain why
- identify missing condition
- suggest next step
- avoid raw technical language

---

## Audit & History

Audit visibility is part of the design system.
For sensitive workflows, always provide:
- activity rail
- timeline
- status change log
- actor + action + time
- expandable details

Audit should look permanent, useful, and reviewable.

---

## Motion

- subtle only
- fast and calm
- no playful bounce
- no cinematic over-animation
- use motion for state change clarity only
- confirmation and transitions should feel deliberate

---

## Content Style

Arabic UI copy must be:
- formal
- clear
- institutional
- direct
- short
- non-ambiguous

Prefer:
- "بانتظار الموافقة"
- "غير متاح قبل استيفاء الشروط"
- "تم تسجيل العملية"
- "تعذر إتمام الإجراء"

Avoid:
- hype
- marketing tone
- casual slang
- vague success messages

---

## Product-Specific Rules

For procurement and sealed bid workflows:
- do not expose financial details too early
- do not merge opening and evaluation visually
- show permission context
- make audit visible
- show one primary action per critical state
- treat official records as first-class UI artifacts

For dashboards:
- prioritize alerts, delays, blocked items, and completeness
- avoid decorative charts
- always connect numbers to operational meaning
