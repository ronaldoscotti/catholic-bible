#!/usr/bin/env bash
#
# Re-exports the dataset at the commit PROVENANCE.json records and compares it
# byte for byte with what is committed here.
#
# This is the only check in this repo that catches a hand edit. The checksum
# tests cannot, because data and hash are committed together. See LIMITS.md.
#
set -euo pipefail

RAW="${1:?usage: verify-export.sh <path to private repo>}"
SOURCE=$(cd "${RAW/#\~/$HOME}" && pwd)
cd "$(dirname "$0")/.."

recorded=$(python3 -c "import json;print(json.load(open('src/catholic_bible/data/corpus/PROVENANCE.json'))['source']['commit'])")
head=$(git -C "$SOURCE" rev-parse HEAD)

# Without this the target reports a hand edit every time the private repo gains
# an unrelated commit, because the fresh provenance would name a different one.
if [ "$recorded" != "$head" ]; then
  echo "the source is at $head and provenance records $recorded"
  echo "check that commit out in $SOURCE and run this again, or re-export if the data should move"
  exit 1
fi

rm -rf .verify && mkdir -p .verify/spine .verify/corpus
./scripts/export-spine.py --source "$SOURCE" --dest .verify/spine >/dev/null
./scripts/export-corpus.py --source "$SOURCE" --dest .verify/corpus >/dev/null

status=0
diff -r .verify/corpus src/catholic_bible/data/corpus || status=$?
diff -r .verify/spine src/catholic_bible/data --exclude=corpus --exclude=derived || status=$?
rm -rf .verify

# diff exits 1 for a difference and 2 for trouble. They are not the same thing
# and an accusation of tampering should not be raised by a missing directory.
case "$status" in
  0) echo "verified: the committed data is byte for byte a fresh export at $recorded" ;;
  1) echo "MISMATCH: the committed data is not what the source produces"; exit 1 ;;
  *) echo "the comparison itself failed, exit $status. this is not a finding"; exit "$status" ;;
esac
