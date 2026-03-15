# Command Workflow

## `conductor:implement`

- Select the correct open track.
- If multiple candidates exist and the request is ambiguous, list them and ask the user to choose.
- Work from the next pending item in `plan.md`.
- Mark progress using `[ ]`, `[~]`, `[x]`.
- Update:
  - `metadata.json`
  - `tracks.md`
  - `verify.md`

## `conductor:review`

- Review against `spec.md`, `plan.md`, `AGENTS.md`, and executed verification.
- Write findings into `review.md`.

## `conductor:revert`

- Scope revert to track, phase, or task/sub-task.
- Be explicit about the rollback target.
- Reflect the rollback in `plan.md`, `review.md`, `verify.md`, `metadata.json`, and `tracks.md`.

## `conductor:archive`

- Only archive tracks with `status: done`.
- Move them from `conductor/tracks/` to `conductor/archive/`.
- Update `status`, `phase`, and `archivedAt`.
- Regenerate `tracks.md`.
