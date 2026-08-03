"""What another scheme calls a psalm of this spine.

Ported as it stands from the working implementation, which returns a string
because the answer is sometimes a range. The Vulgate psalm 9 is 9 and 10
elsewhere, and 114 and 115 are both 116.

Not derivable from the text, which carries no chapter numbers, and not
arithmetic. The offset runs 0, then +1 from psalm 10, then +2 at 114, then +1
from 115, and back to 0 at 147. Twelve psalms carry the same number in both.

B1's `to_scheme` computes the same answer from the Copenhagen table and the two
agree on all 150. They disagreed on two until issue #22, where `to_scheme` could
not see that a candidate was out of range in the target scheme. Kept as a second
independent statement, and a test compares them psalm by psalm.
"""

from __future__ import annotations

# The exceptions. Everything else follows the ranges below.
_HEBREW = {
    9: "9-10",  # merged, this psalm 9 is 9 and 10 elsewhere
    113: "114-115",  # split, this psalm 113 is 114 and 115 elsewhere
    114: "116",  # 114 and 115 are both 116
    115: "116",
    146: "147",  # 146 and 147 are both 147
    147: "147",
}


def counterpart(psalm: int) -> str:
    """The `org` number for a psalm numbered on this spine."""
    if psalm in _HEBREW:
        return _HEBREW[psalm]
    if 10 <= psalm <= 112 or 116 <= psalm <= 145:
        return str(psalm + 1)
    return str(psalm)


def differs(psalm: int) -> bool:
    return counterpart(psalm) != str(psalm)
