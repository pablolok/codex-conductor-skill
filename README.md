# Codex Conductor Skill

This folder is a standalone Codex skill package for a Gemini-first Google Conductor workflow.

It is structured so it can be moved into its own repository without depending on this finance dashboard repository.

## Contents

- `SKILL.md`
- `agents/openai.yaml`
- `references/`
- `scripts/`
- `skills/catalog.md`
- `assets/repo_templates/`
- `assets/styleguides/`

Key helper scripts now include:

- `scripts/setup_workspace.py`
- `scripts/setup_flow.py`
- `scripts/flow_runtime.py`
- `scripts/conversation_state.py`
- `scripts/draft_setup_docs.py`
- `scripts/apply_setup_drafts.py`
- `scripts/new_track.py`
- `scripts/new_track_flow.py`
- `scripts/draft_new_track.py`
- `scripts/apply_new_track_drafts.py`
- `scripts/implement_flow.py`
- `scripts/implement_runtime.py`
- `scripts/implement_track.py`
- `scripts/commit_task.py`
- `scripts/git_notes_helper.py`
- `scripts/review_flow.py`
- `scripts/review_runtime.py`
- `scripts/review_track.py`
- `scripts/commit_review_fixes.py`
- `scripts/revert_flow.py`
- `scripts/revert_runtime.py`
- `scripts/revert_track.py`
- `scripts/execute_revert.py`
- `scripts/repair_track_state.py`
- `scripts/cleanup_flow.py`
- `scripts/install_skills.py`
- `scripts/sync_project_docs.py`
- `scripts/cleanup_track.py`
- `scripts/status_tracks.py`
- `scripts/archive_tracks.py`
- `scripts/migrate_workspace.py`

## Install

Copy this folder so that the final path becomes:

`~/.codex/skills/conductor`

On Windows, that usually means:

`C:\Users\<your-user>\.codex\skills\conductor`

## Use

This skill is meant for explicit workflow triggers:

- `conductor:setup`
- `conductor:newTrack`
- `conductor:implement`
- `conductor:status`
- `conductor:review`
- `conductor:revert`
- `conductor:archive`

## About `conductor:setup`

`conductor:setup` is conversational-first and prompt-first.

It should:

- detect whether the target repository is greenfield or brownfield
- request permission for a read-only scan on brownfield repositories
- analyze the target repository
- gather or refresh only the missing shared context through guided questions
- define the shared Git workflow for tracks
- ask for and record the repository coverage target
- show a preview of the proposed live workspace artifacts and decisions
- require explicit confirmation
- only then materialize the repo-local `conductor/` files

The shared Git workflow currently encoded by the skill is:

- ask per track whether to create or use a dedicated branch
- keep unfinished tracks off `main` and other shared branches
- use the workflow recorded in `workflow.md`

The shared quality workflow currently encoded by the skill is:

- ask for the repository coverage target during setup
- in this repository, the approved target is 100%

For existing repositories, the skill treats an upstream-style `conductor/` workspace as canonical and should take over from the workspace already on disk instead of replacing it with a local-only format.

## Plan Format

Track plans are expected to use a hybrid format:

- phases remain the main execution checkpoints
- each phase contains numbered steps
- each step is tracked with `[ ]`, `[~]`, `[x]`

## Materialization Script

The bootstrap script supports the final materialization step:

```powershell
python scripts/bootstrap_conductor.py --repo <repo-root>
```

## Migration

Older Codex-native conductor workspaces are no longer treated as fully supported runtime state. Migrate them first:

```powershell
python scripts/migrate_workspace.py --repo <repo-root>
```

The migration rewrites the local custom workspace into the canonical Gemini-compatible format while preserving `spec.md`, `plan.md`, `review.md`, and `verify.md`.

Preview support:

```powershell
python scripts/bootstrap_conductor.py --repo <repo-root> --preview
```

Setup analysis support:

```powershell
python scripts/setup_workspace.py --repo <repo-root>
```

Setup checkpoint flow support:

```powershell
python scripts/setup_flow.py --repo <repo-root>
```

Persisted conversation-state support:

```powershell
python scripts/conversation_state.py init --repo <repo-root> --command setup
```

Advance or resume the exact next guided checkpoint:

```powershell
python scripts/flow_runtime.py --repo <repo-root> --command setup
python scripts/flow_runtime.py --repo <repo-root> --command setup --session <session.json> --decision "Approve"
```

