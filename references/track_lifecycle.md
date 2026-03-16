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

1. `conductor:newTrack` must create or switch to a dedicated branch for the track before generating live track artifacts.
2. Unfinished tracks must not remain on `main` or another shared branch that is not the track's dedicated branch.
3. The track branch decision should be reflected in the track's working context or early plan notes.
4. `plan.md` should use phases as the main checkpoints, with numbered steps inside each phase and `[ ]`, `[~]`, `[x]` markers on each step.
5. `conductor:implement` progresses the next pending step from `plan.md`.
6. The standard commit boundary is the end of a phase, not every individual task.
7. Verification should be planned against the approved repository coverage target.
8. `conductor:review` records findings and a decision in `review.md`.
9. `conductor:archive` moves only completed tracks into `conductor/archive/`, and the archived directory must no longer remain under `conductor/tracks/`.
