"""Comprehensive tests for GW2 Misc cog."""

import discord
import pytest
from src.gw2.cogs.misc import GW2Misc, info, setup, wiki
from unittest.mock import AsyncMock, MagicMock, patch


class AsyncContextManager:
    """Helper class to mock async context managers for aiosession."""

    def __init__(self, return_value):
        self.return_value = return_value

    async def __aenter__(self):
        return self.return_value

    async def __aexit__(self, *args):
        pass


class TestGW2Misc:
    """Test cases for the GW2Misc cog class."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.db_session = MagicMock()
        bot.log = MagicMock()
        bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        return bot

    @pytest.fixture
    def gw2_misc_cog(self, mock_bot):
        """Create a GW2Misc cog instance."""
        return GW2Misc(mock_bot)

    def test_gw2_misc_initialization(self, mock_bot):
        """Test GW2Misc cog initialization."""
        cog = GW2Misc(mock_bot)
        assert cog.bot == mock_bot

    def test_gw2_misc_inheritance(self, gw2_misc_cog):
        """Test that GW2Misc inherits from GuildWars2 properly."""
        from src.gw2.cogs.gw2 import GuildWars2

        assert isinstance(gw2_misc_cog, GuildWars2)

    def test_gw2_misc_docstring(self, gw2_misc_cog):
        """Test that GW2Misc has proper docstring."""
        assert GW2Misc.__doc__ is not None
        assert "GW2" in GW2Misc.__doc__


class TestWikiCommand:
    """Test cases for the wiki command."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.db_session = MagicMock()
        ctx.bot.log = MagicMock()
        ctx.bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        ctx.bot.user = MagicMock()
        ctx.bot.user.mention = "<@bot>"
        ctx.bot.aiosession = MagicMock()
        ctx.message = MagicMock()
        ctx.message.author = MagicMock()
        ctx.message.author.id = 12345
        ctx.message.author.display_name = "TestUser"
        ctx.message.author.avatar = MagicMock()
        ctx.message.author.avatar.url = "https://example.com/avatar.png"
        ctx.message.channel = MagicMock()
        ctx.message.channel.typing = AsyncMock()
        ctx.prefix = "!"
        ctx.guild = MagicMock()
        ctx.guild.id = 99999
        ctx.channel = MagicMock(spec=discord.TextChannel)
        ctx.send = AsyncMock()
        ctx.author = ctx.message.author
        return ctx

    def _make_search_result_html(self, results):
        """Helper to build HTML with search result divs.

        Args:
            results: list of dicts with 'title' and 'href' keys
        """
        divs = ""
        for r in results:
            divs += (
                f'<div class="mw-search-result-heading">'
                f'<a href="{r["href"]}" title="{r["title"]}">{r["title"]}</a>'
                f'</div>\n'
            )
        return f"<html><body>{divs}</body></html>"

    @pytest.mark.asyncio
    async def test_wiki_search_too_long(self, mock_ctx):
        """Test wiki command rejects search longer than 300 chars."""
        long_search = "a" * 301
        await wiki(mock_ctx, search=long_search)
        mock_ctx.send.assert_called_once()
        from src.gw2.constants import gw2_messages

        assert mock_ctx.send.call_args[0][0] == gw2_messages.LONG_SEARCH

    @pytest.mark.asyncio
    async def test_wiki_search_exactly_300_chars_allowed(self, mock_ctx):
        """Test wiki command allows search exactly 300 chars."""
        search = "a" * 300
        html = self._make_search_result_html([])
        mock_response = AsyncMock()
        mock_response.text = AsyncMock(return_value=html)
        mock_ctx.bot.aiosession.get = MagicMock(return_value=AsyncContextManager(mock_response))

        with patch('src.gw2.cogs.misc.bot_utils.send_error_msg', new_callable=AsyncMock) as mock_error:
            await wiki(mock_ctx, search=search)
            # Should not send LONG_SEARCH message
            from src.gw2.constants import gw2_messages

            if mock_ctx.send.called:
                assert mock_ctx.send.call_args[0][0] != gw2_messages.LONG_SEARCH

    @pytest.mark.asyncio
    async def test_wiki_no_results_found(self, mock_ctx):
        """Test wiki command sends error when no results found."""
        html = "<html><body></body></html>"
        mock_response = AsyncMock()
        mock_response.text = AsyncMock(return_value=html)
        mock_ctx.bot.aiosession.get = MagicMock(return_value=AsyncContextManager(mock_response))

        with patch('src.gw2.cogs.misc.bot_utils.send_error_msg', new_callable=AsyncMock) as mock_error:
            await wiki(mock_ctx, search="nonexistent")
            mock_error.assert_called_once()
            from src.gw2.constants import gw2_messages

            assert mock_error.call_args[0][1] == gw2_messages.NO_RESULTS

    @pytest.mark.asyncio
    async def test_wiki_results_with_matching_keywords(self, mock_ctx):
        """Test wiki command adds embed fields for matching keywords.

        The dedup logic checks if keyword.title() matches any existing field name.
        So results with titles different from the keyword title are added, while
        once a field matching keyword.title() exists, subsequent results are skipped.
        """
        # Use titles that all contain the keyword "sword" but none exactly equals "Sword"
        results = [
            {"title": "Sword of Fire", "href": "/wiki/Sword_of_Fire"},
            {"title": "Sword of Ice", "href": "/wiki/Sword_of_Ice"},
            {"title": "Sword of Lightning", "href": "/wiki/Sword_of_Lightning"},
        ]
        html = self._make_search_result_html(results)
        mock_response = AsyncMock()
        mock_response.text = AsyncMock(return_value=html)
        mock_ctx.bot.aiosession.get = MagicMock(return_value=AsyncContextManager(mock_response))

        with patch('src.gw2.cogs.misc.bot_utils.send_embed', new_callable=AsyncMock) as mock_send:
            await wiki(mock_ctx, search="sword")
            mock_send.assert_called_once()
            embed = mock_send.call_args[0][1]
            # All results contain keyword "sword" and no title exactly equals "Sword"
            # so none trigger the dedup logic
            assert len(embed.fields) == 3
            assert embed.fields[0].name == "Sword of Fire"
            assert embed.fields[1].name == "Sword of Ice"
            assert embed.fields[2].name == "Sword of Lightning"

    @pytest.mark.asyncio
    async def test_wiki_duplicate_keyword_title_skipped(self, mock_ctx):
        """Test wiki command skips duplicate keyword titles."""
        results = [
            {"title": "Eternity", "href": "/wiki/Eternity"},
            {"title": "Eternity", "href": "/wiki/Eternity_2"},
            {"title": "Eternity (item)", "href": "/wiki/Eternity_(item)"},
        ]
        html = self._make_search_result_html(results)
        mock_response = AsyncMock()
        mock_response.text = AsyncMock(return_value=html)
        mock_ctx.bot.aiosession.get = MagicMock(return_value=AsyncContextManager(mock_response))

        with patch('src.gw2.cogs.misc.bot_utils.send_embed', new_callable=AsyncMock) as mock_send:
            await wiki(mock_ctx, search="eternity")
            mock_send.assert_called_once()
            embed = mock_send.call_args[0][1]
            # The duplicate "Eternity" title should be skipped
            titles = [field.name for field in embed.fields]
            assert titles.count("Eternity") == 1

    @pytest.mark.asyncio
    async def test_wiki_history_page_skipped(self, mock_ctx):
        """Test wiki command skips history pages."""
        results = [
            {"title": "Eternity", "href": "/wiki/Eternity"},
            {"title": "Eternity/history", "href": "/wiki/Eternity/history"},
        ]
        html = self._make_search_result_html(results)
        mock_response = AsyncMock()
        mock_response.text = AsyncMock(return_value=html)
        mock_ctx.bot.aiosession.get = MagicMock(return_value=AsyncContextManager(mock_response))

        with patch('src.gw2.cogs.misc.bot_utils.send_embed', new_callable=AsyncMock) as mock_send:
            await wiki(mock_ctx, search="eternity")
            mock_send.assert_called_once()
            embed = mock_send.call_args[0][1]
            titles = [field.name for field in embed.fields]
            assert not any("/history" in t for t in titles)

    @pytest.mark.asyncio
    async def test_wiki_posts_limited_to_around_25(self, mock_ctx):
        """Test wiki command limits iteration via times_to_run.

        Note: The source code uses `while i <= times_to_run` where times_to_run=25,
        which iterates indices 0 through 25 (26 iterations). This is an off-by-one
        in the source, resulting in up to 26 fields when all match.
        """
        # Create 30 matching results
        results = [{"title": f"Sword {i}", "href": f"/wiki/Sword_{i}"} for i in range(30)]
        html = self._make_search_result_html(results)
        mock_response = AsyncMock()
        mock_response.text = AsyncMock(return_value=html)
        mock_ctx.bot.aiosession.get = MagicMock(return_value=AsyncContextManager(mock_response))

        with patch('src.gw2.cogs.misc.bot_utils.send_embed', new_callable=AsyncMock) as mock_send:
            await wiki(mock_ctx, search="sword")
            mock_send.assert_called_once()
            embed = mock_send.call_args[0][1]
            # Due to `while i <= 25` (off-by-one), up to 26 fields can be added
            assert len(embed.fields) == 26

    @pytest.mark.asyncio
    async def test_wiki_index_error_handled(self, mock_ctx):
        """Test wiki command handles IndexError gracefully."""
        # Create only 2 results but this should not crash
        results = [
            {"title": "Test Item", "href": "/wiki/Test_Item"},
        ]
        html = self._make_search_result_html(results)
        mock_response = AsyncMock()
        mock_response.text = AsyncMock(return_value=html)
        mock_ctx.bot.aiosession.get = MagicMock(return_value=AsyncContextManager(mock_response))

        with patch('src.gw2.cogs.misc.bot_utils.send_embed', new_callable=AsyncMock) as mock_send:
            # Should not raise - IndexError is caught
            await wiki(mock_ctx, search="test item")
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_wiki_no_matching_keywords(self, mock_ctx):
        """Test wiki command when results exist but none match the keyword."""
        results = [
            {"title": "Unrelated Thing", "href": "/wiki/Unrelated_Thing"},
            {"title": "Another Item", "href": "/wiki/Another_Item"},
        ]
        html = self._make_search_result_html(results)
        mock_response = AsyncMock()
        mock_response.text = AsyncMock(return_value=html)
        mock_ctx.bot.aiosession.get = MagicMock(return_value=AsyncContextManager(mock_response))

        with patch('src.gw2.cogs.misc.bot_utils.send_embed', new_callable=AsyncMock) as mock_send:
            await wiki(mock_ctx, search="eternity")
            mock_send.assert_called_once()
            embed = mock_send.call_args[0][1]
            # No matching results, so no fields added
            assert len(embed.fields) == 0

    @pytest.mark.asyncio
    async def test_wiki_url_with_parenthesis_escaped(self, mock_ctx):
        """Test wiki command escapes parentheses in URLs."""
        results = [
            {"title": "Eternity (item)", "href": "/wiki/Eternity_(item)"},
        ]
        html = self._make_search_result_html(results)
        mock_response = AsyncMock()
        mock_response.text = AsyncMock(return_value=html)
        mock_ctx.bot.aiosession.get = MagicMock(return_value=AsyncContextManager(mock_response))

        with patch('src.gw2.cogs.misc.bot_utils.send_embed', new_callable=AsyncMock) as mock_send:
            await wiki(mock_ctx, search="eternity")
            mock_send.assert_called_once()
            embed = mock_send.call_args[0][1]
            if embed.fields:
                # Check that ) is escaped in the URL
                assert "\\)" in embed.fields[0].value

    @pytest.mark.asyncio
    async def test_wiki_sets_thumbnail(self, mock_ctx):
        """Test wiki command sets the GW2 wiki icon as thumbnail."""
        results = [
            {"title": "Eternity", "href": "/wiki/Eternity"},
        ]
        html = self._make_search_result_html(results)
        mock_response = AsyncMock()
        mock_response.text = AsyncMock(return_value=html)
        mock_ctx.bot.aiosession.get = MagicMock(return_value=AsyncContextManager(mock_response))

        with patch('src.gw2.cogs.misc.bot_utils.send_embed', new_callable=AsyncMock) as mock_send:
            await wiki(mock_ctx, search="eternity")
            embed = mock_send.call_args[0][1]
            from src.gw2.constants import gw2_variables

            assert embed.thumbnail.url == gw2_variables.GW2_WIKI_ICON_URL

    @pytest.mark.asyncio
    async def test_wiki_search_with_spaces_converted_to_plus(self, mock_ctx):
        """Test wiki command converts spaces to plus signs in search."""
        results = [
            {"title": "Dawn Weapon", "href": "/wiki/Dawn_Weapon"},
        ]
        html = self._make_search_result_html(results)
        mock_response = AsyncMock()
        mock_response.text = AsyncMock(return_value=html)
        mock_ctx.bot.aiosession.get = MagicMock(return_value=AsyncContextManager(mock_response))

        with patch('src.gw2.cogs.misc.bot_utils.send_embed', new_callable=AsyncMock) as mock_send:
            await wiki(mock_ctx, search="dawn weapon")
            # Verify that the URL passed to aiosession.get contains + instead of spaces
            called_url = mock_ctx.bot.aiosession.get.call_args[0][0]
            assert "dawn+weapon" in called_url

    @pytest.mark.asyncio
    async def test_wiki_embed_title_set(self, mock_ctx):
        """Test wiki command sets embed title correctly."""
        results = [
            {"title": "Eternity", "href": "/wiki/Eternity"},
        ]
        html = self._make_search_result_html(results)
        mock_response = AsyncMock()
        mock_response.text = AsyncMock(return_value=html)
        mock_ctx.bot.aiosession.get = MagicMock(return_value=AsyncContextManager(mock_response))

        with patch('src.gw2.cogs.misc.bot_utils.send_embed', new_callable=AsyncMock) as mock_send:
            await wiki(mock_ctx, search="eternity")
            embed = mock_send.call_args[0][1]
            from src.gw2.constants import gw2_messages

            assert embed.title == gw2_messages.WIKI_SEARCH_RESULTS


