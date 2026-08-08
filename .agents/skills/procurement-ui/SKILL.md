---
name: procurement-ui
description: Generate enterprise-grade Arabic RTL interfaces for public procurement workflows, institutional procedures, controlled documents, and role-based operational systems.
---

# Procurement UI

## Purpose

Use this skill when the request is related to:
- public procurement
- tenders and consultations
- contracting authority workflows
- bidder submission flows
- procurement administration panels
- regulated document workflows
- procedural operations interfaces
- Arabic RTL institutional applications

This skill is specialized for enterprise-grade procurement interfaces with procedural sensitivity, multi-role visibility, and operational realism.

## Design Position

The UI must feel:
- institutional
- serious
- premium but restrained
- dense but readable
- operational, not decorative
- realistic, not conceptual
- secure by design
- suitable for government or large-organization use

Avoid:
- startup landing-page aesthetics
- playful SaaS patterns
- decorative gradients
- generic feature-card layouts
- consumer-app interactions
- random analytics widgets with no operational purpose

## Core Rules

Always prioritize:
1. task clarity
2. procedural sequence
3. role-based visibility
4. clear state representation
5. auditability
6. safe actions
7. Arabic RTL correctness

Do not design screens as generic CRUD pages.
Procurement interfaces are stage-based and role-constrained.

## Workflow Classification

When active, first classify the request into one of these:
- tender creation
- tender listing
- tender detail
- bidder submission
- procurement document review
- approval workflow
- restricted workflow
- audit/review workflow
- administrative configuration
- central oversight dashboard

Then determine:
- main user
- key task
- data sensitivity level
- restricted vs unrestricted information
- next allowed action
- required history/logging

## Information Hierarchy

Default hierarchy for procurement screens:

1. page identity
2. procedure status
3. allowed action
4. key record data
5. documents and related items
6. notes / warnings / constraints
7. audit trail / activity

If the screen is sensitive, push:
- status
- access conditions
- restrictions
- action safety
above all other content.

## Table Rules

For procurement tables:
- show identifiers first
- show stage/state clearly
- show deadlines and timestamps
- use meaningful status badges with text
- show the responsible party where relevant
- hide sensitive fields until authorized
- provide row-level contextual actions only when safe
- avoid exposing files before state conditions are met

Prefer columns such as:
- number/reference
- title
- authority/unit
- stage
- deadline
- submission count
- assigned reviewers/committee
- data completeness
- next action

## Forms and Actions

For forms:
- keep required fields explicit
- group inputs by meaning
- support draft/save where useful
- show validation messages in Arabic
- never overload one form with unnecessary secondary fields

For actions:
- one primary action per state
- secondary actions must not compete
- destructive or procedural actions require confirmation
- disabled actions must explain why
- do not show actions the user cannot perform unless the explanation is useful

## Arabic RTL Rules

Always output Arabic UI copy in Modern Standard Arabic.

Preferred wording:
- واضح
- مهني
- مؤسسي
- غير مبالغ فيه
- غير غامض

Examples:
- "إنشاء صفقة"
- "نشر الإجراء"
- "رفع الوثائق"
- "بانتظار الاستكمال"
- "غير متاح بسبب نقص الصلاحية"
- "تم تسجيل العملية"

Avoid vague copy such as:
- "تم بنجاح" without context
- "إجراء"
- "إرسال" when a more precise verb exists

## States

Each procurement screen should define:
- default
- loading
- empty
- partial/incomplete
- warning
- blocked
- success
- error

Blocked states must explain:
- what is blocked
- why it is blocked
- what condition is missing
- what the next step is

## Reusable Components

Use these components by default when relevant:
- page header
- status banner
- procedure summary card
- assignment card
- deadline card
- records table
- document panel
- warning callout
- permission notice
- empty state
- loading skeleton
- audit timeline
- detail drawer
- confirmation modal

## Operational Realism

Do not generate perfect demo data only.
Include realistic states where useful:
- missing metadata
- pending review
- incomplete assignment
- expired deadline
- restricted documents
- blocked action
- outdated record
- partial validation failure

## Output Format

When responding, structure output as:
1. screen purpose
2. user and permissions
3. information hierarchy
4. screen sections
5. key components
6. states and edge cases
7. Arabic UI copy
8. UX risks
9. refinements

## Final Rule

The result must look like a real procurement system used by institutions,
not a generic AI-generated SaaS admin panel.
