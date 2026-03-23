# Track Lifecycle

Tracks are live workflow units under `conductor/tracks/<track-id>/`.

Required live files per track:

- `index.md`
- `metadata.json`
- `spec.md`
- `plan.md`
- `review.md`
- `verify.md`

Lifecycle expectations:

1. `conductor:newTrack` creates the live track artifacts.
2. `scripts/new_track_flow.py` should be used before materialization to drive the branch, spec, plan, and skills checkpoints for the track.
3. At the start of each track, Conductor asks whether to create or use a dedicated branch for that track.
4. The branch decision should be reflected in the track's working context or early plan notes, and unfinished tracks should not remain on shared branches.
5. Track IDs should use the canonical upstream short-name plus date shape, for example `user-auth_20260323`.
6. `metadata.json` should use canonical keys including `track_id`, `type`, `status`, `created_at`, `updated_at`, and `description`.
7. `plan.md` should use phases as the main checkpoints, with `[ ]`, `[~]`, `[x]` task markers and room to append task SHA or phase checkpoint annotations.
8. `conductor:implement` progresses the next pending task from `plan.md`.
9. The track registry in `conductor/tracks.md` is the canonical project-level source of truth for active tracks.
10. Verification should be planned against the approved repository coverage target and the repository's workflow rules.
11. `conductor:review` records findings and a decision in `review.md`.
12. `conductor:archive` moves only completed tracks into `conductor/archive/` and removes or updates the active registry entry.
13. `conductor:implement` should preserve task SHA recording and phase checkpoint annotations when they exist or when the workflow requires them.
14. When a workflow requires phase checkpointing, `scripts/implement_runtime.py --action checkpoint_phase` should gate the transition into the next phase or doc-sync handoff.
15. `scripts/implement_runtime.py --action commit_task` should drive the explicit code-commit then plan-commit branch before moving into the next task, checkpoint, or doc-sync stage.
16. `scripts/draft_new_track.py` may be used to generate first-pass `spec.md` and `plan.md` content before the interactive confirmation loop.
