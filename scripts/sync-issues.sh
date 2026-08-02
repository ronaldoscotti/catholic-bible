#!/usr/bin/env bash
#
# Syncs one GitHub issue per epic in docs/epics/.
#
# The epic file is the single source of truth. Title comes from its H1,
# milestone and labels come from its metadata table, body is the rest of the
# file. Edit the file, not this script, and never the issue in the browser.
#
# Safe to re-run and that is the point. An epic with no issue gets one. An epic
# whose file moved ahead of its issue gets the issue rewritten to match. The
# bracketed epic id in the H1 is the key, so renaming "[B2] Corpus extraction"
# to "[B2] Corpus export" updates the issue instead of opening a second one.
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

# GitHub stores CRLF and keeps its own trailing whitespace. Compare the text.
normalize() { tr -d '\r' | sed 's/[[:space:]]*$//'; }

# Label names out of an epic's metadata row, one per line. An epic with no
# Labels row is legal and returns nothing, so the grep miss cannot be allowed to
# fail the pipeline under pipefail.
labels_of() { meta Labels "$1" | grep -o '`[^`]*`' | tr -d '`' | sort || true; }

echo "== labels =="
for f in "$EPICS_DIR"/*.md; do labels_of "$f"; done | sort -u | while read -r label; do
  [ -n "$label" ] || continue
  if gh label create "$label" >/dev/null 2>&1; then
    echo "  created  $label"
  else
    echo "  exists   $label"
  fi
done

echo
echo "== milestones =="
for f in "$EPICS_DIR"/*.md; do meta Milestone "$f"; done | sort -u | while read -r milestone; do
  [ -n "$milestone" ] || continue
  if gh api "repos/$REPO/milestones" -f title="$milestone" >/dev/null 2>&1; then
    echo "  created  $milestone"
  else
    echo "  exists   $milestone"
  fi
done

echo
echo "== issues =="
existing=$(gh issue list --state all --limit 200 --json number,title -q '.[] | "\(.number)\t\(.title)"')

# Roadmap order, not glob order. A shell glob sorts B10 before B2, and the first
# run of this script created the issues in that order, which is why issue #3 is
# epic B10. Issue numbers cannot be renumbered, so this only keeps the next epic
# from landing in the same trap. The map is in SESSION_PROMPT.md.
for f in $(printf '%s\n' "$EPICS_DIR"/*.md | sort -V); do
  title=$(head -1 "$f" | sed 's/^#[[:space:]]*//')
  [ -n "$title" ] || { echo "  SKIP     $f has no H1"; continue; }

  tag=$(printf '%s' "$title" | grep -o '^\[[^]]*\]' || true)
  [ -n "$tag" ] || { echo "  SKIP     $f has no [id] in its H1"; continue; }

  number=$(printf '%s\n' "$existing" | awk -F'\t' -v t="$tag " 'index($2, t) == 1 { print $1; exit }')

  milestone=$(meta Milestone "$f")
  want_labels=$(labels_of "$f" | paste -sd, -)

  # Body is the file without its H1, since the H1 becomes the issue title.
  body=$(mktemp)
  tail -n +2 "$f" | normalize > "$body"

  label_args=()
  while read -r label; do
    [ -n "$label" ] || continue
    label_args+=(--label "$label")
  done < <(labels_of "$f")

  if [ -z "$number" ]; then
    url=$(gh issue create --title "$title" --body-file "$body" ${milestone:+--milestone "$milestone"} "${label_args[@]}")
    rm -f "$body"
    echo "  created  $title"
    echo "           $url"
    continue
  fi

  # One field per call. Combining them would need a separator that cannot appear
  # in a body, and command substitution drops NUL.
  live_title=$(gh issue view "$number" --json title -q .title)
  live_body=$(gh issue view "$number" --json body -q .body | normalize)
  live_labels=$(gh issue view "$number" --json labels -q '[.labels[].name] | sort | join(",")')
  live_milestone=$(gh issue view "$number" --json milestone -q '.milestone.title // ""')

  changed=()
  [ "$live_title" = "$title" ] || changed+=(title)
  [ "$live_body" = "$(cat "$body")" ] || changed+=(body)
  [ "$live_labels" = "$want_labels" ] || changed+=(labels)
  [ "$live_milestone" = "$milestone" ] || changed+=(milestone)

  if [ ${#changed[@]} -eq 0 ]; then
    rm -f "$body"
    echo "  current  #$number $title"
    continue
  fi

  # Split on the comma, never on whitespace. A label added in the browser can
  # carry a space, "help wanted" being the one GitHub ships by default, and
  # word splitting would ask gh to remove two labels that do not exist.
  edit_args=("${label_args[@]/--label/--add-label}")
  IFS=, read -ra live_arr <<< "$live_labels"
  for l in ${live_arr[@]+"${live_arr[@]}"}; do
    [ -n "$l" ] || continue
    labels_of "$f" | grep -qxF "$l" || edit_args+=(--remove-label "$l")
  done

  gh issue edit "$number" --title "$title" --body-file "$body" \
    ${milestone:+--milestone "$milestone"} "${edit_args[@]}" >/dev/null

  rm -f "$body"
  echo "  synced   #$number $title  ($(IFS=,; echo "${changed[*]}"))"
done

echo
echo "done. dependencies between epics are written in each body and are not"
echo "enforced by GitHub. Read them before picking one up."
