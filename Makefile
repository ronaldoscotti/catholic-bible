.PHONY: install test lint fmt typecheck run down export-corpus verify-export

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

export-corpus:
	./scripts/export-spine.py --source $(SOURCE)
	./scripts/export-corpus.py --source $(SOURCE)
	uv run scripts/build-orphans.py
	uv run scripts/build-coverage.py

# The job with teeth. Re-exports at the commit provenance records, into a
# scratch directory, and compares. Exporting over the committed files first
# would destroy the evidence before looking for it, and re-exporting at
# whatever the source happens to be checked out at would report every
# unrelated commit as a hand edit. LIMITS.md tells the reader that MISMATCH
# means someone edited a verse, so it must not cry wolf.
# It cannot run on a fork or in CI.
verify-export:
	@test -n "$(SOURCE)" || { echo "usage: make verify-export SOURCE=~/path/to/private/repo"; exit 1; }
	@./scripts/verify-export.sh "$(SOURCE)"
