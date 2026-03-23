# Bootstrap Contract

`scripts/bootstrap_conductor.py` is the deterministic materialization step used after the conversational setup has been approved.

Expected behavior:

1. Generate or refresh only live workspace artifacts:
   - `README.md`
   - `workflow.md`
   - `product.md`
   - `product-guidelines.md`
   - `tech-stack.md`
   - `index.md`
   - `tracks.md`
   - selected files in `code_styleguides/`
   - `archive/`
2. Preserve real tracks when refreshing.
3. Preserve existing official shared context files where they already exist.
4. Refuse to refresh a legacy Codex-native workspace and require migration first.
5. Remove stale generated scaffolds that should not live in the repo target, including:
   - `conductor/templates/`
   - `conductor/tracks/_template/`
6. Rebuild `index.md` from the canonical registry and archive metadata.
7. Create `tracks.md` only when it is missing; never overwrite an existing canonical registry during bootstrap refresh.

The materialization step is idempotent:

- if `conductor/` is missing, recreate it from scratch
- if `conductor/` exists in canonical form, refresh shared scaffolding without duplicating state
