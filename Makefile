.PHONY: test lint lint-fix format goldens run

test:
	uv run pytest

lint:
	uv run ruff check .

lint-fix:
	uv run ruff check --fix .

format:
	uv run ruff format .

goldens:
	echo "no golden harness runner yet (M3)"

run:
	uv run python src/main.py
