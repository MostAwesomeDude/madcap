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
