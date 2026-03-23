# Review, Revert, Archive

## Review

- Review against `spec.md`, `plan.md`, `AGENTS.md`, and executed verification.
- Consider whether the recorded commit history matches the workflow recorded in `conductor/workflow.md`.
- Consider whether the verification evidence is consistent with the approved coverage target.
- Use deterministic helpers to derive scope, diff range, and revert candidates before the agent takes mutating steps.
- Use `scripts/review_flow.py` to materialize the review checkpoint sequence before mutating `review.md`.
- Record findings, risks, gaps, and decision in `review.md`.
- If the review changes the logical track state, run `scripts/repair_track_state.py` before cleanup.

## Revert

- Scope the revert to a track, phase, or task/sub-task.
- Reconcile git history with the logical work described in the track files and the canonical registry in `conductor/tracks.md`.
- Preserve task SHA and phase checkpoint annotations when they already exist in `plan.md`.
- Use `scripts/revert_flow.py` to materialize the rollback candidates and repair checklist before mutating git history.
- Realign `plan.md`, `review.md`, `verify.md`, `metadata.json`, and indexes after the revert.
- Use `scripts/repair_track_state.py` after the rollback when the track status must be reset.

## Archive

- Archive only tracks whose `status` is `completed` or whose effective state is clearly complete.
- Update `status` and `archived_at`.
- Move the track directory to `conductor/archive/`.
- Remove or update the active entry in `conductor/tracks.md`.
- Refresh `conductor/index.md`.
- Ensure no archived track directory remains under `conductor/tracks/`.
- Use `scripts/cleanup_track.py` to model archive, delete, or skip decisions before mutating track storage.
- Use `scripts/cleanup_flow.py` to surface the cleanup decision set before mutating storage.
