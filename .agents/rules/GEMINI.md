You are working on "صفقات ذكية", an Arabic RTL enterprise procurement platform.

## Project Context

This project is a serious institutional system, not a generic SaaS starter.
It includes:
- procurement workflows
- sealed bid submission
- bid opening procedures
- committee-based actions
- audit-heavy records
- government and administrative dashboards
- restricted document access
- procedural status transitions

## Global Behavior Rules

Always optimize for:
- Arabic RTL
- institutional clarity
- role-based visibility
- action safety
- auditability
- operational realism
- reusable UI patterns
- high-quality enterprise structure

Do not optimize for:
- marketing aesthetics
- startup-style generic UI
- decorative complexity
- flashy animations
- random features outside scope

## Design Behavior

When generating or refining UI:
1. identify the real user
2. identify the workflow stage
3. determine what must be visible
4. determine what must remain hidden
5. clarify the next allowed action
6. surface restrictions clearly
7. include state handling
8. include audit/history where relevant

For sensitive screens:
- never expose sensitive content prematurely
- do not show inaccessible actions as active
- explain blocked states
- prioritize state and action over decoration

## Output Preferences

Prefer this structure in responses:
1. purpose
2. user/role
3. hierarchy
4. sections/components
5. states
6. Arabic UI text
7. UX risks
8. refinements

If asked for screen design:
- produce screen architecture first
- then component hierarchy
- then copy
- then improvements

If asked for implementation:
- preserve structure
- keep components reusable
- avoid unnecessary abstraction
- prefer clarity over cleverness

## UI Writing Rules

All UI copy should be:
- in Modern Standard Arabic
- formal
- direct
- precise
- institutional
- concise

Avoid vague messages like:
- "تم بنجاح"
- "تم التنفيذ"
without specifying what happened.

Prefer:
- "تم فتح العروض وتسجيل العملية"
- "لا تملك الصلاحية لتنفيذ هذا الإجراء"
- "غير متاح قبل انتهاء أجل الإيداع"
- "تعذر تحميل الملف بسبب فشل التحقق"

## Dashboard Rules

Dashboards must:
- foreground important KPIs only
- prioritize alerts and exceptions
- surface blocked items
- show timestamps and freshness
- connect every visual to a decision or action

Do not create decorative dashboards.

## Sensitive Workflow Rules

For bid opening and restricted workflows:
- show closed/open/blocked/awaiting approval states clearly
- use progressive disclosure
- keep one primary action per critical state
- make confirmation proportional to risk
- make audit trail visible and useful
- keep official records printable and structured

## Engineering-Oriented Rules

When helping with UI implementation:
- prefer modular architecture
- support RTL cleanly
- make state handling explicit
- include loading, empty, blocked, success, and error states
- keep component names meaningful
- avoid fake placeholders unless clearly marked
- do not generate inaccessible interactions

## Final Rule

Everything generated for this project should feel like a real institutional product used daily by operators, managers, committees, and auditors.

Not AI fluff.
Not demo polish only.
Real workflow, real constraints, real trust.
