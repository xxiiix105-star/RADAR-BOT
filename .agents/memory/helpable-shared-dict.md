---
name: HELPABLE shared dict — __main__ vs Rose package
description: Why HELPABLE must live in Rose/__init__.py, not Rose/__main__.py
---

## The rule
`HELPABLE` must be declared in `Rose/__init__.py`, NOT in `Rose/__main__.py`.

## Why
When the bot runs as `python -m Rose`, the entrypoint is executed as `__main__`,
NOT as `Rose.__main__`. Any plugin that does `import Rose.__main__` later gets a
SEPARATE module object with its own fresh `HELPABLE = {}` that was never populated
by `start_bot()`. So `_helpable()` always returned `{}`, causing the keyboard builder
to produce zero module buttons after a language switch.

## How to apply
- `Rose/__init__.py`: `HELPABLE: dict = {}`
- `Rose/__main__.py`: `from Rose import (..., HELPABLE)` — import, do not declare.
  Remove `global HELPABLE` from `start_bot()`; mutate in-place via `HELPABLE[k] = v`.
- Any plugin needing HELPABLE: `from Rose import HELPABLE` directly.
