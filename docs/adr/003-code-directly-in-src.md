# 003 — Modules live directly in src/, imported by plain name
Date: 2026-10-21
Status: accepted
Context: The usual layout is `src/<package>/`. I did not want a second folder level. An
earlier attempt made the package itself called `src`, which led to imports like
`from src.events...` and a very generic package name.
Decision: Put the modules directly in `src/` (`src/main.py`, `src/events/`, `src/golden.py`
and so on) and import them by plain name (`from events.base import Events`). pytest finds
them through `pythonpath = ["src"]`, ruff through `src = ["src"]`. PRL is an application run
from the repo (`make run`), so pyproject sets `[tool.uv] package = false`: no build backend,
no installed `prl` command for now.
Consequences: One folder level less and short imports. Top-level names such as `events`
or `golden` are generic, so this is only safe as long as PRL is not installed next to other
projects. Shipping it later (the `pipx install` goal in the roadmap) means moving the code
into a named package such as `src/prl/` and adding a build backend again. The local placeholder
`src/.config` must not be committed.
