# Bootstrap Contract

`conductor:setup` must behave as a conversational context-building workflow followed by a deterministic materialization step.

Expected behavior:

1. Inspect the repository for:
   - `AGENTS.md`
   - `README.md`
   - solution files
   - `src/` layout
   - existing `conductor/` files when present
2. Build a proposed shared context in conversation.
3. Show a preview of the files that would be created or updated.
4. Require explicit confirmation.
5. Generate or refresh `conductor/`.
6. Create:
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
7. Preserve real tracks when refreshing.
8. Rebuild `tracks.md` from track and archive metadata.

The materialization step is idempotent:

- if `conductor/` is missing, recreate it from scratch
- if `conductor/` exists, refresh shared context without duplicating state
