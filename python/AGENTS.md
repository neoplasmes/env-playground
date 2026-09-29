# Python workspace

- Read `../ARCHITECTURE.backend.md` for ownership. Keep domain validation pure,
  application ports with their consumers, and Pillow/HTTP/configuration in adapters.
- Use this directory's uv workspace and lockfile; do not create another environment
  in an application directory. Moon supplies the working directory and dependencies.
- Changes to formats, dimensions, orientation, animation, metadata, or failure
  behavior must agree with the Rust API and UI contract; use `$image-processing-change`.
- Run `moon run image-processor:check` and the relevant tests. Changes to the shared
  statement-padding tool also require `repo-style:test` and affected language checks.