Apply approved setup drafts immediately:

```powershell
python scripts/apply_setup_drafts.py --repo <repo-root> --drafts-json <approved-drafts.json>
```

New-track checkpoint flow support:

```powershell
python scripts/new_track_flow.py --repo <repo-root> --title "Implement user authentication"
```

Resume the guided new-track loop after each user decision:

```powershell
python scripts/flow_runtime.py --repo <repo-root> --command newTrack --target "Implement user authentication"
python scripts/flow_runtime.py --repo <repo-root> --command newTrack --target "Implement user authentication" --session <session.json> --decision "Approve"
```

Apply approved track drafts immediately:

```powershell
python scripts/apply_new_track_drafts.py --repo <repo-root> --title "Implement user authentication" --spec-file <approved-spec.md> --plan-file <approved-plan.md>
```

Implement/review/revert checkpoint flow support:

```powershell
python scripts/implement_flow.py --repo <repo-root>
python scripts/implement_runtime.py --repo <repo-root> --track <track-id> --action start
python scripts/implement_runtime.py --repo <repo-root> --track <track-id> --action complete_task --sha <short-sha>
python scripts/implement_runtime.py --repo <repo-root> --track <track-id> --action commit_task --code-message "feat: ..." --plan-message "conductor(plan): Mark task complete" --paths <file>...
python scripts/implement_runtime.py --repo <repo-root> --track <track-id> --action commit_task --code-message "feat: ..." --plan-message "conductor(plan): Mark task complete" --verify-message "test(conductor): Record phase verification" --paths <file>...
python scripts/implement_runtime.py --repo <repo-root> --track <track-id> --action checkpoint_phase --sha <short-sha>
python scripts/commit_task.py --repo <repo-root> --code-message "feat: ..." --plan-message "conductor(plan): Mark task complete"
python scripts/review_flow.py --repo <repo-root> --run-tests
python scripts/review_runtime.py --repo <repo-root> --track <track-id> --action start
python scripts/review_runtime.py --repo <repo-root> --track <track-id> --action apply_fixes
python scripts/review_runtime.py --repo <repo-root> --track <track-id> --action complete
python scripts/review_runtime.py --repo <repo-root> --action commit_changes_execute
python scripts/review_runtime.py --repo <repo-root> --track <track-id> --action cleanup_execute --cleanup-action archive
python scripts/review_runtime.py --repo <repo-root> --track <track-id> --action cleanup_execute --cleanup-action delete --confirmed
python scripts/commit_review_fixes.py --repo <repo-root> --message "fix(conductor): Apply review suggestions"
python scripts/revert_flow.py --repo <repo-root> --candidates
python scripts/revert_runtime.py --repo <repo-root> --action start
python scripts/revert_runtime.py --repo <repo-root> --track <track-id> --task "<task>" --action prepare
python scripts/revert_runtime.py --repo <repo-root> --track <track-id> --task "<task>" --action execute
python scripts/execute_revert.py --repo <repo-root> --repair-state
python scripts/cleanup_flow.py --repo <repo-root>
python scripts/repair_track_state.py --repo <repo-root> --track <track-id> --status in_progress
```

Skills install support:

```powershell
python scripts/install_skills.py --repo <repo-root> --catalog skills/catalog.md --skills <skill-name>
```

This installs the canonical Gemini skill payload into `.gemini/skills/<skill-name>/` and writes the matching Codex bridge entry into `.codex/skills/<skill-name>/SKILL.md`.

## Publish As Its Own Repo

If you want to publish this as a separate repository:

1. Copy `conductor-skill/` out of this repo.
2. Initialize a new git repository in that copied folder.
3. Keep the folder name as `conductor` or rename it on install so Codex resolves it as the `conductor` skill.

## Notes

- The skill is self-contained.
- Template and styleguide libraries stay inside the skill.
- `skills/catalog.md` mirrors the upstream Conductor skills-catalog contract for recommendation parity.
- The target repository should receive only live `conductor/` artifacts, not repo-local template scaffolds.
- The target repository still provides its own `AGENTS.md` and project-specific context.
- The bootstrap script is not the full meaning of `conductor:setup`; it only materializes the agreed context.
- Existing official Conductor files are preserved whenever possible.