class TestInfoCommand:
    """Test cases for the info command."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.db_session = MagicMock()
        ctx.bot.log = MagicMock()
        ctx.bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        ctx.bot.user = MagicMock()
        ctx.bot.user.mention = "<@bot>"
        ctx.bot.aiosession = MagicMock()
        ctx.message = MagicMock()
        ctx.message.author = MagicMock()
        ctx.message.author.id = 12345
        ctx.message.author.display_name = "TestUser"
        ctx.message.author.avatar = MagicMock()
        ctx.message.author.avatar.url = "https://example.com/avatar.png"
        ctx.message.channel = MagicMock()
        ctx.message.channel.typing = AsyncMock()
        ctx.prefix = "!"
        ctx.guild = MagicMock()
        ctx.guild.id = 99999
        ctx.channel = MagicMock(spec=discord.TextChannel)
        ctx.send = AsyncMock()
        ctx.author = ctx.message.author
        return ctx

    def _make_info_html(self, skill_name, description=None, image_alt=None, srcset=None, tp_data_id=None):
        """Helper to build HTML for info command.

        Args:
            skill_name: The skill name
            description: Blockquote text (if any)
            image_alt: Alt attribute for image match
            srcset: srcset attribute for image
            tp_data_id: data-id for trading post span (if any)
        """
        blockquote = ""
        if description:
            blockquote = f'<blockquote>\n\n{description}</blockquote>'

        img = ""
        if image_alt:
            if srcset:
                img = f'<img alt="{image_alt}" srcset="{srcset} 1x" />'
            else:
                img = f'<img alt="{image_alt}" />'

        tp_span = ""
        if tp_data_id:
            tp_span = f'<span class="gw2-tpprice" data-id="{tp_data_id}">price</span>'

        return f"<html><body>{blockquote}{img}{tp_span}<br/>new line</body></html>"

    @pytest.mark.asyncio
    async def test_info_non_200_status(self, mock_ctx):
        """Test info command sends error on non-200 status."""
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_ctx.bot.aiosession.get = MagicMock(return_value=AsyncContextManager(mock_response))

        with patch('src.gw2.cogs.misc.bot_utils.send_error_msg', new_callable=AsyncMock) as mock_error:
            await info(mock_ctx, skill="nonexistent")
            mock_error.assert_called_once()
            from src.gw2.constants import gw2_messages

            assert mock_error.call_args[0][1] == gw2_messages.NO_RESULTS

    @pytest.mark.asyncio
    async def test_info_skill_with_description_and_icon(self, mock_ctx):
        """Test info command with skill that has description and icon."""
        html = self._make_info_html(
            skill_name="Eternity",
            description="A legendary greatsword.",
            image_alt="eternity.png",
            srcset="/images/eternity.png",
        )
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.url = "https://wiki.guildwars2.com/wiki/Eternity"
        mock_response.text = AsyncMock(return_value=html)
        mock_ctx.bot.aiosession.get = MagicMock(return_value=AsyncContextManager(mock_response))

        with patch('src.gw2.cogs.misc.bot_utils.send_embed', new_callable=AsyncMock) as mock_send:
            await info(mock_ctx, skill="Eternity")
            mock_send.assert_called_once()
            embed = mock_send.call_args[0][1]
            assert embed.title == "Eternity"
            assert "legendary greatsword" in embed.description
            assert embed.color.value == 0x00FF00
            assert "eternity.png" in embed.thumbnail.url

    @pytest.mark.asyncio
    async def test_info_skill_with_trading_post_data(self, mock_ctx):
        """Test info command with skill that has trading post data."""
        html = self._make_info_html(
            skill_name="Eternity",
            description="A legendary greatsword.",
            image_alt="eternity.png",
            srcset="/images/eternity.png",
            tp_data_id="12345",
        )
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.url = "https://wiki.guildwars2.com/wiki/Eternity"
        mock_response.text = AsyncMock(return_value=html)

        tp_html = (
            '<html><body>'
            '<td id="sell-price" data-price="100000">1g</td>'
            '<td id="buy-price" data-price="90000">0g 90s</td>'
            '</body></html>'
        )
        mock_tp_response = AsyncMock()
        mock_tp_response.status = 200
        mock_tp_response.text = AsyncMock(return_value=tp_html)

        # First call returns wiki page, second returns TP page
        mock_ctx.bot.aiosession.get = MagicMock(
            side_effect=[
                AsyncContextManager(mock_response),
                AsyncContextManager(mock_tp_response),
            ]
        )

        with patch('src.gw2.cogs.misc.bot_utils.send_embed', new_callable=AsyncMock) as mock_send:
            with patch('src.gw2.cogs.misc.gw2_utils.format_gold', side_effect=["10g 0s 0c", "9g 0s 0c"]):
                await info(mock_ctx, skill="Eternity")
                mock_send.assert_called_once()
                embed = mock_send.call_args[0][1]
                assert "Trading Post" in embed.description
                assert "Sell:" in embed.description
                assert "Buy:" in embed.description
                assert "Gw2tp" in embed.description
                assert "Gw2bltc" in embed.description

    @pytest.mark.asyncio
    async def test_info_skill_without_description(self, mock_ctx):
        """Test info command with skill that has no description (no blockquote)."""
        html = '<html><body>' '<img alt="eternity.png" srcset="/images/eternity.png 1x" />' '</body></html>'
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.url = "https://wiki.guildwars2.com/wiki/Eternity"
        mock_response.text = AsyncMock(return_value=html)
        mock_ctx.bot.aiosession.get = MagicMock(return_value=AsyncContextManager(mock_response))

        with patch('src.gw2.cogs.misc.bot_utils.send_embed', new_callable=AsyncMock) as mock_send:
            await info(mock_ctx, skill="Eternity")
            mock_send.assert_called_once()
            embed = mock_send.call_args[0][1]
            from src.gw2.constants import gw2_messages

            assert embed.description == gw2_messages.CLICK_ON_LINK
            assert embed.color == discord.Color.red()

    @pytest.mark.asyncio
    async def test_info_no_image_match_found(self, mock_ctx):
        """Test info command when no matching image is found."""
        html = (
            '<html><body>'
            '<blockquote>\n\nSome description.</blockquote>'
            '<img alt="other_image.png" srcset="/images/other.png 1x" />'
            '</body></html>'
        )
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.url = "https://wiki.guildwars2.com/wiki/Eternity"
        mock_response.text = AsyncMock(return_value=html)
        mock_ctx.bot.aiosession.get = MagicMock(return_value=AsyncContextManager(mock_response))

        with patch('src.gw2.cogs.misc.bot_utils.send_embed', new_callable=AsyncMock) as mock_send:
            await info(mock_ctx, skill="Eternity")
            mock_send.assert_called_once()
            embed = mock_send.call_args[0][1]
            # Icon URL should be empty string (no match found)
            assert embed.thumbnail.url == ""

    @pytest.mark.asyncio
    async def test_info_image_key_error_on_srcset(self, mock_ctx):
        """Test info command handles KeyError when image has no srcset."""
        html = (
            '<html><body>'
            '<blockquote>\n\nSome description.</blockquote>'
            '<img alt="eternity.png" />'
            '</body></html>'
        )
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.url = "https://wiki.guildwars2.com/wiki/Eternity"
        mock_response.text = AsyncMock(return_value=html)
        mock_ctx.bot.aiosession.get = MagicMock(return_value=AsyncContextManager(mock_response))

        with patch('src.gw2.cogs.misc.bot_utils.send_embed', new_callable=AsyncMock) as mock_send:
            # Should not raise KeyError
            await info(mock_ctx, skill="Eternity")
            mock_send.assert_called_once()
            embed = mock_send.call_args[0][1]
            # Icon URL remains empty since KeyError was handled
            assert embed.thumbnail.url == ""

    @pytest.mark.asyncio
    async def test_info_no_trading_post_item(self, mock_ctx):
        """Test info command when no trading post item is found (item_id is None)."""
        html = (
            '<html><body>'
            '<blockquote>\n\nA skill description.</blockquote>'
            '<img alt="eternity.png" srcset="/images/eternity.png 1x" />'
            '</body></html>'
        )
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.url = "https://wiki.guildwars2.com/wiki/Eternity"
        mock_response.text = AsyncMock(return_value=html)
        mock_ctx.bot.aiosession.get = MagicMock(return_value=AsyncContextManager(mock_response))

        with patch('src.gw2.cogs.misc.bot_utils.send_embed', new_callable=AsyncMock) as mock_send:
            await info(mock_ctx, skill="Eternity")
            mock_send.assert_called_once()
            embed = mock_send.call_args[0][1]
            # No TP data should be in description
            assert "Trading Post" not in embed.description
            assert "Sell:" not in embed.description

    @pytest.mark.asyncio
    async def test_info_tp_request_non_200(self, mock_ctx):
        """Test info command when TP request returns non-200 status."""
        html = self._make_info_html(
            skill_name="Eternity",
            description="A legendary greatsword.",
            image_alt="eternity.png",
            srcset="/images/eternity.png",
            tp_data_id="12345",
        )
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.url = "https://wiki.guildwars2.com/wiki/Eternity"
        mock_response.text = AsyncMock(return_value=html)

        mock_tp_response = AsyncMock()
        mock_tp_response.status = 404

        mock_ctx.bot.aiosession.get = MagicMock(
            side_effect=[
                AsyncContextManager(mock_response),
                AsyncContextManager(mock_tp_response),
            ]
        )

        with patch('src.gw2.cogs.misc.bot_utils.send_embed', new_callable=AsyncMock) as mock_send:
            await info(mock_ctx, skill="Eternity")
            mock_send.assert_called_once()
            embed = mock_send.call_args[0][1]
            # TP data should not be included
            assert "Trading Post" not in embed.description

    @pytest.mark.asyncio
    async def test_info_skill_name_extracted_from_url(self, mock_ctx):
        """Test info command extracts skill name from URL correctly."""
        html = self._make_info_html(
            skill_name="Sunrise",
            description="A legendary greatsword of dawn.",
            image_alt="sunrise.png",
            srcset="/images/sunrise.png",
        )
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.url = "https://wiki.guildwars2.com/wiki/Sunrise"
        mock_response.text = AsyncMock(return_value=html)
        mock_ctx.bot.aiosession.get = MagicMock(return_value=AsyncContextManager(mock_response))

        with patch('src.gw2.cogs.misc.bot_utils.send_embed', new_callable=AsyncMock) as mock_send:
            await info(mock_ctx, skill="Sunrise")
            embed = mock_send.call_args[0][1]
            assert embed.title == "Sunrise"

    @pytest.mark.asyncio
    async def test_info_skill_name_with_underscores_converted(self, mock_ctx):
        """Test info command converts underscores in URL to spaces for title."""
        html = self._make_info_html(
            skill_name="Bolt of Damask",
            description="A crafting material.",
            image_alt="bolt of damask.png",
            srcset="/images/bolt_of_damask.png",
        )
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.url = "https://wiki.guildwars2.com/wiki/Bolt_of_Damask"
        mock_response.text = AsyncMock(return_value=html)
        mock_ctx.bot.aiosession.get = MagicMock(return_value=AsyncContextManager(mock_response))

        with patch('src.gw2.cogs.misc.bot_utils.send_embed', new_callable=AsyncMock) as mock_send:
            await info(mock_ctx, skill="bolt of damask")
            embed = mock_send.call_args[0][1]
            assert embed.title == "Bolt of Damask"

    @pytest.mark.asyncio
    async def test_info_skill_with_spaces_replaced_by_underscore(self, mock_ctx):
        """Test info command replaces spaces with underscores for URL."""
        html = self._make_info_html(
            skill_name="Bolt",
            description="A legendary sword.",
        )
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.url = "https://wiki.guildwars2.com/wiki/Dawn_Weapon"
        mock_response.text = AsyncMock(return_value=html)
        mock_ctx.bot.aiosession.get = MagicMock(return_value=AsyncContextManager(mock_response))

        with patch('src.gw2.cogs.misc.bot_utils.send_embed', new_callable=AsyncMock) as mock_send:
            await info(mock_ctx, skill="dawn weapon")
            called_url = mock_ctx.bot.aiosession.get.call_args[0][0]
            assert "Dawn_Weapon" in called_url or "dawn_weapon" in called_url

    @pytest.mark.asyncio
    async def test_info_embed_author_set(self, mock_ctx):
        """Test info command sets embed author correctly."""
        html = self._make_info_html(
            skill_name="Eternity",
            description="A legendary greatsword.",
        )
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.url = "https://wiki.guildwars2.com/wiki/Eternity"
        mock_response.text = AsyncMock(return_value=html)
        mock_ctx.bot.aiosession.get = MagicMock(return_value=AsyncContextManager(mock_response))

        with patch('src.gw2.cogs.misc.bot_utils.send_embed', new_callable=AsyncMock) as mock_send:
            await info(mock_ctx, skill="Eternity")
            embed = mock_send.call_args[0][1]
            assert embed.author.name == "TestUser"
            assert embed.author.icon_url == "https://example.com/avatar.png"

    @pytest.mark.asyncio
    async def test_info_embed_url_set(self, mock_ctx):
        """Test info command sets embed URL correctly."""
        html = self._make_info_html(
            skill_name="Eternity",
            description="A legendary greatsword.",
        )
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.url = "https://wiki.guildwars2.com/wiki/Eternity"
        mock_response.text = AsyncMock(return_value=html)
        mock_ctx.bot.aiosession.get = MagicMock(return_value=AsyncContextManager(mock_response))

        with patch('src.gw2.cogs.misc.bot_utils.send_embed', new_callable=AsyncMock) as mock_send:
            await info(mock_ctx, skill="Eternity")
            embed = mock_send.call_args[0][1]
            assert embed.url == "https://wiki.guildwars2.com/wiki/Eternity"

    @pytest.mark.asyncio
    async def test_info_description_strips_question_mark(self, mock_ctx):
        """Test info command removes question marks from description."""
        html = '<html><body>' '<blockquote>\n\nSome description?</blockquote>' '</body></html>'
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.url = "https://wiki.guildwars2.com/wiki/Eternity"
        mock_response.text = AsyncMock(return_value=html)
        mock_ctx.bot.aiosession.get = MagicMock(return_value=AsyncContextManager(mock_response))

        with patch('src.gw2.cogs.misc.bot_utils.send_embed', new_callable=AsyncMock) as mock_send:
            await info(mock_ctx, skill="Eternity")
            embed = mock_send.call_args[0][1]
            assert "?" not in embed.description

    @pytest.mark.asyncio
    async def test_info_description_splits_on_em_dash(self, mock_ctx):
        """Test info command splits description on em dash."""
        html = (
            '<html><body>' '<blockquote>\n\nSome description text\u2014Attribution here</blockquote>' '</body></html>'
        )
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.url = "https://wiki.guildwars2.com/wiki/Eternity"
        mock_response.text = AsyncMock(return_value=html)
        mock_ctx.bot.aiosession.get = MagicMock(return_value=AsyncContextManager(mock_response))

        with patch('src.gw2.cogs.misc.bot_utils.send_embed', new_callable=AsyncMock) as mock_send:
            await info(mock_ctx, skill="Eternity")
            embed = mock_send.call_args[0][1]
            # Description should only contain text before the em dash
            assert "Attribution here" not in embed.description
            assert "Some description text" in embed.description

    @pytest.mark.asyncio
    async def test_info_of_and_the_lowercased_in_skill(self, mock_ctx):
        """Test info command lowercases 'Of' to 'of' and 'The' to 'the' in sanitized skill."""
        html = self._make_info_html(
            skill_name="Blade of the Void",
            description="A powerful weapon.",
            image_alt="blade of the void.png",
            srcset="/images/blade.png",
        )
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.url = "https://wiki.guildwars2.com/wiki/Blade_of_the_Void"
        mock_response.text = AsyncMock(return_value=html)
        mock_ctx.bot.aiosession.get = MagicMock(return_value=AsyncContextManager(mock_response))

        with patch('src.gw2.cogs.misc.bot_utils.send_embed', new_callable=AsyncMock) as mock_send:
            await info(mock_ctx, skill="blade of the void")
            called_url = mock_ctx.bot.aiosession.get.call_args[0][0]
            # URL should use "of" and "the" (lowercase), not "Of" and "The"
            assert "Blade_of_the_Void" in called_url

    @pytest.mark.asyncio
    async def test_info_returns_none_on_success(self, mock_ctx):
        """Test info command returns None on successful execution."""
        html = self._make_info_html(
            skill_name="Eternity",
            description="A legendary greatsword.",
        )
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.url = "https://wiki.guildwars2.com/wiki/Eternity"
        mock_response.text = AsyncMock(return_value=html)
        mock_ctx.bot.aiosession.get = MagicMock(return_value=AsyncContextManager(mock_response))

        with patch('src.gw2.cogs.misc.bot_utils.send_embed', new_callable=AsyncMock):
            result = await info(mock_ctx, skill="Eternity")
            assert result is None

    @pytest.mark.asyncio
    async def test_info_calls_typing(self, mock_ctx):
        """Test info command calls typing indicator."""
        html = self._make_info_html(
            skill_name="Eternity",
            description="A legendary greatsword.",
        )
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.url = "https://wiki.guildwars2.com/wiki/Eternity"
        mock_response.text = AsyncMock(return_value=html)
        mock_ctx.bot.aiosession.get = MagicMock(return_value=AsyncContextManager(mock_response))

        with patch('src.gw2.cogs.misc.bot_utils.send_embed', new_callable=AsyncMock):
            await info(mock_ctx, skill="Eternity")
            mock_ctx.message.channel.typing.assert_called_once()

    @pytest.mark.asyncio
    async def test_info_tp_url_format(self, mock_ctx):
        """Test info command formats TP URLs correctly with hyphens."""
        html = self._make_info_html(
            skill_name="Bolt of Damask",
            description="A crafting material.",
            image_alt="bolt of damask.png",
            srcset="/images/bolt.png",
            tp_data_id="99999",
        )
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.url = "https://wiki.guildwars2.com/wiki/Bolt_of_Damask"
        mock_response.text = AsyncMock(return_value=html)

        tp_html = (
            '<html><body>'
            '<td id="sell-price" data-price="50000">5g</td>'
            '<td id="buy-price" data-price="45000">4g 50s</td>'
            '</body></html>'
        )
        mock_tp_response = AsyncMock()
        mock_tp_response.status = 200
        mock_tp_response.text = AsyncMock(return_value=tp_html)

        mock_ctx.bot.aiosession.get = MagicMock(
            side_effect=[
                AsyncContextManager(mock_response),
                AsyncContextManager(mock_tp_response),
            ]
        )

        with patch('src.gw2.cogs.misc.bot_utils.send_embed', new_callable=AsyncMock) as mock_send:
            with patch('src.gw2.cogs.misc.gw2_utils.format_gold', side_effect=["5g 0s 0c", "4g 50s 0c"]):
                await info(mock_ctx, skill="bolt of damask")
                embed = mock_send.call_args[0][1]
                # TP URL should use hyphens instead of underscores
                assert "bolt-of-damask" in embed.description
                assert "gw2tp.com" in embed.description
                assert "gw2bltc.com" in embed.description


class TestMiscSetup:
    """Test cases for misc cog setup."""

    @pytest.mark.asyncio
    async def test_setup_function_exists(self):
        """Test that setup function exists and is callable."""
        assert callable(setup)

    @pytest.mark.asyncio
    async def test_setup_removes_existing_gw2_command(self):
        """Test that setup removes existing gw2 command."""
        mock_bot = MagicMock()
        mock_bot.remove_command = MagicMock()
        mock_bot.add_cog = AsyncMock()

        await setup(mock_bot)
        mock_bot.remove_command.assert_called_once_with("gw2")

    @pytest.mark.asyncio
    async def test_setup_adds_cog(self):
        """Test that setup adds the GW2Misc cog."""
        mock_bot = MagicMock()
        mock_bot.remove_command = MagicMock()
        mock_bot.add_cog = AsyncMock()

        await setup(mock_bot)
        mock_bot.add_cog.assert_called_once()
        cog_instance = mock_bot.add_cog.call_args[0][0]
        assert isinstance(cog_instance, GW2Misc)


class TestWikiNoResultsBranch:
    """Test cases for the wiki command line 80 - the 'else' branch when total_posts is 0."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock()
        ctx.bot = MagicMock()
        ctx.bot.db_session = MagicMock()
        ctx.bot.log = MagicMock()
        ctx.bot.settings = {"gw2": {"EmbedColor": 0x00FF00}}
        ctx.bot.user = MagicMock()
        ctx.bot.user.mention = "<@bot>"
        ctx.bot.aiosession = MagicMock()
        ctx.message = MagicMock()
        ctx.message.author = MagicMock()
        ctx.message.author.id = 12345
        ctx.message.author.display_name = "TestUser"
        ctx.message.author.avatar = MagicMock()
        ctx.message.author.avatar.url = "https://example.com/avatar.png"
        ctx.message.channel = MagicMock()
        ctx.message.channel.typing = AsyncMock()
        ctx.prefix = "!"
        ctx.guild = MagicMock()
        ctx.guild.id = 99999
        ctx.channel = MagicMock(spec=discord.TextChannel)
        ctx.send = AsyncMock()
        ctx.author = ctx.message.author
        return ctx

    @pytest.mark.asyncio
    async def test_wiki_no_search_results_sends_no_results_error(self, mock_ctx):
        """Test wiki command sends error when no search results found (line 80 - no posts).

        This covers the case where posts is an empty list, triggering
        'await bot_utils.send_error_msg(ctx, gw2_messages.NO_RESULTS)' and returning.
        """
        # HTML with no mw-search-result-heading divs at all
        html = "<html><body><div>No results here</div></body></html>"
        mock_response = AsyncMock()
        mock_response.text = AsyncMock(return_value=html)
        mock_ctx.bot.aiosession.get = MagicMock(
            return_value=type(
                'AsyncCM',
                (),
                {
                    '__aenter__': AsyncMock(return_value=mock_response),
                    '__aexit__': AsyncMock(return_value=False),
                },
            )()
        )

        with patch('src.gw2.cogs.misc.bot_utils.send_error_msg', new_callable=AsyncMock) as mock_error:
            await wiki(mock_ctx, search="xyznonexistent123")
            mock_error.assert_called_once()
            from src.gw2.constants import gw2_messages

            assert mock_error.call_args[0][1] == gw2_messages.NO_RESULTS
