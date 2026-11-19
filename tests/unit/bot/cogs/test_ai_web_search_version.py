"""Fails when the installed anthropic SDK ships a newer web search tool than the bot uses."""

import anthropic.types
import re
from src.bot.cogs import ai
from src.bot.constants import variables

_PARAM_NAME = re.compile(r"^WebSearchTool(\d{8})Param$")


def _dates(names) -> list[str]:
    return sorted(m.group(1) for name in names if (m := _PARAM_NAME.match(name)))


def test_bot_uses_newest_web_search_tool_in_installed_sdk():
    newest = _dates(dir(anthropic.types))[-1]
    used = variables.ANTHROPIC_WEB_SEARCH_TOOL.removeprefix("web_search_")
    assert used == newest, (
        f"anthropic SDK has web_search_{newest}, bot uses web_search_{used}. Read the changelog entry "
        "(https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool), then update "
        "ANTHROPIC_WEB_SEARCH_TOOL and ANTHROPIC_WEB_SEARCH_TOOL_PARAM in src/bot/constants/variables.py."
    )


def test_type_alias_matches_configured_web_search_tool():
    date = variables.ANTHROPIC_WEB_SEARCH_TOOL.removeprefix("web_search_")
    assert variables.ANTHROPIC_WEB_SEARCH_TOOL_PARAM.__name__ == f"WebSearchTool{date}Param"


def test_cog_does_not_pin_its_own_web_search_version():
    assert _dates(vars(ai)) == []
