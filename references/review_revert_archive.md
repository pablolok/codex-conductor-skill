# Review, Revert, Archive

## Review

- Review against `spec.md`, `plan.md`, `AGENTS.md`, and executed verification.
- Record findings, risks, gaps, and decision in `review.md`.

## Revert

- Scope the revert to a track, phase, or task/sub-task.
- Reconcile git history with the logical work described in the track files.
- Realign `plan.md`, `review.md`, `verify.md`, `metadata.json`, and indexes after the revert.

## Archive

- Archive only tracks whose `status` is `done`.
- Update `status`, `phase`, and `archivedAt`.
- Move the track directory to `conductor/archive/`.
- Refresh `conductor/index.md` and `conductor/tracks.md`.
