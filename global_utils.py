import datetime
import string


def capitalize(s: str):
    if not isinstance(s, str):
        raise ValueError(f"expected str, but got {type(s)} instead")
    if len(s) == 0:
        return s
    if s[0] in string.ascii_lowercase:
        return s[0].upper() + s[1:]
    return s


def rreplace(s, old, new, max_replace=1):
    return new.join(s.rsplit(old, max_replace))


def get_timestamp_str():
    return str(datetime.datetime.now().timestamp()).replace(".", "")


def get_time_str():
    return str(datetime.datetime.now().strftime("20%y-%m-%d-%H-%M-%S"))
