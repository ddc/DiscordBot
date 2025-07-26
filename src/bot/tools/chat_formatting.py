"""Discord chat formatting utilities with emojis and text styling."""

from typing import Final

# Discord emoji constants
NO_ENTRY: Final[str] = ":no_entry:"
WARNING_SIGN: Final[str] = ":warning:"
INFORMATION_SOURCE: Final[str] = ":grey_exclamation:"
QUESTION_MARK: Final[str] = ":question:"
SAD_FACE: Final[str] = ":frowning2:"
ROBOT: Final[str] = ":robot:"


def error_inline(text: str) -> str:
    """Format text as an inline error with emoji."""
    return f"{NO_ENTRY}\n`{text}`"


def error(text: str) -> str:
    """Format text as an error with emoji."""
    return f"{NO_ENTRY}\n{text}"


def warning_inline(text: str) -> str:
    """Format text as an inline warning with emoji."""
    return f"{WARNING_SIGN}\n`{text}`"


def warning(text: str) -> str:
    """Format text as a warning with emoji."""
    return f"{WARNING_SIGN}\n{text}"


def info_inline(text: str) -> str:
    """Format text as inline information with emoji."""
    return f"{INFORMATION_SOURCE}\n`{text}`"


def info(text: str) -> str:
    """Format text as information with emoji."""
    return f"{INFORMATION_SOURCE}\n{text}"


def question_inline(text: str) -> str:
    """Format text as an inline question with emoji."""
    return f"{QUESTION_MARK}\n`{text}`"


def question(text: str) -> str:
    """Format text as a question with emoji."""
    return f"{QUESTION_MARK}\n{text}"


def bold(text: str) -> str:
    """Make text bold using Discord markdown."""
    return f"**{text}**"


def box(text: str) -> str:
    """Put text in a code block."""
    return f"```{text}```"


def inline(text: str) -> str:
    """Make text inline code."""
    return f"`{text}`"


def italics(text: str) -> str:
    """Make text italic using Discord markdown."""
    return f"*{text}*"


def strikethrough(text: str) -> str:
    """Add strikethrough to text using Discord markdown."""
    return f"~~{text}~~"


def underline(text: str) -> str:
    """Underline text using Discord markdown."""
    return f"__{text}__"


def green_text(text: str) -> str:
    """Format text with green syntax highlighting."""
    return f"```css\n{text}\n```"


def red_text(text: str) -> str:
    """Format text with red syntax highlighting."""
    return f"```prolog\n{text}\n```"


def orange_text(text: str) -> str:
    """Format text with orange syntax highlighting."""
    return f"```fix\n{text}\n```"
