# Install Conductor Skill

This repository contains a standalone Codex skill named `conductor`.

## Install Path

Install it so the final local path is:

`~/.codex/skills/conductor`

On Windows:

`C:\Users\<your-user>\.codex\skills\conductor`

## Installation Steps

1. Clone or download this repository.
2. Copy the repository contents into your Codex skills directory under a folder named `conductor`.
3. Start a new Codex session.

Example on Windows PowerShell:

```powershell
Copy-Item -Recurse -Force .\ConductorSkillRepo C:\Users\<your-user>\.codex\skills\conductor
```

If the destination already exists and you want a clean reinstall:

```powershell
Remove-Item -Recurse -Force C:\Users\<your-user>\.codex\skills\conductor
Copy-Item -Recurse -Force .\ConductorSkillRepo C:\Users\<your-user>\.codex\skills\conductor
```

## Verify Installation

Check that these files exist:

- `SKILL.md`
- `agents/openai.yaml`
- `skills/catalog.md`
- `references/bootstrap.md`
- `references/setup_protocol.md`
- `references/brownfield_scan.md`
- `references/track_lifecycle.md`
- `references/review_revert_archive.md`
- `references/artifact_sync.md`
- `scripts/bootstrap_conductor.py`
- `scripts/setup_workspace.py`
- `scripts/setup_flow.py`
- `scripts/flow_runtime.py`
- `scripts/conversation_state.py`
- `scripts/draft_setup_docs.py`
- `scripts/apply_setup_drafts.py`
- `scripts/migrate_workspace.py`
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
- `scripts/review_track.py`
- `scripts/commit_review_fixes.py`
- `scripts/revert_flow.py`
- `scripts/revert_track.py`
- `scripts/execute_revert.py`
- `scripts/repair_track_state.py`
- `scripts/cleanup_flow.py`
- `scripts/install_skills.py`
- `scripts/sync_project_docs.py`
- `scripts/cleanup_track.py`
- `scripts/skills_catalog.py`
- `scripts/status_tracks.py`
- `scripts/archive_tracks.py`

## How `conductor:setup` Should Behave

`conductor:setup` is not just a bootstrap command.

It should:

1. detect whether the repository is greenfield or brownfield
2. request permission for a read-only scan on brownfield repositories
3. analyze the repository
4. gather or refresh only the missing shared context through guided questions
5. define the shared Git workflow for tracks
6. ask for and record the repository coverage target
7. show a preview of the proposed live workspace artifacts and workflow decisions
8. require explicit confirmation
9. only then materialize the repo-local `conductor/` workspace

The shared Git workflow encoded by the skill is:

- branch policy: ask per track whether to create or use a dedicated branch
- shared branch hygiene: unfinished tracks should not remain on `main` or another shared branch
- commit policy: commit per phase
Track plans are expected to use a hybrid format:

- phases remain the main execution checkpoints
- each phase contains numbered steps
- each step uses `[ ]`, `[~]`, `[x]`

## Preview a Repository Setup

Use this to inspect the materialization preview support:

```powershell
python scripts/bootstrap_conductor.py --repo <repo-root> --preview
```

## Inspect Setup State

Use this to inspect project maturity, resumable setup state, and recommended skills:

```powershell
python scripts/setup_workspace.py --repo <repo-root>
```

Use this to inspect the guided setup checkpoints that should be followed:

```powershell
python scripts/setup_flow.py --repo <repo-root>
```

Use this to persist multi-turn revise/approve loop state:

```powershell
python scripts/conversation_state.py init --repo <repo-root> --command setup
```

Use this to advance or resume the exact next guided setup checkpoint:

```powershell
python scripts/flow_runtime.py --repo <repo-root> --command setup
python scripts/flow_runtime.py --repo <repo-root> --command setup --session <session.json> --decision "Approve"
```

Use this to write the approved shared-context drafts exactly as reviewed:

```powershell
python scripts/apply_setup_drafts.py --repo <repo-root> --drafts-json <approved-drafts.json>
```

## Materialize a Repository Context

Run the materialization step against a target repository:

```powershell
python scripts/bootstrap_conductor.py --repo <repo-root>
```

This recreates or refreshes the repo-local `conductor/` directory after the conversational setup has been confirmed.

For existing upstream-style Conductor repositories, this preserves shared context files and only fills missing canonical artifacts.

## Migrate a Legacy Codex-Native Workspace

If a repository was created with the older Codex-native workspace shape, migrate it before using the full lifecycle commands:

```powershell
python scripts/migrate_workspace.py --repo <repo-root>
```

This converts the workspace into the canonical Gemini-compatible format.

## Install Recommended Skills

Use this when the setup or new-track flow recommends skill installation:

```powershell
python scripts/install_skills.py --repo <repo-root> --catalog skills/catalog.md --skills <skill-name>
```

The installer writes Gemini skill payloads into `.gemini/skills/` and refreshes the corresponding Codex bridge wrappers in `.codex/skills/`.

Use this to inspect the guided new-track checkpoints before materializing the track:

```powershell
python scripts/new_track_flow.py --repo <repo-root> --title "Implement user authentication"
```

Use this to advance or resume the exact next guided new-track checkpoint:

```powershell
python scripts/flow_runtime.py --repo <repo-root> --command newTrack --target "Implement user authentication"
python scripts/flow_runtime.py --repo <repo-root> --command newTrack --target "Implement user authentication" --session <session.json> --decision "Approve"
```

Use this to write the approved spec and plan exactly as reviewed:

```powershell
python scripts/apply_new_track_drafts.py --repo <repo-root> --title "Implement user authentication" --spec-file <approved-spec.md> --plan-file <approved-plan.md>
```

Use these to inspect guided lifecycle checkpoints before the mutating helper steps:

```powershell
python scripts/implement_flow.py --repo <repo-root>
python scripts/implement_runtime.py --repo <repo-root> --track <track-id> --action start
python scripts/implement_runtime.py --repo <repo-root> --track <track-id> --action complete_task --sha <short-sha>
python scripts/commit_task.py --repo <repo-root> --code-message "feat: ..." --plan-message "conductor(plan): Mark task complete"
python scripts/review_flow.py --repo <repo-root> --run-tests
python scripts/commit_review_fixes.py --repo <repo-root> --message "fix(conductor): Apply review suggestions"
python scripts/revert_flow.py --repo <repo-root> --candidates
python scripts/execute_revert.py --repo <repo-root> --repair-state
python scripts/cleanup_flow.py --repo <repo-root>
python scripts/repair_track_state.py --repo <repo-root> --track <track-id> --status in_progress
```

## Update an Existing Installation

1. Pull or download the latest version of this repository.
2. Copy the updated contents again into `~/.codex/skills/conductor`.
3. Start a new Codex session so the updated skill is loaded.

## Supported Commands

The skill is intended for these explicit workflow triggers:

- `conductor:setup`
- `conductor:newTrack`
- `conductor:implement`
- `conductor:status`
- `conductor:review`
- `conductor:revert`
- `conductor:archive`

## Notes

- The skill can materialize a repo-local `conductor/` workspace from bundled libraries.
- The target repository still owns its own `AGENTS.md` and project-specific rules.
- The bootstrap script is only the final file generation step.
- Legacy Codex-native workspaces must be migrated before takeover support is guaranteed.
