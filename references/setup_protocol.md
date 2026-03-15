# Setup Protocol

`conductor:setup` is a conversational-first command.

It must not be treated as "run bootstrap and confirm".

## Purpose

Build or refresh the shared project context that later commands depend on.

## Required phases

1. Repository analysis
2. Context gap detection
3. Guided questions
4. Proposed context summary
5. Preview of file changes
6. Explicit confirmation
7. File materialization

## Repository analysis

Before asking questions, inspect:

- `AGENTS.md`
- `README.md`
- solution and project files
- `src/` and `tests/`
- existing `conductor/` files if present

Infer stable facts first.

## Guided questions

Ask questions for all major context areas when they are not already stable and explicit:

- product mission
- target audience
- scope boundaries
- key workflows and delivery expectations
- technical stack
- testing and verification expectations
- styleguide or process expectations

When refreshing an existing `conductor/`, treat current files as draft context and ask for confirmation where drift or ambiguity exists.

## Preview

Before writing files, show:

- the shared context summary
- which files will be created or updated
- the most important changes from the current context

No file write should happen before explicit user confirmation.

## Materialization

After confirmation:

- run the deterministic bootstrap materialization
- regenerate the shared files
- preserve real tracks
- refresh `tracks.md`

## Important rule

The scripts support setup, but they are not the setup itself.
