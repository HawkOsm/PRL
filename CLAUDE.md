# PRL — Prompt Refine Loop (`prl`)

A local-model layer in front of Claude Code: a small local LLM routes, clarifies and
compiles requests, and only a clean prompt reaches Claude. Implementation: Python 3.12
with `uv` (`src/`, `tests/`, `pyproject.toml`).
Plan and design: `docs/building.md` (milestones), `docs/design.md`, `docs/schemas.md`.

## Working contract (this is a learning project)
- **The owner makes the decisions and writes the code.** Every design decision (what to
  build, thresholds, expected values, which option) is theirs, and the important ones are
  recorded as a short ADR *before* the code. The owner writes every line of `src/` and
  `tests/`, including the expected values in tests. Claude recommends, gives the main
  tradeoff, and never decides silently.
- **Claude helps a lot, short of writing their modules.** Welcome and expected: a skeleton
  to fill in (signatures, docstrings, `...` bodies, a test outline with the arrange / act /
  assert steps marked), a worked example on generic names that shows the syntax or idiom,
  the exact line and cause of an error, plain-word steps, concept explanations *plus* a
  link, line-by-line review, and mutation checks of their tests. Claude may also write
  docs, ADR drafts, schedules, config and build files, and mechanical changes across files
  (a rename), when asked. Claude does not fill in the logic of a module or the expected
  values of a test. If unsure which side something falls on, ask once.
- **The owner reviews everything.** Nothing is committed that the owner cannot explain in
  plain words. Claude still reviews by running (below).
- **When stuck:** find the real cause by reproducing it, point at the file and line, name
  the concept, explain it briefly in plain words, and link a good source (check it exists
  and is beginner-friendly). Show the shape of the fix (a generic example or a skeleton) and
  let the owner write it.
- **Review by running:** run `make test` and `make lint`, reproduce suspected bugs with
  scratch scripts (never inside the project), report findings by severity, and say what
  the green tests do not cover. Correct your own earlier mistakes plainly.
- **Before coding:** work a tiny example by hand and write the steps in plain words, then
  the test, then the code.
- Use plain words and a small picture (text diagram) when explaining. Prefer one next
  step over a long list.
- Docs, schedules and notes may be written by Claude when asked.

## Commands
- `make test`, `make lint`, `make lint-fix`, `make format`, `make goldens` (pytest and ruff), `make run` (runs `src/main.py`).
- Run `make format` then `make lint-fix` before committing.

## Conventions
- Follow `docs/building.md` milestone order. A deviation from `docs/design.md` gets a
  short ADR in `docs/adr/` and an update to the design doc.
- Dependency direction: `core/` never imports `ui/`.
- pydantic v2 (`from pydantic import ...`, never `pydantic.v1`). Timestamps are
  timezone-aware UTC. Use `Literal` for fixed sets of values.
- Tests use `tmp_path` for files and explicit timestamps; avoid global state (a started
  freezegun clock must be stopped, so prefer its decorator or context manager).
- Router contract: a function `(message: str, session_active: bool) -> str` returning one
  of `PASSTHROUGH`, `TASK_NEW`, `TRIVIAL` (`META` for `/` commands).

## Git
- Small commits, one idea each, made when tests and lint are green. Formatting-only
  changes get their own commit.
- Stage files by name; never `git add .` or `-A` on a messy tree.
- Run `git status` before any command that could discard work. Stash or commit first.
- Do not commit `src/.config` (local placeholder) or `.claude/skills/` (ignored).
