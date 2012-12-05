from base64 import b32decode, b32encode


def b32d(s):
    """
    Decode a base32 string, repairing padding if necessary.
    """

    if len(s) % 8:
        s = s.ljust((len(s) // 8 + 1) * 8, "=")
    return b32decode(s)


def b32e(s):
    """
    Encode a base32 string, stripping padding.
    """

    return b32encode(s).rstrip("=")


class EscapeError(Exception):
    """
    A string could not be unescaped due to an incorrect escape sequence.
    """


def escape(s):
    """
    Escape a string.
    """

    return s.replace("\\", "\\\\").replace("\n", "\\n").replace(" ", "\\s")


def unescape(s):
    """
    Undo escape sequences.
    """

    rv = ""
    i = iter(s)
    for char in i:
        if char == '\\':
            n = next(i)
            if n == 's':
                rv += ' '
            elif n == 'n':
                rv += '\n'
            elif n == '\\':
                rv += '\\'
            else:
                raise EscapeError("Incorrect escape character %r" % n)
        else:
            rv += char

    return rv
