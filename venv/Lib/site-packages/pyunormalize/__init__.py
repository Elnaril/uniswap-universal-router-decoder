"""Unicode normalization.

This is a pure-Python implementation of the Unicode normalization algorithm.
Because it relies on data files from the Unicode character database (UCD)
associated with version 17.0 of the Unicode Standard, it is independent
of Python's core Unicode database. This approach ensures strict compliance
with the definitions and rules of that version, released in September 2025.

Copyright (c) 2021-2025, Marc Lodewijck
All rights reserved.

The code is available under the terms of the MIT license.
"""

__all__ = [
    "NFC",
    "NFD",
    "NFKC",
    "NFKD",
    "normalize",
    "UCD_VERSION",
    "UNICODE_VERSION",
    "__version__",
]

# Unicode Standard used to process the data
UNICODE_VERSION = UCD_VERSION = "17.0.0"

from pyunormalize import _version

__version__ = _version.__version__
del _version

from pyunormalize._unicode_data import _UNICODE_VERSION

if _UNICODE_VERSION != UNICODE_VERSION:
    raise RuntimeError(
        f"Unicode version mismatch in '_unicode_data' "
        f"(expected {UNICODE_VERSION!r}, found {_UNICODE_VERSION!r})"
    )

del _UNICODE_VERSION

from pyunormalize.normalization import *
