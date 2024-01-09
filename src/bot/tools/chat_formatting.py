# -*- coding: utf-8 -*-
NO_ENTRY = ":no_entry:"
WARNING_SIGN = ":warning:"
INFORMATION_SOURCE = ":grey_exclamation:"
QUESTION_MARK = ":question:"
SAD_FACE = ":frowning2:"
ROBOT = ":robot:"


def error_inline(text):
    return f"{NO_ENTRY}\n`{text}`"


def error(text):
    return f"{NO_ENTRY}\n{text}"


def warning_inline(text):
    return f"{WARNING_SIGN}\n`{text}`"


def warning(text):
    return f"{WARNING_SIGN}\n{text}"


def info_inline(text):
    return f"{INFORMATION_SOURCE}\n`{text}`"


def info(text):
    return f"{INFORMATION_SOURCE}\n{text}"


def question_inline(text):
    return f"{QUESTION_MARK}\n`{text}`"


def question(text):
    return f"{QUESTION_MARK}\n{text}"


def bold(text):
    return f"**{text}**"


def box(text):
    return f"```{text}```"


def inline(text):
    return f"`{text}`"


def italics(text):
    return f"*{text}*"


def strikethrough(text):
    return f"~~{text}~~"


def underline(text):
    return f"__{text}__"


def green_text(text):
    return f"```css\n{text}\n```"


def red_text(text):
    return f"```prolog\n{text}\n```"


def orange_text(text):
    return f"```fix\n{text}\n```"
