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
- `tracks.md` is the canonical Tracks Registry for active tracks.
- Track `index.md` is the per-track navigation view.
- `metadata.json` is supporting structured state and must stay aligned with the registry and track files.
- `spec.md`, `plan.md`, `review.md`, and `verify.md` remain the operational source of truth.
- Generated helpers must preserve existing official files and only create or repair missing canonical artifacts.
