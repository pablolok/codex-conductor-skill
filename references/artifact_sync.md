# Artifact Sync Rules

Primary workspace artifacts:

- `conductor/index.md`
- `conductor/tracks.md`
- `conductor/tracks/<track-id>/index.md`
- `conductor/tracks/<track-id>/metadata.json`
- `conductor/tracks/<track-id>/spec.md`
- `conductor/tracks/<track-id>/plan.md`
- `conductor/tracks/<track-id>/review.md`
- `conductor/tracks/<track-id>/verify.md`

Sync rules:

- `index.md` is the primary workspace navigation file.
- `tracks.md` is a compact compatibility summary, regenerated from metadata.
- Track `index.md` is the per-track navigation view, regenerated from `metadata.json`.
- `spec.md`, `plan.md`, `review.md`, and `verify.md` remain the operational source of truth.
