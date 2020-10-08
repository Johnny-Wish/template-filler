import string


def capitalize(s: str):
    if not isinstance(s, str):
        raise ValueError(f"expected str, but got {type(s)} instead")
    if len(s) == 0:
        return s
    if s[0] in string.ascii_lowercase:
        return s[0].upper() + s[1:]
    return s
