---
name: conductor
description: Use when the user explicitly invokes `conductor:setup`, `conductor:newTrack`, `conductor:implement`, `conductor:status`, `conductor:review`, `conductor:revert`, or `conductor:archive`, or when they want a Google Conductor-style workflow in a repository. This skill operates as a Gemini-first Conductor client for existing `conductor/` workspaces and keeps template libraries inside the skill.
metadata:
  short-description: Run a Gemini-first Conductor workflow
---

# Conductor

Use this skill only for explicit Conductor workflow requests.

## Core behavior

- Treat `AGENTS.md` as repository-wide rules.
- Treat repo-local `conductor/` as the canonical workflow state for structured work.
- Mirror the official Gemini Conductor prompts and artifact contract as closely as possible.
- Treat `conductor:setup` as a conversational context-building workflow, not as a bootstrap shortcut.
- Use bundled scripts only for deterministic preview, materialization, migration, and synchronization after confirmation.
- Default to the upstream file-resolution protocol from `GEMINI.md`: resolve project files through `conductor/index.md`, resolve track files through `conductor/tracks.md` and each track's `index.md`, and fall back to standard Conductor paths only when the linked file is missing.
- Treat `conductor/tracks.md` as the canonical Tracks Registry for compatibility.
- Treat `conductor/index.md` as the primary navigation index.
- When a repository already has `conductor/`, inspect it before writing anything and preserve official artifacts instead of reshaping them into a local-only format.
- Refuse full lifecycle operations on a legacy Codex-native workspace until it has been migrated to the canonical Gemini-compatible format.

## Commands

### `conductor:setup`

1. Read `AGENTS.md`, `README.md`, and repo shape.
2. Read `references/setup_protocol.md`, `references/brownfield_scan.md`, and `references/artifact_sync.md`.
3. Audit existing `conductor/` artifacts and determine whether setup should resume or start fresh.
4. Detect greenfield or brownfield maturity.
5. On brownfield, ask permission for a read-only scan before analyzing the project.
6. Infer as much product, guideline, stack, workflow, and styleguide context as possible from the repository.
7. Ask only for missing or preference-driven context, including track Git workflow policy and coverage target.
8. Capture and approve the workflow policy that should be written into or preserved in `conductor/workflow.md`.
   - branch policy: ask per track whether to create or use a dedicated branch
   - shared branch hygiene: unfinished tracks should not remain on `main` or another shared branch
   - commit policy: commit per phase
   - coverage target for the repository workflow
9. Produce a structured preview of the proposed live workspace artifacts and approved workflow decisions before writing files.
10. Require explicit user confirmation.
11. If an official-style workspace already exists, preserve its shared context files and only fill missing artifacts.
12. If a legacy Codex-native workspace is detected, stop and require migration before continuing.
13. Only after confirmation, run `scripts/bootstrap_conductor.py --repo <repo-root>` to materialize or repair the agreed canonical workspace.
14. Be ready to hand off into the first track flow when appropriate.

### `conductor:newTrack`

1. Ensure `conductor/` exists.
2. Read `references/track_lifecycle.md`.
3. Run `scripts/new_track.py --repo <repo-root> --title "<title>"`.
4. Ask whether to create or use a dedicated branch for that track, per the shared workflow policy.
5. Verify core context through the file-resolution protocol before creating track artifacts.
6. Continue by refining the generated `spec.md` and `plan.md`.
7. Keep `plan.md` compatible with upstream Conductor expectations: phases as main headings, `[ ]`, `[~]`, `[x]` task markers, and room for task SHA and phase checkpoint annotations.
8. Do not leave unfinished track artifacts on `main` or another shared branch; if the branch choice is wrong, stop and correct it before continuing.

### `conductor:status`

Run `scripts/status_tracks.py --repo <repo-root>` and summarize the result.

### `conductor:archive`

Run `scripts/archive_tracks.py --repo <repo-root>` and ensure archived tracks are physically moved from `conductor/tracks/` to `conductor/archive/`.

### `conductor:implement`, `conductor:review`, `conductor:revert`

These remain agent-driven workflow commands.

- For `implement`, select tracks from `conductor/tracks.md`, resolve track files through the track index, and treat the repository's existing `conductor/workflow.md` as the source of truth for task lifecycle.
- For `implement`, preserve task markers, task SHA recording, and phase checkpoint annotations when present in `plan.md`.
- For `implement`, treat workflow verification and checkpoint behavior as authoritative for the track unless the user explicitly changes it.
- For `review`, update `review.md` with findings, risks, gaps, and decision.
- For `revert`, scope the rollback to track, phase, or task/sub-task, reconcile plan history against git commits, and realign registry and track files after the revert.

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

## Canonical Track Contract

- Track directories live at `conductor/tracks/<track_id>/`.
- Track identifiers should follow the upstream short-name plus date shape, for example `user-auth_20260323`.
- `metadata.json` must use canonical keys including `track_id`, `type`, `status`, `created_at`, `updated_at`, and `description`.
- `conductor/tracks.md` must store track entries and links in upstream registry form instead of a metadata-only summary table.

## Migration

- Use `scripts/migrate_workspace.py --repo <repo-root>` to migrate an older Codex-native workspace into the canonical Gemini-compatible format.
- Migration must preserve track content while rewriting track folder names, metadata keys, `tracks.md`, and generated indexes.
