# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import unicodedata
import sys
if sys.hexversion >= 0x03000000:
    unichr = chr

# Start with an inventory of "gremlins", which are characters from all over
# Unicode that Windows has instead assigned to the control characters
# 0x80-0x9F. We might encounter them in their Unicode forms and have to figure
# out what they were originally.

WINDOWS_1252_GREMLINS = [
    # adapted from http://effbot.org/zone/unicode-gremlins.htm
    0x0152,  # LATIN CAPITAL LIGATURE OE
    0x0153,  # LATIN SMALL LIGATURE OE
    0x0160,  # LATIN CAPITAL LETTER S WITH CARON
    0x0161,  # LATIN SMALL LETTER S WITH CARON
    0x0178,  # LATIN CAPITAL LETTER Y WITH DIAERESIS
    0x017E,  # LATIN SMALL LETTER Z WITH CARON
    0x017D,  # LATIN CAPITAL LETTER Z WITH CARON
    0x0192,  # LATIN SMALL LETTER F WITH HOOK
    0x02C6,  # MODIFIER LETTER CIRCUMFLEX ACCENT
    0x02DC,  # SMALL TILDE
    0x2013,  # EN DASH
    0x2014,  # EM DASH
    0x201A,  # SINGLE LOW-9 QUOTATION MARK
    0x201C,  # LEFT DOUBLE QUOTATION MARK
    0x201D,  # RIGHT DOUBLE QUOTATION MARK
    0x201E,  # DOUBLE LOW-9 QUOTATION MARK
    0x2018,  # LEFT SINGLE QUOTATION MARK
    0x2019,  # RIGHT SINGLE QUOTATION MARK
    0x2020,  # DAGGER
    0x2021,  # DOUBLE DAGGER
    0x2022,  # BULLET
    0x2026,  # HORIZONTAL ELLIPSIS
    0x2030,  # PER MILLE SIGN
    0x2039,  # SINGLE LEFT-POINTING ANGLE QUOTATION MARK
    0x203A,  # SINGLE RIGHT-POINTING ANGLE QUOTATION MARK
    0x20AC,  # EURO SIGN
    0x2122,  # TRADE MARK SIGN
]

# a list of Unicode characters that might appear in Windows-1252 text
WINDOWS_1252_CODEPOINTS = list(range(256)) + WINDOWS_1252_GREMLINS

# Rank the characters typically represented by a single byte -- that is, in
# Latin-1 or Windows-1252 -- by how weird it would be to see them in running
# text.
#
#   0 = not weird at all
#   1 = rare punctuation or rare letter that someone could certainly
#       have a good reason to use. All Windows-1252 gremlins are at least
#       weirdness 1.
#   2 = things that probably don't appear next to letters or other
#       symbols, such as math or currency symbols
#   3 = obscure symbols that nobody would go out of their way to use
#       (includes symbols that were replaced in ISO-8859-15)
#   4 = why would you use this?
#   5 = unprintable control character
#
# The Portuguese letter Ã (0xc3) is marked as weird because it would usually
# appear in the middle of a word in actual Portuguese, and meanwhile it
# appears in the mis-encodings of many common characters.

SINGLE_BYTE_WEIRDNESS = (
#   0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
    5, 5, 5, 5, 5, 5, 5, 5, 5, 0, 0, 5, 5, 5, 5, 5,  # 0x00
    5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5,  # 0x10
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  # 0x20
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  # 0x30
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  # 0x40
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  # 0x50
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  # 0x60
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5,  # 0x70
    2, 5, 1, 4, 1, 1, 3, 3, 4, 3, 1, 1, 1, 5, 1, 5,  # 0x80
    5, 1, 1, 1, 1, 3, 1, 1, 4, 1, 1, 1, 1, 5, 1, 1,  # 0x90
    1, 0, 2, 2, 3, 2, 4, 2, 4, 2, 2, 0, 3, 1, 1, 4,  # 0xa0
    2, 2, 3, 3, 4, 3, 3, 2, 4, 4, 4, 0, 3, 3, 3, 0,  # 0xb0
    0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  # 0xc0
    1, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0,  # 0xd0
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  # 0xe0
    1, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0,  # 0xf0
)

