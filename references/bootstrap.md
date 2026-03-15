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
3. Remove stale generated scaffolds that should not live in the repo target, including:
   - `conductor/templates/`
   - `conductor/tracks/_template/`
4. Rebuild `index.md` and `tracks.md` from track and archive metadata.

The materialization step is idempotent:

- if `conductor/` is missing, recreate it from scratch
- if `conductor/` exists, refresh shared context without duplicating state
