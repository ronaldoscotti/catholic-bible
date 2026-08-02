import hashlib
import json

from catholic_bible.canon import DATA_DIR

PROVENANCE = json.loads((DATA_DIR / "PROVENANCE.json").read_text(encoding="utf-8"))


def test_every_data_file_matches_its_recorded_checksum() -> None:
    for name, record in PROVENANCE["files"].items():
        payload = (DATA_DIR / name).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == record["sha256"], name


def test_provenance_covers_every_data_file() -> None:
    on_disk = {path.name for path in DATA_DIR.glob("*.json")} - {"PROVENANCE.json"}
    assert on_disk == set(PROVENANCE["files"])


def test_provenance_names_the_source_commit() -> None:
    source = PROVENANCE["source"]
    assert len(source["commit"]) == 40
    assert source["repository"]
    assert source["private"] is True
