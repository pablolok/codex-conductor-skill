# Review, Revert, Archive

## Review

- Review against `spec.md`, `plan.md`, `AGENTS.md`, and executed verification.
- Consider whether the recorded commit history matches the workflow recorded in `conductor/workflow.md`.
- Consider whether the verification evidence is consistent with the approved coverage target.
- Use deterministic helpers to derive scope, diff range, and revert candidates before the agent takes mutating steps.
- Record findings, risks, gaps, and decision in `review.md`.

## Revert

- Scope the revert to a track, phase, or task/sub-task.
- Reconcile git history with the logical work described in the track files and the canonical registry in `conductor/tracks.md`.
- Preserve task SHA and phase checkpoint annotations when they already exist in `plan.md`.
- Realign `plan.md`, `review.md`, `verify.md`, `metadata.json`, and indexes after the revert.

## Archive

- Archive only tracks whose `status` is `completed` or whose effective state is clearly complete.
- Update `status` and `archived_at`.
- Move the track directory to `conductor/archive/`.
- Remove or update the active entry in `conductor/tracks.md`.
- Refresh `conductor/index.md`.
- Ensure no archived track directory remains under `conductor/tracks/`.
- Use `scripts/cleanup_track.py` to model archive, delete, or skip decisions before mutating track storage.
