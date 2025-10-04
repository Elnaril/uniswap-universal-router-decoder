"""Core functions for Unicode normalization.

This module provides the main functions for applying the four Unicode
normalization forms: NFC, NFD, NFKC, and NFKD. It relies on data files
from the Unicode character database (UCD) associated with version 17.0
of the Unicode Standard. As a result, the module can only fully handle
the characters defined in version 17.0 and produces results consistent
with the definitions and rules of that version.
"""

from pyunormalize._unicode_data import (
    _COMPOSITION_EXCLUSIONS,
    _DECOMP_BY_CHARACTER,
    _NFC__QC_NO_OR_MAYBE,
    _NFD__QC_NO,
    _NFKC_QC_NO_OR_MAYBE,
    _NFKD_QC_NO,
    _NON_ZERO_CCC_TABLE as _CCC,
)

# Hangul syllables for modern Korean
_SB = 0xAC00
_SL = 0xD7A3

# Hangul leading consonants (syllable onsets)
_LB = 0x1100
_LL = 0x1112

# Hangul vowels (syllable nucleuses)
_VB = 0x1161
_VL = 0x1175

# Hangul trailing consonants (syllable codas)
_TB = 0x11A8
_TL = 0x11C2

# Number of Hangul vowels
_VCOUNT = 21

# Number of Hangul trailing consonants,
# with the additional case of no trailing consonant
_TCOUNT = 27 + 1

# Cache for full decompositions
_SHARED_FULL_DECOMP_CACHE = {}

# Note: Hangul syllables are excluded from the following three normalization
# tables, as their compositions and decompositions are handled algorithmically
# in code.

# Dictionary mapping canonical decompositions to their precomposed character
_COMPOSITE_BY_CDECOMP = {}

# Dictionary mapping characters to their full canonical decomposition
_FULL_CDECOMP_BY_CHAR = {}

# Dictionary mapping characters to their full compatibility decomposition
_FULL_KDECOMP_BY_CHAR = {}


def _compute_full_decompositions(decomp_dict):
    # Compute the full decomposition for every code point in the provided
    # dictionary. The process repeatedly decomposes each code point using
    # the dictionary until no further decomposition is possible, storing
    # the final sequence of code points. The provided dictionary is updated
    # in place. The shared cache is used to avoid recomputing common
    # sub-decompositions, allowing results from canonical decomposition
    # to be reused immediately for compatibility decomposition.

    for key in decomp_dict:
        decomposition = [key]

        while decomposition:
            next_decomp = []

            for k in decomposition:
                if k in _SHARED_FULL_DECOMP_CACHE:
                    next_decomp.extend(_SHARED_FULL_DECOMP_CACHE[k])
                elif k in decomp_dict:
                    next_decomp.extend(decomp_dict[k])
                else:
                    next_decomp.append(k)

            if next_decomp == decomposition:
                # No further decomposition possible, we reached a stable form
                break

            decomposition = next_decomp

        # Update dictionary in place
        decomp_dict[key] = _SHARED_FULL_DECOMP_CACHE[key] = decomposition


def _init_normalization_tables():
    for key, val in _DECOMP_BY_CHARACTER.items():
        if isinstance(val[0], int):
            if len(val) == 2 and val[0] not in _CCC:
                _COMPOSITE_BY_CDECOMP[tuple(val)] = key

            _FULL_CDECOMP_BY_CHAR[key] = _FULL_KDECOMP_BY_CHAR[key] = val

        else:
            _FULL_KDECOMP_BY_CHAR[key] = val[1:]

    # Compute full canonical decompositions first, which populates the cache
    # with base sequences, a subset of the compatibility sequences
    _compute_full_decompositions(_FULL_CDECOMP_BY_CHAR)

    # Then compute full compatibility decompositions, leveraging the existing
    # cache for a performance gain
    _compute_full_decompositions(_FULL_KDECOMP_BY_CHAR)


# Initialize normalization tables
_init_normalization_tables()


del _DECOMP_BY_CHARACTER, _SHARED_FULL_DECOMP_CACHE


