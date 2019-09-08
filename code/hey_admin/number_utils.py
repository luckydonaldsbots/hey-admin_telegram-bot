from math import floor, log10
from typing import Union


def num_length(number: int) -> int:
    """
    Gets the length of a number.
    Negative and positive numbers have the same length, i.e. the sign is not taken into account.
    Only works with integers, not floats.

    Example: Negative `-100` and positive `100` both have the length of `3`.

    :param number: Number to calculate the length of.
    :return: the count of digits.
    """
    return floor(log10(abs(number))) + 1
# end def


def num_substring_start(number: int, length: int) -> int:
    delete_n_from_end = num_length(number) - length
    return int(number / 10 ** delete_n_from_end)
# end def


def from_supergroup(number: int, length: int) -> int:
    number = number * -1  # turn positive
    return number - 10 ** int(floor(log10(number)))
# end def


# https://github.com/tdlib/td/blob/56163c2460a65afc4db2c57ece576b8c38ea194b/td/telegram/DialogId.h#L27-L33
MIN_SECRET_ID = -2002147483648
# ZERO_SECRET_ID = -2000000000000
MAX_SECRET_ID = -1997852516353
MIN_CHANNEL_ID = -1002147483647
MAX_CHANNEL_ID = -1000000000000
MIN_CHAT_ID = -2147483647
MAX_USER_ID = 2147483647


def type_from_id(chat_id: int) -> Union[None, str]:
    # https://github.com/tdlib/td/blob/56163c2460a65afc4db2c57ece576b8c38ea194b/td/telegram/DialogId.cpp#L37-L52
    if chat_id >= 0:
        if 0 < chat_id <= MAX_USER_ID:
            return "private"
        # end if
        return None
    # end if
    if MIN_CHAT_ID <= chat_id:
        return "group"
    elif MIN_CHANNEL_ID <= chat_id < MAX_CHANNEL_ID:
        return "supergroup/channel"
    elif MIN_SECRET_ID <= chat_id < MAX_SECRET_ID:
        return "secret"
    # end if
# end def


def num_startswith(number: int, start: int) -> bool:
    start_n_digits = num_length(start)
    return num_substring_start(number, start_n_digits) == start
# end def
