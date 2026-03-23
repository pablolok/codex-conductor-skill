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
2. At the start of each track, Conductor asks whether to create or use a dedicated branch for that track.
3. The branch decision should be reflected in the track's working context or early plan notes, and unfinished tracks should not remain on shared branches.
4. Track IDs should use the canonical upstream short-name plus date shape, for example `user-auth_20260323`.
5. `metadata.json` should use canonical keys including `track_id`, `type`, `status`, `created_at`, `updated_at`, and `description`.
6. `plan.md` should use phases as the main checkpoints, with `[ ]`, `[~]`, `[x]` task markers and room to append task SHA or phase checkpoint annotations.
7. `conductor:implement` progresses the next pending task from `plan.md`.
8. The track registry in `conductor/tracks.md` is the canonical project-level source of truth for active tracks.
9. Verification should be planned against the approved repository coverage target and the repository's workflow rules.
10. `conductor:review` records findings and a decision in `review.md`.
11. `conductor:archive` moves only completed tracks into `conductor/archive/` and removes or updates the active registry entry.
