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

## About `conductor:setup`

`conductor:setup` is conversational-first.

It should:

- analyze the target repository
- gather or refresh the shared context through guided questions
- show a preview of the proposed context and file changes
- require explicit confirmation
- only then materialize the repo-local `conductor/` files

## Materialization Script

The bootstrap script supports the final materialization step:

```powershell
python scripts/bootstrap_conductor.py --repo <repo-root>
```

Preview support:

```powershell
python scripts/bootstrap_conductor.py --repo <repo-root> --preview
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
- The bootstrap script is not the full meaning of `conductor:setup`; it only materializes the agreed context.
