"""What the built wheel has to carry, which the type checker does not enforce.

`mypy` runs over `src` and `scripts` in one pass, so it resolves this package
from the source tree and never consults the marker. An installed copy is a
different question and nothing else here asks it.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def test_the_package_ships_its_type_marker() -> None:
    """PEP 561. Without it a consumer running mypy gets import-untyped.

    Every public function here is annotated and CI checks them, and none of
    that reaches anyone who installs the package unless this file is beside
    the code.
    """
    assert (REPO / "src" / "catholic_bible" / "py.typed").is_file()


def test_the_type_marker_is_inside_the_wheel_package_root() -> None:
    """A marker outside the packaged directory ships nothing.

    Hatchling copies the tree named here, so the assertion is that the marker
    sits under it rather than beside it.
    """
    config = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
    packages = config["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"]

    assert any((REPO / package / "py.typed").is_file() for package in packages), (
        packages
    )


def test_the_type_checker_reads_the_scripts() -> None:
    """`scripts/` holds two CI gates and was outside the checked set until B7.

    A gate the type checker never reads breaks on a rename at the worst moment.
    """
    config = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))

    assert "scripts" in config["tool"]["mypy"]["files"]


def project() -> dict[str, object]:
    config = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
    return dict(config["project"])


def test_the_distribution_is_named_for_a_registry_nobody_else_holds() -> None:
    """`catholic-bible` on PyPI is an unrelated project, taken 2026-03-30.

    Nothing was ever published from here, so the name in the metadata could
    never have worked and no tag would have told anyone why.
    """
    assert project()["name"] == "the-catholic-bible"


def test_the_licence_grants_mit_over_the_code() -> None:
    licence = (REPO / "LICENSE").read_text(encoding="utf-8")

    assert "MIT License" in licence
    assert "without restriction" in licence


def test_the_licence_does_not_let_mit_swallow_the_corpus() -> None:
    """The bundle is not MIT and saying so once is not enough.

    Both packages carry the corpus. `LIMITS.md` audits it asset by asset and
    the OpenBible cross-references are CC BY 4.0 with attribution required, so
    a licence file that stopped at the MIT grant would relicense somebody
    else's work and drop an obligation honoured inside every published file.
    """
    licence = (REPO / "LICENSE").read_text(encoding="utf-8")

    assert "CC BY 4.0" in licence
    assert "OpenBible.info" in licence
    assert "LIMITS.md" in licence


def test_the_metadata_points_at_the_licence_rather_than_naming_one() -> None:
    """A field that can hold only `MIT` holds nothing when MIT is not the truth.

    PEP 639 takes either an SPDX expression or the files themselves. The
    expression would be a claim over the corpus this repository cannot make.
    """
    fields = project()

    assert "license-files" in fields
    assert "LICENSE" in fields["license-files"]  # type: ignore[operator]
    assert "license" not in fields
