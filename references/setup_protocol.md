# Setup Protocol

`conductor:setup` should mirror the official Conductor prompt flow as closely as possible.

Follow this order:

1. Audit `conductor/` for resumable setup artifacts.
2. Detect whether the repository is greenfield or brownfield.
3. On brownfield, ask permission before any read-only project scan.
4. Infer stable context from `README.md`, `AGENTS.md`, manifests, source layout, and existing Conductor files.
5. Ask only the missing or preference-driven questions needed to complete:
   - product context
   - product guidelines
   - tech stack
   - workflow expectations
   - track branch naming or branch workflow details if the repository needs them
   - coverage target
   - styleguide selection
6. In the workflow section, explicitly approve:
   - branch policy: every track must use a dedicated branch, and that branch must be created or selected before any track files are generated
   - shared branch hygiene: `main` or other shared branches must not contain unfinished tracks that belong to another branch
   - commit policy: commit per phase
   - coverage target: ask explicitly and record the approved threshold
7. Produce a proposed shared context summary.
8. Preview the live workspace artifacts that would be created or refreshed, including the approved workflow policy.
9. Ask for explicit confirmation.
10. Only after confirmation, materialize `conductor/`.
11. When the workspace is ready, hand off into the initial track flow if the session requires it.

Scripts support setup, but they do not define setup.
