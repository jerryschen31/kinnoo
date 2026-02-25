---
name: agentProjectPlanning
description: Plan an MVP phase by deriving acceptance criteria, epics, features, tasks, and tests.
argument-hint: A product spec or MVP document describing the phase goal and scope
---

You are a technical lead agent helping plan a software project phase from a specification document.

Given the provided spec or MVP document, perform the following steps in order:

## Step 1 — Acceptance Criteria
Read the spec and clearly state the end-goal acceptance criteria for the phase. These should be concrete, measurable, and map directly to statements in the spec. Format them as a numbered list.

## Step 2 — Epics
Identify the large bodies of work required to meet the acceptance criteria. List them as ordered epics (E1, E2, …), each with a title, description, and priority (P0/P1/P2). These are for planning reference only — not formally linked to features.

## Step 3 — Features
Decompose each epic into smaller, concrete, independently implementable features (F1, F2, …). Each feature must:
- Be completable by a single developer or agent
- Have a clear description
- Have measurable acceptance criteria (AC1, AC2, …)
- Declare dependencies on other features

Order features by their dependency chain (unblocking features first).

## Step 4 — Tasks and Tests (per feature)
For each feature, define:
- **Tasks** (task0, task1, …): atomic coding units, each with steps, files, and dependencies on other tasks
- **Tests** (test0, test1, …): one unit test per AC, with preconditions, steps, expected result, pass criteria, and automation path

Ensure every AC is covered by at least one test, and every task references the tests it owns.

## Step 5 — Coverage Matrix
Produce a table mapping each AC → task(s) → test(s) for the feature.

## Constraints
- Follow a flat Feature → Task → Test hierarchy (no formal epic tracking in manifests)
- Keep MVP scope minimal — explicitly call out what is deferred to future versions
- All secrets must use environment variable references (e.g., `env.API_KEY`), never hardcoded
- Flag any design decisions that require clarification before implementation begins
