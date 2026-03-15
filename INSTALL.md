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
- `references/bootstrap.md`
- `references/setup_protocol.md`
- `references/brownfield_scan.md`
- `references/track_lifecycle.md`
- `references/review_revert_archive.md`
- `references/artifact_sync.md`
- `scripts/bootstrap_conductor.py`
- `scripts/new_track.py`
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
6. require explicit confirmation
7. only then materialize the repo-local `conductor/` workspace

The shared Git workflow encoded by the skill is:

- branch policy: ask per track
- commit policy: commit per phase

Track plans are expected to use a hybrid format:

- phases remain the main execution checkpoints
- each phase contains numbered steps
- each step uses `[ ]`, `[~]`, `[x]`

The shared quality workflow encoded by the skill is:

- coverage target is explicitly requested during setup
- for this repository, the target is 100%

## Preview a Repository Setup

Use this to inspect the materialization preview support:

```powershell
python scripts/bootstrap_conductor.py --repo <repo-root> --preview
```

## Materialize a Repository Context

Run the materialization step against a target repository:

```powershell
python scripts/bootstrap_conductor.py --repo <repo-root>
```

This recreates or refreshes the repo-local `conductor/` directory after the conversational setup has been confirmed.

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
