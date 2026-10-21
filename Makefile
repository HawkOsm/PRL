.PHONY: test lint lint-fix format goldens run unused-public

test:
	uv run pytest

lint:
	uv run ruff check .

lint-fix:
	uv run ruff check --fix .

format:
	uv run ruff format .

goldens:
	uv run python src/run_goldens.py

run:
	uv run python src/main.py

unused-public:
	uv run python tools/unused_public.py
