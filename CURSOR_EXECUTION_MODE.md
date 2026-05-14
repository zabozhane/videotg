# Cursor Execution Mode

## Purpose
This file defines how Cursor should implement the project using pre-generated context artifacts.
Do not regenerate architecture/spec from scratch. Use existing artifacts as source of truth.

## Source of Truth (Read First)
1. `.ai/project_spec.json`
2. `.ai/architecture.json`
3. `.ai/tasks.json`
4. `.ai/skills.json`
5. `.ai/workflow.json` (if present)

## Supporting Context
- `README.md`
- `ARCHITECTURE.md`
- `TASKS.md`
- `SKILLS.md`
- `CURSOR_CONTEXT.md`
- `WORKFLOW_REPORT.md` (if present)

## Required Working Mode
1. Work on one task at a time from `TASKS.md`.
2. Pick the highest-priority unfinished task unless user explicitly selects another.
3. Before coding, provide:
   - short plan (3-6 steps),
   - Definition of Done for this task,
   - exact test/check commands.
4. Implement only the current task scope.
5. Run/describe verification for this task.
6. Stop and wait for user feedback after each task.
7. Move to the next task only after the current task is accepted.

## Scope Guardrails
- Do not perform large refactors unless explicitly requested.
- Do not change unrelated files.
- Do not introduce architecture that contradicts `ARCHITECTURE.md`.
- Do not add overengineered patterns (agents/event bus/RAG/microservices) unless explicitly requested.

## Artifact Update Policy (Required)
A task is not complete until these artifacts are updated:
1. `TASKS.md`
   - Mark current task as done.
   - Add a short completion note and what was tested.
   - Mark next task as in progress (or keep pending if user prefers).
2. `SESSION_HANDOFF.md` (create if missing)
   - What was completed in this iteration.
   - Test result summary.
   - Known issues/risks.
   - Next task recommendation.

## Quality Gate Per Task
A task is complete only if:
- implementation matches task intent,
- tests/checks pass,
- edge cases for this task are reasonably handled,
- constraints from project spec are not violated,
- required artifacts are updated.

## Response Format (Every Iteration)
1. **Task**: current task id/title
2. **Plan**: short execution plan
3. **Changes**: what was implemented
4. **How To Test**: exact commands
5. **Result**: pass/fail and next action
6. **Artifact Updates**: what was updated in `TASKS.md` and `SESSION_HANDOFF.md`

## If Blocked
If required info is missing (API keys, unclear behavior, missing file paths, external service access), stop and ask one focused clarification question before proceeding.