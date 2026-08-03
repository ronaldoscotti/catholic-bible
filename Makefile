.PHONY: install test lint fmt typecheck run down db openapi export-corpus export-commentary review-sample verify-export

install:
	uv sync

test:
	uv run pytest

# Derived from the committed corpus. Not committed, and carrying no checksum,
# because CI already verifies the checksums of everything it is built from.
db:
	uv run scripts/build-db.py

# Generated from the routes. CI regenerates it and fails on a difference.
openapi:
	uv run scripts/build-openapi.py

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

export-commentary:
	./scripts/export-commentary.py --source $(SOURCE)

review-sample:
	uv run scripts/draw-review-sample.py

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
