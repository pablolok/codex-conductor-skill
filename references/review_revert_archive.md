# Review, Revert, Archive

## Review

- Review against `spec.md`, `plan.md`, `AGENTS.md`, and executed verification.
- Consider whether the recorded commit history matches the shared commit policy for phase checkpoints.
- Consider whether the verification evidence is consistent with the approved coverage target.
- Record findings, risks, gaps, and decision in `review.md`.

## Revert

- Scope the revert to a track, phase, or task/sub-task.
- Reconcile git history with the logical work described in the track files.
- Assume the normal git history is organized around phase-level commits unless the track explicitly recorded a different approach.
- Realign `plan.md`, `review.md`, `verify.md`, `metadata.json`, and indexes after the revert.

## Archive

- Archive only tracks whose `status` is `done`.
- Move the track directory to `conductor/archive/` before finalizing archived metadata so partial archive state is avoided if the move fails.
- Update `status`, `phase`, `archivedAt`, and the stored track path after the move succeeds.
- Ensure no archived track directory remains under `conductor/tracks/`.
- Refresh `conductor/index.md` and `conductor/tracks.md`.
