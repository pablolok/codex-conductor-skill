# Setup Protocol

`conductor:setup` should mirror the official Conductor prompt flow as closely as possible.

Follow this order:

1. Audit `conductor/` for resumable setup artifacts using `scripts/setup_workspace.py`.
2. Generate the concrete setup checkpoint sequence using `scripts/setup_flow.py`.
3. Detect whether the repository is greenfield or brownfield.
4. On brownfield, ask permission before any read-only project scan.
5. Infer stable context from `README.md`, `AGENTS.md`, manifests, source layout, and existing Conductor files.
6. If an upstream-style `conductor/` workspace already exists, preserve it and resume from its actual state.
7. If a legacy Codex-native workspace is detected, stop and require migration before full lifecycle operations.
8. Ask only the missing or preference-driven questions needed to complete:
   - product context
   - product guidelines
   - tech stack
   - workflow expectations
   - track branch naming or branch workflow details if the repository needs them
   - coverage target
   - styleguide selection
9. In the workflow section, explicitly confirm whether existing workflow rules should be preserved or refreshed.
   - branch policy: ask per track whether to create or use a dedicated branch
   - shared branch hygiene: unfinished tracks should not remain on shared branches
   - commit policy: commit per phase unless preserved workflow says otherwise
   - coverage target: ask explicitly and record the approved threshold
10. Produce a proposed shared context summary.
11. Preview the live workspace artifacts that would be created or refreshed, including the approved workflow policy.
12. Ask for explicit confirmation.
13. Only after confirmation, materialize or repair the canonical `conductor/` workspace.
14. When the workspace is ready, hand off into the initial track flow if the session requires it.

Support scripts:

- `scripts/setup_workspace.py` for maturity detection, artifact audit, resume target, and skills recommendations
- `scripts/setup_flow.py` for concrete setup checkpoints, question batches, approval payloads, and reload pause instructions
- `scripts/draft_setup_docs.py` for first-pass document drafts during interactive setup

Interaction bridge:

- In Plan Mode, preserve Gemini-style checkpoint questions with `request_user_input`.
- In Default mode, ask the same checkpoints inline and resume the flow after the user answers.

Scripts support setup, but they do not define setup.
