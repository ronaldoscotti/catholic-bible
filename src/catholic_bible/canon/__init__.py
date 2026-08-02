"""The canon and the versification spine.

Imports nothing from storage or api. Dependency direction runs one way.
"""

from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

__all__ = ["DATA_DIR"]
