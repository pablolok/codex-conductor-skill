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
2. `conductor:implement` progresses the next task from `plan.md`.
3. `conductor:review` records findings and a decision in `review.md`.
4. `conductor:archive` moves only completed tracks into `conductor/archive/`.
