.PHONY: install test lint fmt typecheck run down

install:
	uv sync

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .

fmt:
	uv run ruff format .
	uv run ruff check --fix .

typecheck:
	uv run mypy

run:
	docker compose up --build

down:
	docker compose down
