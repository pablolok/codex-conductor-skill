# Codex Conductor Skill

This folder is a standalone Codex skill package for an official-style Google Conductor workflow.

It is structured so it can be moved into its own repository without depending on this finance dashboard repository.

## Contents

- `SKILL.md`
- `agents/openai.yaml`
- `references/`
- `scripts/`
- `assets/repo_templates/`
- `assets/styleguides/`

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
- show a preview of the proposed live workspace artifacts and decisions
- require explicit confirmation
- only then materialize the repo-local `conductor/` files

The shared Git workflow currently encoded by the skill is:

- ask per track whether to create or use a dedicated branch
- use phase checkpoints as the standard commit boundary

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
- Template and styleguide libraries stay inside the skill.
- The target repository should receive only live `conductor/` artifacts, not repo-local template scaffolds.
- The target repository still provides its own `AGENTS.md` and project-specific context.
- The bootstrap script is not the full meaning of `conductor:setup`; it only materializes the agreed context.
