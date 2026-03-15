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
3. The branch decision should be reflected in the track's working context or early plan notes.
4. `conductor:implement` progresses the next task from `plan.md`.
5. The standard commit boundary is the end of a phase, not every individual task.
6. `conductor:review` records findings and a decision in `review.md`.
7. `conductor:archive` moves only completed tracks into `conductor/archive/`.
