# Git Commit Prefix Convention

> English translation of [`docs/Git提交前缀.md`](../Git提交前缀.md).

## Overview

To keep the repo's commit history clean and consistent, the commit message format is standardized. This doc defines the basic structure of a commit message plus a set of common prefixes. Please follow it.

## Commit message format

Commit messages should follow the format below. Use a colon followed by a space, then a short description, e.g. `: fix bug`.

```plaintext
<prefix>(optional scope): <space> <short description>
<blank line>
<detailed description> (if applicable)
<blank line>
- <bullet description> (if applicable)
```

### Example

```plaintext
refactor(PublicAreaDailyTasks): refactor the public-area daily tasks

Visiting the lounge and dispatch-room assignments currently create too many options, so they can be merged into a single task entry that runs both from within the public-area dailies.

- Removed the original "enter lounge" and "dispatch-room daily" options from interface.json and folded them into the public-area daily task as sub-options
- Extracted the lounge / dispatch-room code into public
- Added a PublicAreaDailyTasks file for interface.json to call as a user task option
- Adjusted some naming conventions
```

## Prefix list

### Common prefixes

- `feat` — New feature. For commits that add functionality.
- `fix` — Bug fix. For commits that fix script errors and bugs.
- `docs` — Documentation. For commits that only touch docs.
- `chore` — Routine maintenance or chores. Commits that don't directly affect source or tests, such as updating build config, or removing unused code/files. When used for deletion, it generally means a replacement or optimization will follow.

  ```plaintext
  chore(ClaimStamina): remove the limited-time stamina claim on the event page; all event-page features will migrate to ClaimEventRewards for unified management
  ```

- `refactor` — Refactor existing code without changing external behavior.
- `perf` — Performance. Commits that improve code performance.
- `remove` — Removal. Removing code/scripts that are no longer used, generally deprecated scripts with no replacement. Example:

  ```plaintext
  remove(ClaimStamina): remove the deprecated limited-time stamina claim script
  ```

- `rename` — Rename a file or directory.

### Less common prefixes

- `merge` — Merge branches.
- `release` — Prepare a release.
- `init` — Initial commit or project initialization.
- `config` — Config file changes.
- `style` — Style-only changes that don't affect behavior (whitespace, semicolons, etc.).
- `deps` — Update dependency versions.
- `test` — Add missing tests or fix existing ones.
- `ci` — Continuous-integration changes.
- `build` — Build-system changes.
- `revert` — Revert to a previous or specific commit.

## Optional scope

Where applicable, add a scope in parentheses after the prefix to point to the affected feature/file so others can locate the change quickly. In this project, the scope is usually the feature involved or the file modified. Use your own judgment.

### Example

```plaintext
fix(enterDispatchCenterAction): fix the dispatch one-click-claim recognition mismatch that prevented claiming
```

## Writing guidelines

1. **Short description**
   - Must be a complete sentence starting with a verb.
   - Keep it short — ideally under 50 characters.
2. **Detailed description**
   - Provide a fuller explanation if needed.
   - Use complete sentences and paragraphs.
   - Include background, the solution, and any necessary context.
3. **Notes**
   - Avoid abbreviations and jargon unless they're widely understood by the team.
   - Avoid vague descriptions like "fix issue" or "update code".
