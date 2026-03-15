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
   - styleguide selection
6. Produce a proposed shared context summary.
7. Preview the live workspace artifacts that would be created or refreshed.
8. Ask for explicit confirmation.
9. Only after confirmation, materialize `conductor/`.
10. When the workspace is ready, hand off into the initial track flow if the session requires it.

Scripts support setup, but they do not define setup.
