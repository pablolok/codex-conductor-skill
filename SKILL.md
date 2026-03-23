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
- Use bundled scripts for deterministic support of setup analysis, guided-flow checkpoints, persisted conversation state, draft generation, track lifecycle updates, review/revert preparation, and skills installation.
- Default to the upstream file-resolution protocol from `GEMINI.md`: resolve project files through `conductor/index.md`, resolve track files through `conductor/tracks.md` and each track's `index.md`, and fall back to standard Conductor paths only when the linked file is missing.
- Treat `conductor/tracks.md` as the canonical Tracks Registry for compatibility.
- Treat `conductor/index.md` as the primary navigation index.
- When a repository already has `conductor/`, inspect it before writing anything and preserve official artifacts instead of reshaping them into a local-only format.
- Refuse full lifecycle operations on a legacy Codex-native workspace until it has been migrated to the canonical Gemini-compatible format.

## Interaction Bridge

- Gemini `ask_user` checkpoints map to `request_user_input` when Codex is already in Plan Mode.
- In Default mode, the same checkpoints map to concise inline questions and the command resumes after the user answers.
- Gemini `enter_plan_mode` and `exit_plan_mode` should be interpreted as workflow phases and confirmation boundaries, not as literal tool requirements.
- Gemini `/skills reload` pauses should be preserved as a Codex instruction-and-wait step before continuing.

## Commands

### `conductor:setup`

1. Read `AGENTS.md`, `README.md`, and repo shape.
2. Read `references/setup_protocol.md`, `references/brownfield_scan.md`, and `references/artifact_sync.md`.
3. Use `scripts/setup_workspace.py --repo <repo-root>` to audit existing artifacts, detect project maturity, determine resume state, and surface recommended skills.
4. Use `scripts/setup_flow.py --repo <repo-root>` to materialize the actual setup checkpoint sequence, draft payloads, approval payloads, styleguide-selection branches, and skills-install pause points.
5. Use `scripts/conversation_state.py init --repo <repo-root> --command setup` when the setup flow needs persisted revise/approve loop state across multiple user turns.
6. Use `scripts/flow_runtime.py --repo <repo-root> --command setup` to resume the exact next setup checkpoint after each user decision instead of re-deriving the loop manually.
7. Detect greenfield or brownfield maturity.
8. On brownfield, ask permission for a read-only scan before analyzing the project.
9. Infer as much product, guideline, stack, workflow, and styleguide context as possible from the repository.
10. Use `scripts/draft_setup_docs.py --repo <repo-root>` to generate starting drafts for shared context files when guided setup needs a first-pass document.
11. Use `scripts/apply_setup_drafts.py --repo <repo-root> --drafts-json <file>` to write the approved shared-context drafts immediately after approval, without regenerating different content.
12. Ask only for missing or preference-driven context, including track Git workflow policy and coverage target.
13. Capture and approve the workflow policy that should be written into or preserved in `conductor/workflow.md`.
   - branch policy: ask per track whether to create or use a dedicated branch
   - shared branch hygiene: unfinished tracks should not remain on `main` or another shared branch
   - commit policy: commit per phase
   - coverage target for the repository workflow
14. Produce a structured preview of the proposed live workspace artifacts and approved workflow decisions before writing files.
15. Require explicit user confirmation.
16. If an official-style workspace already exists, preserve its shared context files and only fill missing artifacts.
17. If a legacy Codex-native workspace is detected, stop and require migration before continuing.
18. Only after confirmation, run `scripts/bootstrap_conductor.py --repo <repo-root>` to materialize or repair the agreed canonical workspace, then apply the approved shared drafts with `scripts/apply_setup_drafts.py`.
19. Be ready to hand off into the first track flow when appropriate.

### `conductor:newTrack`

1. Ensure `conductor/` exists.
2. Read `references/track_lifecycle.md`.
3. Use `scripts/new_track_flow.py --repo <repo-root> --title "<title>"` to materialize the actual branch/spec/plan/skills checkpoints before writing the track.
4. Use `scripts/flow_runtime.py --repo <repo-root> --command newTrack --target "<title>"` to resume the exact next new-track checkpoint after each user decision.
5. Run `scripts/new_track.py --repo <repo-root> --title "<title>"` only after the spec and plan have been approved.
6. Ask whether to create or use a dedicated branch for that track, per the shared workflow policy.
7. Verify core context through the file-resolution protocol before creating track artifacts.
8. Use `scripts/draft_new_track.py --repo <repo-root> --track-id <track-id> --title "<title>"` to produce first-pass `spec.md` and `plan.md` drafts before interactive refinement.
9. Continue by refining the generated `spec.md` and `plan.md`.
10. After spec and plan approval, use `scripts/apply_new_track_drafts.py --repo <repo-root> --title "<title>" --spec-file <file> --plan-file <file>` when the approved drafts must be written exactly as reviewed.
11. Keep `plan.md` compatible with upstream Conductor expectations: phases as main headings, `[ ]`, `[~]`, `[x]` task markers, and room for task SHA and phase checkpoint annotations.
12. Use `scripts/skills_catalog.py` and `scripts/install_skills.py` when the track flow recommends skill installation.
13. Do not leave unfinished track artifacts on `main` or another shared branch; if the branch choice is wrong, stop and correct it before continuing.

### `conductor:status`

Run `scripts/status_tracks.py --repo <repo-root>` and summarize the result.

### `conductor:archive`

Run `scripts/archive_tracks.py --repo <repo-root>` and ensure archived tracks are physically moved from `conductor/tracks/` to `conductor/archive/`.

### `conductor:implement`, `conductor:review`, `conductor:revert`

These remain agent-driven workflow commands backed by deterministic helper scripts.

