---
name: conductor
description: Use when the user explicitly invokes `conductor:setup`, `conductor:newTrack`, `conductor:implement`, `conductor:status`, `conductor:review`, `conductor:revert`, or `conductor:archive`, or when they want a Google Conductor-style workflow in a repository. This skill mirrors the official Conductor command prompts, generates only live repo artifacts, and keeps template libraries inside the skill.
metadata:
  short-description: Run an official-style Conductor workflow
---

# Conductor

Use this skill only for explicit Conductor workflow requests.

## Core behavior

- Treat `AGENTS.md` as repository-wide rules.
- Treat repo-local `conductor/` as generated workflow state.
- Mirror the official Conductor command prompts as closely as possible.
- Treat `conductor:setup` as a conversational context-building workflow, not as a bootstrap shortcut.
- Use bundled scripts only for deterministic preview, materialization, and index synchronization after confirmation.
- Treat `conductor/index.md` as the primary workspace index, with `tracks.md` as a compact summary view.
- Treat the track Git workflow policy as part of the shared setup context.

## Commands

### `conductor:setup`

1. Read `AGENTS.md`, `README.md`, and repo shape.
2. Read `references/setup_protocol.md`, `references/brownfield_scan.md`, and `references/artifact_sync.md`.
3. Audit existing `conductor/` artifacts and determine whether setup should resume or start fresh.
4. Detect greenfield or brownfield maturity.
5. On brownfield, ask permission for a read-only scan before analyzing the project.
6. Infer as much product, guideline, stack, workflow, and styleguide context as possible from the repository.
7. Ask only for missing or preference-driven context, including track Git workflow policy and coverage target.
8. Capture and approve:
   - branch policy: dedicated branch required for every track; create or switch to that branch before track artifacts are generated
   - commit policy: commit per phase
   - coverage target for the repository workflow
9. Produce a structured preview of the proposed live workspace artifacts and approved workflow decisions before writing files.
10. Require explicit user confirmation.
11. Only after confirmation, run `scripts/bootstrap_conductor.py --repo <repo-root>` to materialize the agreed context.
12. Be ready to hand off into the first track flow when appropriate.

### `conductor:newTrack`

1. Ensure `conductor/` exists.
2. Read `references/track_lifecycle.md`.
3. Determine the dedicated branch for the track and create or switch to it before generating any track artifacts.
4. Do not leave unfinished track artifacts on `main` or another shared branch; if the current branch is wrong, stop and correct the branch first.
5. Run `scripts/new_track.py --repo <repo-root> --title "<title>"`.
6. Continue by refining the generated `spec.md` and `plan.md`.
7. Keep `plan.md` in the hybrid format: phases as workflow checkpoints, numbered steps inside each phase, and `[ ]`, `[~]`, `[x]` markers on each step.

### `conductor:status`

Run `scripts/status_tracks.py --repo <repo-root>` and summarize the result.

### `conductor:archive`

Run `scripts/archive_tracks.py --repo <repo-root>` and ensure archived tracks are physically moved from `conductor/tracks/` to `conductor/archive/`.

### `conductor:implement`, `conductor:review`, `conductor:revert`

These remain agent-driven workflow commands.

- For `implement`, use the active track's `plan.md` and update `[ ]`, `[~]`, `[x]`, `metadata.json`, `index.md`, `tracks.md`, and `verify.md`.
- For `implement`, keep the plan organized as phases with numbered steps rather than flat task bullets.
- For `implement`, treat a phase checkpoint as the standard commit boundary for the track unless the approved workflow explicitly differs.
- For `implement`, keep verification aligned with the approved repository coverage target.
- For `review`, update `review.md` with findings, risks, gaps, and decision.
- For `revert`, scope the rollback to track, phase, or task/sub-task and realign all track files and indexes.

Read `references/track_lifecycle.md`, `references/review_revert_archive.md`, and `references/artifact_sync.md` when handling these commands.

## Files to keep aligned

- `conductor/index.md`
- `conductor/tracks.md`
- `conductor/tracks/<track-id>/index.md`
- `conductor/tracks/<track-id>/metadata.json`
- `conductor/tracks/<track-id>/spec.md`
- `conductor/tracks/<track-id>/plan.md`
- `conductor/tracks/<track-id>/review.md`
- `conductor/tracks/<track-id>/verify.md`
