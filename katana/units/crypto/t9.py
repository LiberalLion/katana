"""
T9 Phone keypad Cipher 

This unit will decode a T9 cipher and look for flags.
This code relies on there being spaces between the T9 ciphers. 
It can be made cleaner with some regular expression processing, but it
has not yet been done...
"""

import regex as re
from typing import Any

from katana.unit import RegexUnit
from katana.units.crypto import CryptoUnit

# JOHN: I do NOT use a dictionary for this, because the sorting and order would
#       get all messed up, Instead, a force an ordered list.
t9_mappings = {
    b"7777": b"s",
    b"9999": b"z",
    b"222": b"c",
    b"111": b"@",
    b"333": b"f",
    b"444": b"i",
    b"555": b"l",
    b"666": b"o",
    b"777": b"r",
    b"888": b"v",
    b"999": b"y",
    b"22": b"b",
    b"33": b"e",
    b"44": b"h",
    b"55": b"k",
    b"66": b"n",
    b"77": b"q",
    b"88": b"u",
    b"99": b"x",
    b"11": b":",
    b"2": b"a",
    b"3": b"d",
    b"4": b"g",
    b"5": b"j",
    b"6": b"m",
    b"7": b"p",
    b"8": b"t",
    b"9": b"w",
    b"1": b"_",
    b"0": b" ",
    b"*": b" ",
}


class Unit(RegexUnit, CryptoUnit):

    GROUPS = ["crypto", "t9"]
    """
    These are "tags" for a unit. Considering it is a Crypto unit, "crypto"
    is included, and the name of the unit, "t9".
    """

    BLOCKED_GROUPS = ["crypto"]
    """
    These are tags for groups to not recurse into. Recursing into other crypto units
    would be silly.
    """

    PRIORITY = 50
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a defualt
    priority.
    """

    RECURSE_SELF = False
    """
    Do not recurse into self
    """

    # Regular expression pattern to match
    PATTERN = re.compile(rb"[0-9*]+(\w([0-9*]+))*")

    def decode_one(self, number):
        result = []

        token = b""
        for c in number:
            if token + bytes([c]) in t9_mappings:
                token += bytes([c])

            elif token in t9_mappings:
                result.append(t9_mappings[token])
                token = bytes([c])
            else:
                token += bytes([c])
        if token in t9_mappings:
            result.append(t9_mappings[token])

        return b"".join(result)

    def evaluate(self, match):

        # Grab the groups and split them on whitespace
        matches = match.group().split()

        result = [self.decode_one(m) for m in matches]
        # Register with and without spaces separating
        self.manager.register_data(self, b"".join(result))
        self.manager.register_data(self, b" ".join(result))
