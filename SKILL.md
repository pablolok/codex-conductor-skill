---
name: conductor
description: Use when the user explicitly invokes `conductor:setup`, `conductor:newTrack`, `conductor:implement`, `conductor:status`, `conductor:review`, `conductor:revert`, or `conductor:archive`, or when they want a Google Conductor-style workflow in a repository. This skill bootstraps and maintains a repo-local `conductor/` workspace from bundled templates and drives track-based execution against that workspace.
metadata:
  short-description: Bootstrap and run a Conductor workflow
---

# Conductor

Use this skill only for explicit Conductor workflow requests.

## Core behavior

- Treat `AGENTS.md` as repository-wide rules.
- Treat repo-local `conductor/` as generated workflow state.
- Treat `conductor:setup` as a conversational context-building workflow, not as a bootstrap shortcut.
- Use bundled scripts only for deterministic preview and file materialization after confirmation.
- Keep `tracks.md` as the portfolio index and `metadata.json` as per-track structured state.

## Commands

### `conductor:setup`

1. Read `AGENTS.md`, `README.md`, and repo shape.
2. Read `references/setup_protocol.md`.
3. Analyze the repository and infer as much stable context as possible.
4. Ask targeted setup questions covering product, audience, boundaries, workflow, stack, testing, and styleguide expectations.
5. Produce a structured preview of the proposed shared context before writing files.
6. Require explicit user confirmation.
7. Only after confirmation, run `scripts/bootstrap_conductor.py --repo <repo-root>` to materialize the agreed context.

Read `references/bootstrap.md` for the materialization contract and `references/setup_protocol.md` for the conversational setup contract.

### `conductor:newTrack`

1. Ensure `conductor/` exists.
2. Run `scripts/new_track.py --repo <repo-root> --title "<title>"`.
3. Continue by refining the generated `spec.md`.

### `conductor:status`

Run `scripts/status_tracks.py --repo <repo-root>` and summarize the result.

### `conductor:archive`

Run `scripts/archive_tracks.py --repo <repo-root>`.

### `conductor:implement`, `conductor:review`, `conductor:revert`

These remain agent-driven workflow commands.

- For `implement`, use the active track's `plan.md` and update `[ ]`, `[~]`, `[x]`, `metadata.json`, `tracks.md`, and `verify.md`.
- For `review`, update `review.md` with findings, risks, gaps, and decision.
- For `revert`, scope the rollback to track, phase, or task/sub-task and realign all track files and indexes.

Read `references/command_workflow.md` when handling these commands.

## Files to keep aligned

- `conductor/tracks.md`
- `conductor/tracks/<track-id>/metadata.json`
- `conductor/tracks/<track-id>/spec.md`
- `conductor/tracks/<track-id>/plan.md`
- `conductor/tracks/<track-id>/review.md`
- `conductor/tracks/<track-id>/verify.md`
