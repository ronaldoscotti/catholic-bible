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

# The job with teeth. Re-exports into a scratch directory and compares it with
# what is committed, so a hand edit is still on disk when the comparison runs.
# An earlier version exported over the committed files first, which destroyed
# the evidence before looking for it. It cannot run on a fork or in CI, and
# LIMITS.md says so.
verify-export:
	@test -n "$(SOURCE)" || { echo "usage: make verify-export SOURCE=~/path/to/private/repo"; exit 1; }
	@rm -rf .verify && mkdir -p .verify/spine .verify/corpus
	@./scripts/export-spine.py --source $(SOURCE) --dest .verify/spine >/dev/null
	@./scripts/export-corpus.py --source $(SOURCE) --dest .verify/corpus >/dev/null
	@diff -r .verify/corpus src/catholic_bible/data/corpus \
	  && diff -r .verify/spine src/catholic_bible/data --exclude=corpus --exclude=derived \
	  && echo "verified: the committed data is byte for byte a fresh export" \
	  || { echo "MISMATCH: committed data differs from a fresh export"; rm -rf .verify; exit 1; }
	@rm -rf .verify
