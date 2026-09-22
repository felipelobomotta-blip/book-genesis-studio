"""Prove a bundle carries the continuity fix, instead of assuming a rebuild did it.

The old bundle predated the fix, so "I rebuilt it" is not evidence. This reads the
compiled runner.chapter out of the executable's PYZ archive and walks every nested
code object looking for a string that exists only in the fixed code path. Run it
against the old bundle too: the answer must differ, or the check proves nothing.
"""

import sys
from types import CodeType

from PyInstaller.archive.readers import CArchiveReader, ZlibArchiveReader

NEEDLE = "previous canonical text is preserved"


def strings(code: CodeType):
    for const in code.co_consts:
        if isinstance(const, str):
            yield const
        elif isinstance(const, CodeType):
            yield from strings(const)


exe = sys.argv[1]
archive = CArchiveReader(exe)
pyz_name = next(n for n in archive.toc if n.lower().endswith(".pyz"))
open("_pyz.tmp", "wb").write(archive.extract(pyz_name))
code = ZlibArchiveReader("_pyz.tmp").extract("runner.chapter")

found = any(NEEDLE in s for s in strings(code))
print(f"{exe}: runner.chapter present, fix string {'PRESENT' if found else 'ABSENT'}")
sys.exit(0 if found else 1)
