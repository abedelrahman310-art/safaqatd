---
name: gov-dashboard-ui
description: Generate Arabic RTL executive and operational dashboards for government and institutional platforms with strong hierarchy, auditability, data density, and decision clarity.
---

# Government Dashboard UI

## Purpose

Use this skill when the request is about:
- executive dashboards
- operational dashboards
- central administration panels
- oversight interfaces
- compliance and monitoring dashboards
- audit and activity visibility
- KPI-based institutional screens
- role-based reporting interfaces
- data-heavy Arabic RTL administrative systems

This skill is designed for government and institutional environments,
not startup analytics dashboards.

## Dashboard Philosophy

A government dashboard is not a Dribbble chart board.
It exists to:
- clarify status
- show priorities
- surface exceptions
- support oversight
- make action possible
- preserve trust in the numbers

The dashboard should feel:
- authoritative
- calm
- dense but readable
- evidence-based
- review-friendly
- suitable for managers, auditors, and operators

## Default Hierarchy

Organize dashboards in this order:

1. context (period, unit, filters, scope)
2. high-level status and KPIs
3. exceptions, risks, and alerts
4. trend or comparison views
5. operational detail table
6. recent activity / audit / notes

Do not put decorative charts ahead of action-oriented information.

## KPI Rules

Use KPIs only when they answer real operational questions.
Each KPI should have:
- label
- current value
- scope or period
- trend if available
- meaning
- optional drill-down path

Avoid meaningless KPIs.
Do not add a metric just to fill space.

Preferred KPI types:
- total procedures
- active procedures
- delayed procedures
- completion rate
- data completeness
- value totals
- open alerts
- pending approvals
- units with issues

## Alert and Exception Design

Dashboards must prominently surface:
- delays
- blocked items
- incomplete data
- policy risks
- unusual changes
- missing approvals
- stale records

Alerts should be:
- prioritized
- readable
- filterable
- actionable

Use text + icon + severity badge.
Never rely on color only.

## Table and Detail Rules

Operational tables should:
- support sorting and filtering
- prioritize the identifier and current status
- show deadlines and ownership
- provide safe next actions
- support dense viewing without clutter
- allow drill-down into detail

If there is a side panel or drawer, use it for:
- activity
- notes
- details
- quick summary
- audit slices

## Visual Direction

Use:
- neutral or dark institutional palette
- compact cards
- strong text contrast
- restrained accent colors
- clean separators
- soft surfaces
- consistent grid
- minimal decoration

Avoid:
- startup KPI rainbow cards
- oversized charts
- overuse of glassmorphism
- playful microinteractions
- promotional styling

## Arabic RTL Rules

Always optimize for Arabic RTL first.

Use wording such as:
- "لوحة التحليل المركزي"
- "آخر تحديث"
- "نسبة الاكتمال"
- "الملفات المتأخرة"
- "الوحدات الأعلى تأخيرًا"
- "تنبيهات تحتاج إلى متابعة"
- "لا توجد بيانات مطابقة للمرشحات"

Prefer:
- concise institutional labels
- direct action labels
- precise state labels

## Required States

Every dashboard design should consider:
- default
- loading
- no data
- partial data
- stale data warning
- insufficient permissions
- error state
- filtered empty result

## Reusable Components

Preferred components:
- filter bar
- date range selector
- scope switcher
- KPI strip
- alert stack
- chart card
- comparison card
- ranked list
- activity rail
- detail drawer
- data table
- empty state
- stale-data banner
- export action

## Data Realism

Use realistic states:
- one unit lagging
- one KPI missing trend
- one chart with incomplete data note
- one table row with missing field
- one alert already acknowledged
- one stale section needing refresh

Do not make dashboards unrealistically clean.

## Output Format

Structure the response as:
1. dashboard goal
2. audience and roles
3. information hierarchy
4. sections
5. KPI logic
6. alerts and exceptions
7. table/detail behavior
8. Arabic UI copy
9. UX risks
10. refinements

## Final Rule

The dashboard must help people supervise, decide, and intervene.
If a visual element does not support that, remove it.
