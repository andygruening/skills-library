# Repository Instructions

This repository is a skill library. When a skill under `skills/` is created, updated, renamed, moved, or deleted, update the Skills section in `README.md` in the same change.

Before finishing a skill-library change:

- Verify the README summary reflects the current skill names, paths, categories, and purpose.
- Run `npx skills add . --list --full-depth` to confirm the local skill inventory is discoverable when the CLI is available.
- Validate each touched `SKILL.md` frontmatter for `name` and `description`.
