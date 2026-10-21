# 001 — Python is the implementation language
Date: 2026-10-13
Status: accepted
Context: I tried a Rust rewrite for about a week (skeleton, Makefile, first structs). Rust is
slower for a beginner, the Python version already existed, and the local-model part (the
router, the clarifier, the compiler) is mostly prompts, golden cases and scoring, not
low-level performance. AI/ML jobs mostly ask for Python.
Decision: Python 3.12 with uv stays the only implementation. The Rust files were deleted
(they remain only in git history, commits 2dbebef and bb55bdb).
Consequences: Faster progress toward the ML part (target 2026-11-25). Command start-up is
slower than a native binary (measured: about 133 ms with pydantic imported, against about
1 ms for a Rust hello world), which only matters if a mod calls `prl` on every key press.