- For `implement`, use `scripts/implement_flow.py --repo <repo-root>` first to materialize the active track, task context, workflow checkpoints, and phase status before mutating the plan.
- For `implement`, interpret the repository's existing `conductor/workflow.md` through the deterministic workflow policy parser instead of ad hoc string guesses whenever runtime branching depends on workflow rules.
- For `implement`, use the `track_prompt`, `track_confirmation`, and `cleanup_options` payloads from `scripts/implement_flow.py` to preserve Gemini-style track selection and post-completion cleanup branching.
- For `implement`, use `scripts/implement_runtime.py --repo <repo-root> --track <track-id> --action <start|complete_task|commit_task|checkpoint_phase|doc_sync_execute>` to advance the runtime state through track start, task progression, task-commit choreography, phase-checkpoint verification, doc-sync application, completion, and cleanup handoff.
- For `implement`, pass `--verify-message` to the `commit_task` runtime action when workflow verification evidence should be committed and the resulting verification commit should become the phase checkpoint SHA.
- For `implement`, use `scripts/implement_track.py --repo <repo-root>` to support track selection, registry transitions, task start/completion markers, and track completion transitions.
- For `implement`, use `scripts/commit_task.py --repo <repo-root>` when the workflow requires the explicit Gemini-style code-commit then plan-commit sequence for a task.
- For `implement`, select tracks from `conductor/tracks.md`, resolve track files through the track index, and treat the repository's existing `conductor/workflow.md` as the source of truth for task lifecycle.
- For `implement`, preserve task markers, task SHA recording, and phase checkpoint annotations when present in `plan.md`.
- For `implement`, treat workflow verification and checkpoint behavior as authoritative for the track unless the user explicitly changes it.
- For `implement`, use `scripts/git_notes_helper.py --repo <repo-root> --sha <commit> --task "<task>" --summary "<summary>"` when the workflow calls for task or checkpoint notes.
- For `implement`, use `scripts/sync_project_docs.py --repo <repo-root> --track <track-id>` when the completed track requires project-document synchronization.
- For `implement`, use the `approval_questions` payload from `scripts/sync_project_docs.py` to present the proposed document diffs and require explicit approval before applying them.
- For `review`, use `scripts/review_runtime.py --repo <repo-root> --track <track-id> --action start` to drive the guided review sequence through scope confirmation, large-review branching, test execution, decision handling, and cleanup handoff as one runtime loop.
- For `review`, use `scripts/review_runtime.py --repo <repo-root> --track <track-id> --action complete` to preserve the Gemini-style "commit review changes first, then cleanup" branch before archiving, deleting, or skipping cleanup.
- For `review`, use `scripts/review_runtime.py --repo <repo-root> --track <track-id> --action cleanup_execute --cleanup-action <archive|delete|skip>` to execute the post-review cleanup branch, including delete confirmation and cleanup commits.
- For `review`, use `scripts/review_runtime.py --repo <repo-root> --action commit_changes_execute` to execute the non-track "commit review changes" branch after the user approves it.
- For `review`, use `scripts/review_flow.py --repo <repo-root> --run-tests` when the flow payload itself needs to be inspected directly, then use `scripts/review_track.py --repo <repo-root>` to prepare scaffolding and update `review.md` with findings, risks, gaps, and decision.
- For `review`, use the `diff_strategy`, `large_review_confirmation`, `test_command`, and `decision_question` payloads from `scripts/review_flow.py` to preserve the Gemini-style review branches.
- For `review`, use `scripts/review_runtime.py --repo <repo-root> --track <track-id> --action apply_fixes` to prepare the review-fix branch, then `scripts/commit_review_fixes.py --repo <repo-root>` when review fixes were applied and the workflow requires the review-fix task plus plan-update commit sequence.
- For `revert`, use `scripts/revert_flow.py --repo <repo-root>` first to materialize candidates, target scope, and rollback checkpoints, then use `scripts/revert_track.py --repo <repo-root>` to enumerate implementation commits, associated plan-update commits, and whole-track registry-creation commits before executing the rollback.
- For `revert`, use the `selection_menu`, `target_confirmation`, and `plan_confirmation` payloads from `scripts/revert_flow.py` to preserve the Gemini-style guided selection and final go/no-go confirmation.
- For `revert`, use `scripts/revert_runtime.py --repo <repo-root> --action <start|prepare|execute>` to drive the guided selection, plan confirmation, execution, and repair handoff as one runtime sequence.
- For `revert`, use `scripts/execute_revert.py --repo <repo-root>` to execute the drafted revert order and optionally repair logical track state after successful rollback.
- After `review` or `revert`, use `scripts/repair_track_state.py --repo <repo-root> --track <track-id> --status <new|in_progress|completed>` to realign `metadata.json`, `tracks.md`, and indexes when the logical track state changed.
- For cleanup after `implement` or `review`, use `scripts/cleanup_track.py --repo <repo-root> --track <track-id> --action <archive|delete|skip>`.
- Before cleanup after `implement` or `review`, use `scripts/cleanup_flow.py --repo <repo-root> --track <track-id>` to materialize the user choice set and guardrails.

### Skills Catalog

- Use `skills/catalog.md` as the local mirror of the upstream Conductor skills catalog.
- Use `scripts/skills_catalog.py` to load and score recommendations from repository context, `conductor/tech-stack.md`, `spec.md`, and `plan.md`.
- Preserve the upstream choice points: install all, hand-pick, or skip.
- Use `scripts/install_skills.py --repo <repo-root> --catalog skills/catalog.md --skills <skill>...` to install selected skills into workspace-local `.gemini/skills/` and refresh the corresponding `.codex/skills/` bridge wrappers.

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
