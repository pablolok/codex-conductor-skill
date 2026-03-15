# Bootstrap Contract

`conductor:setup` must behave as an active bootstrap or refresh operation, not a passive check.

Expected behavior:

1. Inspect the repository for:
   - `AGENTS.md`
   - `README.md`
   - solution files
   - `src/` layout
2. Generate or refresh `conductor/`.
3. Create:
   - `README.md`
   - `workflow.md`
   - `product.md`
   - `product-guidelines.md`
   - `tech-stack.md`
   - `tracks.md`
   - `code_styleguides/README.md`
   - `templates/`
   - `tracks/_template/`
   - `archive/`
4. Preserve real tracks when refreshing.
5. Rebuild `tracks.md` from track and archive metadata.

The bootstrap is idempotent:

- if `conductor/` is missing, recreate it from scratch
- if `conductor/` exists, refresh shared context without duplicating state
