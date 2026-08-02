#!/usr/bin/env bash
#
# Creates one GitHub issue per epic in docs/epics/.
#
# The epic file is the single source of truth. Title comes from its H1,
# milestone and labels come from its metadata table. Edit the file, not this
# script.
#
# Safe to re-run. An epic that already has an issue is skipped, so this can be
# used to add newly written epics later.
#
set -euo pipefail

cd "$(dirname "$0")/.."
EPICS_DIR="docs/epics"

command -v gh >/dev/null || { echo "gh CLI not found. brew install gh"; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "not authenticated. run: gh auth login"; exit 1; }
[ -d "$EPICS_DIR" ] || { echo "no $EPICS_DIR directory"; exit 1; }

REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
echo "target: $REPO"
echo

# Reads a row out of the metadata table at the top of an epic file.
# "| Labels | `epic` `area/data` |" -> "`epic` `area/data`"
meta() { grep -m1 "^| $1 " "$2" 2>/dev/null | sed 's/^|[^|]*|[[:space:]]*//; s/[[:space:]]*|[[:space:]]*$//' || true; }

echo "== labels =="
for f in "$EPICS_DIR"/*.md; do
  meta Labels "$f" | grep -o '`[^`]*`' | tr -d '`'
done | sort -u | while read -r label; do
  [ -n "$label" ] || continue
  if gh label create "$label" >/dev/null 2>&1; then
    echo "  created  $label"
  else
    echo "  exists   $label"
  fi
done

echo
echo "== milestones =="
for f in "$EPICS_DIR"/*.md; do
  meta Milestone "$f"
done | sort -u | while read -r milestone; do
  [ -n "$milestone" ] || continue
  if gh api "repos/$REPO/milestones" -f title="$milestone" >/dev/null 2>&1; then
    echo "  created  $milestone"
  else
    echo "  exists   $milestone"
  fi
done

echo
echo "== issues =="
existing=$(gh issue list --state all --limit 200 --json title -q '.[].title')

for f in "$EPICS_DIR"/*.md; do
  title=$(head -1 "$f" | sed 's/^#[[:space:]]*//')
  [ -n "$title" ] || { echo "  SKIP     $f has no H1"; continue; }

  if printf '%s\n' "$existing" | grep -qxF "$title"; then
    echo "  exists   $title"
    continue
  fi

  milestone=$(meta Milestone "$f")
  label_args=()
  while read -r label; do
    [ -n "$label" ] && label_args+=(--label "$label")
  done < <(meta Labels "$f" | grep -o '`[^`]*`' | tr -d '`')

  # Body is the file without its H1, since the H1 becomes the issue title.
  body=$(mktemp)
  tail -n +2 "$f" > "$body"

  url=$(gh issue create \
    --title "$title" \
    --body-file "$body" \
    ${milestone:+--milestone "$milestone"} \
    "${label_args[@]}")

  rm -f "$body"
  echo "  created  $title"
  echo "           $url"
done

echo
echo "done. dependencies between epics are written in each body and are not"
echo "enforced by GitHub. Read them before picking one up."
