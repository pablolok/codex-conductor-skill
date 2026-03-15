# Codex Conductor Skill

This folder is a standalone Codex skill package for a Google Conductor-style workflow.

It is structured so it can be moved into its own repository without depending on this finance dashboard repository.

## Contents

- `SKILL.md`
- `agents/openai.yaml`
- `references/`
- `scripts/`
- `assets/repo_templates/`

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

## Bootstrap Script

The bootstrap script can recreate a repo-local `conductor/` workspace from bundled templates:

```powershell
python scripts/bootstrap_conductor.py --repo <repo-root>
```

## Publish As Its Own Repo

If you want to publish this as a separate repository:

1. Copy `conductor-skill/` out of this repo.
2. Initialize a new git repository in that copied folder.
3. Keep the folder name as `conductor` or rename it on install so Codex resolves it as the `conductor` skill.

## Notes

- The skill is self-contained.
- The bundled templates are generic bootstrap material.
- The target repository still provides its own `AGENTS.md` and project-specific context.