def _quick_check(string, quick_check_set):
    # Check if the string is already normalized to the target form (NFC, NFD,
    # NFKC, or NFKD). The normalization form checked is determined by the
    # specific set of code points provided.

    prev_ccc = 0

    for char in string:
        cp = ord(char)

        if cp in quick_check_set:
            return False

        if cp not in _CCC:
            continue

        if (curr_ccc := _CCC[cp]) < prev_ccc:
            return False

        prev_ccc = curr_ccc

    return True


def _decompose_hangul_syllable(cp):
    # Decompose a precomposed Hangul syllable into its constituent jamo
    # characters using the canonical Hangul decomposition algorithm.

    sindex = cp - _SB
    tindex = sindex % _TCOUNT
    q = (sindex - tindex) // _TCOUNT
    V = _VB + (q  % _VCOUNT)
    L = _LB + (q // _VCOUNT)

    if tindex:
        return (L, V, _TB - 1 + tindex)  # LVT syllable

    return (L, V)  # LV syllable


def _compose_hangul_syllable(cp, next_cp):
    # This function attempts to compose a sequence of Hangul characters into
    # a single syllable using the specialized Hangul composition algorithm. It
    # returns the new syllable's code point on success, or `None` if the pair
    # of code points does not form a valid Hangul composition. The composition
    # logic only applies to two specific scenarios: a leading consonant (L)
    # is combined with a vowel (V), and in this case `cp` is L and `next_cp`
    # is V; or a precomposed LV syllable is combined with a trailing
    # consonant (T), and `cp` is then the LV syllable and `next_cp` is T.

    if _LB <= cp <= _LL and _VB <= next_cp <= _VL:
        # Compose a leading consonant and a vowel into an LV syllable
        return _SB + (((cp - _LB) * _VCOUNT) + next_cp - _VB) * _TCOUNT

    if (
        _SB <= cp <= _SL
        and not (cp - _SB) % _TCOUNT
        and _TB <= next_cp <= _TL
    ):
        # Compose an LV syllable and a trailing consonant into an LVT syllable
        return cp + next_cp - (_TB - 1)

    # Composition did not take place
    return None


def _reorder(codepoints):
    # Apply the canonical ordering algorithm to a fully decomposed string,
    # arranging combining marks with a non-zero combining class value in
    # a well-defined order. This ensures the uniqueness of normalization forms.

    size = len(codepoints)

    # Outer loop: optimized bubble sort, runs as long as swaps occur
    while size > 1:
        swap_pos = 0

        i = 1
        while i < size:

            curr = codepoints[i]

            # Block check: if the current character is a starter (ccc is 0),
            # it acts as a blocker, and no reordering can happen across it
            if curr not in _CCC:
                i += 2  # optimized skip: jump past the character after `curr`
                continue

            prev = codepoints[i - 1]

            # Reordering rule: order is correct if the previous character
            # is a starter or if ccc(prev) is less than or equal to ccc(curr)
            if prev not in _CCC or _CCC[prev] <= _CCC[curr]:
                i += 1
                continue

            # Swap adjacent combining marks to enforce canonical order
            codepoints[i - 1], codepoints[i] = codepoints[i], codepoints[i - 1]

            swap_pos = i
            i += 1

        # Shrink the scope of the sort to the position of the last swap
        size = swap_pos

    return "".join(map(chr, codepoints))


def _decompose(string, *, compatibility=False):
    # Perform full decomposition of the input string. Canonical decomposition
    # is used for NFC/NFD, and compatibility decomposition for NFKC/NFKD.

    codepoints = []
    decomp = _FULL_KDECOMP_BY_CHAR if compatibility else _FULL_CDECOMP_BY_CHAR

    for cp in map(ord, string):
        if cp in decomp:
            codepoints.extend(decomp[cp])
        elif _SB <= cp <= _SL:
            codepoints.extend(_decompose_hangul_syllable(cp))
        else:
            codepoints.append(cp)

    return codepoints


def _compose(string):
    # Apply the canonical composition algorithm, transforming the fully
    # decomposed and canonically ordered string into its most fully composed
    # but still canonically equivalent sequence.

    codepoints = [*map(ord, string)]

    # Iterate through the code points to find a base character for composition
    for i, cp in enumerate(codepoints):

        # Skip if consumed (`None`) or if it is a combining mark (not a base)
        if cp is None or cp in _CCC:
            continue

        # Flags to control composition rules
        is_blocked = False
        last_is_combining = False

        # Try to compose the base character with following combining marks
        for j, next_cp in enumerate(codepoints[i + 1 :], i + 1):
            if next_cp in _CCC:
                # Current character is a combining mark
                last_is_combining = True
            else:
                # A non-combining character blocks further compositions
                is_blocked = True

            if is_blocked and last_is_combining:
                # Skip: composition is blocked by intervening characters
                continue

            prev_cp = codepoints[j - 1]

            # Check if composition is allowed by canonical ordering
            if (
                prev_cp is None
                or prev_cp not in _CCC
                or _CCC[prev_cp] < _CCC[next_cp]
            ):
                pair = (cp, next_cp)

                if pair in _COMPOSITE_BY_CDECOMP:
                    # Found a precomposed form in the lookup table
                    precomposed_char = _COMPOSITE_BY_CDECOMP[pair]
                else:
                    # Check if the composition pair can be composed using
                    # the Hangul algorithm
                    precomposed_char = _compose_hangul_syllable(*pair)

                # Accept only if a valid precomposed character exists
                # and it is not excluded from composition
                if (
                    precomposed_char
                    and precomposed_char not in _COMPOSITION_EXCLUSIONS
                ):
                    codepoints[j] = None  # flag combining mark as consumed

                    # Update base character to the new precomposed one
                    codepoints[i] = cp = precomposed_char

                    # Reset flags depending on composition state
                    if is_blocked:
                        is_blocked = False
                    else:
                        last_is_combining = False

                else:
                    # No valid composition: stop scanning this base
                    if is_blocked:
                        break

    return "".join(map(chr, filter(None, codepoints)))


def NFD(string):
    """Return the normalization form D of the input string.

    Replaces composed characters with their canonically equivalent decomposed
    forms in canonical order, while leaving compatibility characters
    unaffected.

    The function first checks if the input is already in NFD. If so, it returns
    the string unchanged to avoid unnecessary processing.

    Args:
        string (str): The string to be normalized.

    Returns:
        str: The NFD string.

    Examples:
        # Decomposing accented characters
        >>> string = "élève"
        >>> nfd = NFD(string)
        >>> nfd
        'élève'
        >>> nfd != string  # binary content differs
        True
        >>> " ".join([f"{ord(c):04X}" for c in string])
        '00E9 006C 00E8 0076 0065'
        >>> " ".join([f"{ord(c):04X}" for c in nfd])
        '0065 0301 006C 0065 0300 0076 0065'

        # Decomposing Hangul syllables
        >>> string = "한국"
        >>> nfd = NFD(string)
        >>> nfd
        '한국'
        >>> " ".join([f"{ord(c):04X}" for c in string])
        'D55C AD6D'
        >>> " ".join([f"{ord(c):04X}" for c in nfd])
        '1112 1161 11AB 1100 116E 11A8'

        # Compatibility characters are unaffected
        >>> strings = ["ﬃ", "⑴", "²", "ｱｲｳｴｵ"]
        >>> all(NFD(s) == s for s in strings)
        True
    """
    if _quick_check(string, _NFD__QC_NO):
        return string
    return _reorder(_decompose(string))


def NFKD(string):
    """Return the normalization form KD of the input string.

    Replaces composed characters with their canonically equivalent decomposed
    forms in canonical order and converts compatibility characters into their
    nominal counterparts.

    The function first checks if the input is already in NFKD. If so, it
    returns the string unchanged to avoid unnecessary processing.

    Args:
        string (str): The string to be normalized.

    Returns:
        str: The NFKD string.

    Examples:
        # NFKD decomposes canonically composed forms
        >>> NFKD("\u00E9l\u00E8ve") == "e\u0301le\u0300ve"
        True

        # NFKD converts compatibility characters
        >>> [NFKD(s) for s in ["ﬃ", "⑴", "²", "ｱｲｳｴｵ"]]
        ['ffi', '(1)', '2', 'アイウエオ']
    """
    if _quick_check(string, _NFKD_QC_NO):
        return string
    return _reorder(_decompose(string, compatibility=True))


def NFC(string):
    """Return the normalization form C of the input string.

    Replaces character sequences with their canonically equivalent composed
    forms whenever possible, while leaving compatibility characters unaffected.

    The function first checks if the input is already in NFC. If so, it returns
    the string unchanged to avoid unnecessary processing.

    Args:
        string (str): The string to be normalized.

    Returns:
        str: The NFC string.

    Examples:
        # Composing accented characters
        >>> string = "élève"
        >>> nfc = NFC(string)
        >>> nfc
        'élève'
        >>> nfc != string  # binary content differs
        True
        >>> " ".join([f"{ord(c):04X}" for c in string])
        '0065 0301 006C 0065 0300 0076 0065'
        >>> " ".join([f"{ord(c):04X}" for c in nfc])
        '00E9 006C 00E8 0076 0065'

        # Composing Hangul syllables
        >>> string = "한국"
        >>> nfc = NFC(string)
        >>> nfc
        '한국'
        >>> " ".join([f"{ord(c):04X}" for c in string])
        '1112 1161 11AB 1100 116E 11A8'
        >>> " ".join([f"{ord(c):04X}" for c in nfc])
        'D55C AD6D'

        # Compatibility characters are unaffected
        >>> strings = ["ﬃ", "⑴", "²", "ｱｲｳｴｵ"]
        >>> all(NFC(s) == s for s in strings)
        True
    """
    if _quick_check(string, _NFC__QC_NO_OR_MAYBE):
        return string
    return _compose(NFD(string))


def NFKC(string):
    """Return the normalization form KC of the input string.

    Replaces character sequences with their canonically equivalent composed
    forms whenever possible and converts compatibility characters into their
    nominal counterparts.

    The function first checks if the input is already in NFKC. If so, it
    returns the string unchanged to avoid unnecessary processing.

    Args:
        string (str): The string to be normalized.

    Returns:
        str: The NFKC string.

    Examples:
        # NFKC composes canonically decomposed forms
        >>> NFKC("e\u0301le\u0300ve") == "\u00E9l\u00E8ve"
        True

        # NFKC converts compatibility characters
        >>> [NFKC(s) for s in ["ﬃ", "⑴", "²", "ｱｲｳｴｵ"]]
        ['ffi', '(1)', '2', 'アイウエオ']
    """
    if _quick_check(string, _NFKC_QC_NO_OR_MAYBE):
        return string
    return _compose(NFKD(string))


# Dictionary for normalization forms dispatch
_NORMALIZATION_FORMS = {"NFC": NFC, "NFD": NFD, "NFKC": NFKC, "NFKD": NFKD}


def normalize(form, string):
    """Return the normalized form of the input string as specified by `form`.

    This function transforms the input string according to the normalization
    form given in `form`. Supported values are "NFC", "NFD", "NFKC",
    and "NFKD".

    Args:
        form (str): The normalization form to apply, one of "NFC", "NFD",
            "NFKC", or "NFKD".

        string (str): The string to be normalized.

    Returns:
        str: The normalized string.

    Examples:
        >>> normalize("NFKD", "ﬂuﬃness")
        'fluffiness'

        >>> forms = ["NFC", "NFD", "NFKC", "NFKD"]
        >>> string = "\u1E9B\u0323"
        >>> def hexpoints(s):
        ...     return " ".join([f"{ord(c):04X}" for c in s])
        >>> [hexpoints(normalize(f, string)) for f in forms]
        ['1E9B 0323', '017F 0323 0307', '1E69', '0073 0323 0307']
    """
    return _NORMALIZATION_FORMS[form](string)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
