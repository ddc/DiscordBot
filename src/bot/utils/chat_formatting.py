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


def pagify(text, delims=["\n"], *, escape=True, shorten_by=8,
           page_length=2000):
    """DOES NOT RESPECT MARKDOWN BOXES OR INLINE CODE"""
    in_text = text
    if escape:
        num_mentions = text.count("@here") + text.count("@everyone")
        shorten_by += num_mentions
    page_length -= shorten_by
    while len(in_text) > page_length:
        closest_delim = max([in_text.rfind(d, 0, page_length)
                             for d in delims])
        closest_delim = closest_delim if closest_delim != -1 else page_length
        if escape:
            to_send = escape_mass_mentions(in_text[:closest_delim])
        else:
            to_send = in_text[:closest_delim]
        yield to_send
        in_text = in_text[closest_delim:]

    if escape:
        yield escape_mass_mentions(in_text)
    else:
        yield in_text


def escape_mass_mentions(text):
    return _escape(text, mass_mentions=True)


def _escape(text, *, mass_mentions=False, formatting=False):
    if mass_mentions:
        text = text.replace("@everyone", "@\u200beveryone")
        text = text.replace("@here", "@\u200bhere")
    if formatting:
        text = (text.replace("`", "\\`")
                .replace("*", "\\*")
                .replace("_", "\\_")
                .replace("~", "\\~"))
    return text