# Pre-cache the Unicode data saying which of these first 256 characters are
# letters. We'll need it often.
SINGLE_BYTE_LETTERS = [
    unicodedata.category(unichr(i)).startswith('L')
    for i in range(256)
]

# Create a fast mapping that converts a Unicode string to a string describing
# its character classes, particularly the scripts its letters are in.
#
# Capital letters represent groups of commonly-used scripts:
#   L = Latin
#   E = several East Asian scripts including hanzi, kana, and Hangul
#   C = Cyrillic
#   etc.
#
# Lowercase letters represent rare scripts.
# . represents non-letters.
# Whitespace represents whitespace.
# ? represents errors.
#
# Astral characters pass through unmodified; we don't count them as script
# conflicts. They are probably intentional.

SCRIPT_LETTERS = {
    'LATIN': 'L',
    'CJK': 'E',
    'ARABIC': 'A',
    'CYRILLIC': 'C',
    'GREEK': 'G',
    'HEBREW': 'H',
    'KATAKANA': 'E',
    'HIRAGANA': 'E',
    'HIRAGANA-KATAKANA': 'E',
    'HANGUL': 'E',
    'DEVANAGARI': 'D',
    'THAI': 'T',
    'FULLWIDTH': 'E',
    'MASCULINE': 'L',
    'FEMININE': 'L',
    'MODIFIER': '.',
    'HALFWIDTH': 'E',
    'BENGALI': 'b',
    'LAO': 'l',
    'KHMER': 'k',
    'TELUGU': 't',
    'MALAYALAM': 'm',
    'SINHALA': 's',
    'TAMIL': 'a',
    'GEORGIAN': 'g',
    'ARMENIAN': 'r',
    'KANNADA': 'n',  # mostly used for looks of disapproval
}


SCRIPT_MAP = {}

for codepoint in range(0x10000):
    char = unichr(codepoint)
    if unicodedata.category(char).startswith('L'):
        try:
            name = unicodedata.name(char)
            script = name.split()[0]
            if script in SCRIPT_LETTERS:
                SCRIPT_MAP[codepoint] = SCRIPT_LETTERS[script]
            else:
                SCRIPT_MAP[codepoint] = 'z'
        except ValueError:
            # it's unfortunate that this gives subtly different results
            # on Python 2.6, which is confused about the Unicode 5.1
            # Chinese range. It knows they're letters but it has no idea
            # what they are named.
            #
            # This could be something to fix in the future, or maybe we
            # just stop supporting Python 2.6 eventually.
            SCRIPT_MAP[codepoint] = 'z'
    elif unicodedata.category(char).startswith('Z'):
        SCRIPT_MAP[codepoint] = ' '
    elif unicodedata.category(char) in ('Cn', 'Co'):
        SCRIPT_MAP[codepoint] = '?'
    else:
        SCRIPT_MAP[codepoint] = '.'

SCRIPT_MAP[0x09] = ' '
SCRIPT_MAP[0x0a] = '\n'
SCRIPT_MAP[0xfffd] = '?'

# mark weird extended characters as their own script
for codepoint in range(0x100):
    if SINGLE_BYTE_WEIRDNESS[codepoint] >= 2:
        SCRIPT_MAP[codepoint] = 'W'

# A translate mapping that will strip all control characters except \t and \n.
# This incidentally has the effect of normalizing Windows \r\n line endings to
# Unix \n line endings.
CONTROL_CHARS = {}
for i in range(256):
    if unicodedata.category(unichr(i)) == 'Cc':
        CONTROL_CHARS[i] = None

CONTROL_CHARS[ord('\t')] = '\t'
CONTROL_CHARS[ord('\n')] = '\n'
