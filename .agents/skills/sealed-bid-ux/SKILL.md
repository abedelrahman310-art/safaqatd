---
name: sealed-bid-ux
description: Design and refine Arabic RTL UX for sealed bid workflows, bid opening committees, restricted access flows, opening records, and audit-heavy tender procedures.
---

# Sealed Bid UX

## Purpose

Use this skill when the request includes:
- sealed bids
- closed bid submissions
- bid opening
- opening committees
- opening records
- restricted tender visibility
- bid access control
- committee approval flows
- procedural opening screens
- audit-heavy procurement stages

This skill is only for high-sensitivity workflows where information must remain hidden until explicit procedural conditions are met.

## Core Principle

Design for:
- no premature exposure
- committee-driven action
- condition-based visibility
- safe procedural confirmation
- traceable opening events
- institutional confidence
- minimal user confusion

Opening bids is not a normal "view details" action.
It is a formal workflow event.

## Mandatory UX Rules

Always enforce these interface assumptions:

1. sensitive bid content stays hidden before valid opening
2. financial content must never appear before opening conditions are met
3. the UI must clearly show:
   - closed
   - not yet eligible
   - ready for opening
   - awaiting approval
   - opening in progress
   - opened
   - blocked
   - failed
4. one primary action per state only
5. blocked states must explain why
6. every opening action must appear loggable and consequential
7. audit trail must be visible and meaningful
8. permission context must be explicit
9. opening success must feel official, not celebratory
10. no consumer-style UX patterns

## Opening Conditions Model

When this skill is active, assume that bid opening depends on conditions such as:
- submission deadline passed
- correct tender state
- authorized committee member
- quorum or approval rule satisfied
- opening event logged
- record generated or ready to generate

The UI must visually express these conditions before enabling any action.

## Screen Types

This skill should generate or review these screens:
- sealed bids list
- opening detail
- permission/eligibility screen
- opening confirmation modal
- dual approval waiting state
- opening success state
- blocked/error state
- opening record
- audit timeline
- printable opening report

## Screen Hierarchy

For opening-related screens, default hierarchy is:

1. tender identity
2. opening state
3. eligibility/permission banner
4. primary procedural action
5. sealed bid list
6. committee card
7. warnings and constraints
8. audit trail
9. secondary actions

Audit trail should never be buried if the workflow is high-risk.

## Sealed Bid Table Rules

Before opening:
- show only permitted metadata
- show submission timestamp if allowed
- show validation state if allowed
- hide financial details
- hide downloadable sensitive content
- mask or omit fields not yet allowed

After opening:
- reveal only the fields permitted by the procedure stage
- keep evaluation information separate from opening information
- do not collapse opening and evaluation into one cluttered table

## Committee UX Rules

When a committee is involved:
- show assigned members
- show current user’s role
- show quorum or approval status
- show what is still required
- explain why the action is blocked if quorum is missing
- if multi-approval is required, show progress explicitly

Preferred components:
- committee status card
- approval tracker
- waiting state panel
- restricted action banner

## Confirmation UX

High-risk actions require proportional confirmation.

Opening confirmation should include:
- tender identifier
- number of bids to open
- acting user
- current timestamp
- warning that the action is recorded
- explicit confirm CTA

If dual approval exists:
- show first approver
- show waiting status
- do not reveal bid content while waiting

## Audit Trail Rules

Always include an audit/activity timeline for opening workflows.

Important events:
- deadline reached
- early opening denied
- committee member viewed opening screen
- approval granted
- approval pending
- opening executed
- record generated
- export/download
- decryption issue
- missing file
- repeated attempt blocked

Each event should show:
- actor
- action
- timestamp
- status
- expandable detail when needed

## Arabic UI Copy Style

Use precise Arabic suitable for regulated workflows.

Preferred phrases:
- "العروض ما تزال مغلقة"
- "غير متاح قبل انتهاء أجل الإيداع"
- "لا تملك الصلاحية لفتح العروض"
- "بانتظار موافقة عضو آخر من اللجنة"
- "تم تنفيذ عملية الفتح وتسجيلها في سجل التدقيق"
- "تعذر إتمام الفتح بسبب نقص شرط إجرائي"
- "تم إنشاء محضر فتح العروض"

Avoid:
- casual language
- celebratory language
- vague messages
- technical raw errors exposed to end users

## Edge Cases

Always consider:
- deadline not reached
- wrong tender state
- no bids submitted
- no committee assigned
- user not in committee
- approval missing
- decryption failure
- corrupted file
- duplicate opening attempt
- network interruption
- record generation failure

## Output Format

Structure output as:
1. workflow purpose
2. user roles and visibility
3. screen-by-screen UX
4. wireframe description
5. key components
6. Arabic UI text
7. blocked/error states
8. audit trail model
9. UX issues and improvements

## Final Rule

Treat sealed bid opening as a formal procedural workflow.
Never design it like a standard document list or admin detail page.
