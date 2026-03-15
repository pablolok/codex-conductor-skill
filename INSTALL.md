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
- `references/command_workflow.md`
- `scripts/bootstrap_conductor.py`
- `scripts/new_track.py`
- `scripts/status_tracks.py`
- `scripts/archive_tracks.py`

## Bootstrap a Repository

Run the bootstrap script against a target repository:

```powershell
python scripts/bootstrap_conductor.py --repo <repo-root>
```

This recreates or refreshes the repo-local `conductor/` directory.

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

- The skill bootstraps a repo-local `conductor/` workspace from bundled templates.
- The target repository still owns its own `AGENTS.md` and project-specific rules.
