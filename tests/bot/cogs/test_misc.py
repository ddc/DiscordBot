"""Comprehensive tests for the Misc cog."""

import pytest
import discord
import sys
from unittest.mock import AsyncMock, MagicMock, patch, Mock, mock_open
from discord.ext import commands
from datetime import datetime, timezone
from io import BytesIO

# Mock problematic imports before importing the module
sys.modules['ddcDatabases'] = Mock()

from src.bot.cogs.misc import Misc
from src.bot.constants import messages, variables


@pytest.fixture
def mock_bot():
    """Create a mock bot instance."""
    bot = AsyncMock()
    bot.db_session = MagicMock()
    bot.log = MagicMock()
    bot.user = MagicMock()
    bot.user.name = "TestBot"
    bot.user.display_name = "TestBot"
    bot.user.avatar = MagicMock()
    bot.user.avatar.url = "https://example.com/bot_avatar.png"
    bot.owner_id = 123456
    bot.description = "Test bot description"
    bot.start_time = datetime.now(timezone.utc)
    bot.guilds = []
    bot.users = []
    return bot


@pytest.fixture
def misc_cog(mock_bot):
    """Create a Misc cog instance."""
    return Misc(mock_bot)


@pytest.fixture
def mock_ctx():
    """Create a mock context."""
    ctx = AsyncMock()
    ctx.guild = MagicMock()
    ctx.guild.id = 12345
    ctx.guild.name = "Test Server"
    ctx.guild.icon = MagicMock()
    ctx.guild.icon.url = "https://example.com/icon.png"
    ctx.guild.members = []
    ctx.guild.text_channels = []
    ctx.guild.voice_channels = []
    ctx.guild.roles = []
    ctx.guild.emojis = []
    ctx.guild.created_at = datetime.now(timezone.utc)
    ctx.guild.owner = MagicMock()
    ctx.guild.owner.display_name = "ServerOwner"
    
    author = MagicMock()
    author.id = 67890
    author.display_name = "TestUser"
    author.nick = None
    author.avatar = MagicMock()
    author.avatar.url = "https://example.com/avatar.png"
    author.created_at = datetime.now(timezone.utc)
    author.joined_at = datetime.now(timezone.utc)
    author.color = discord.Color.blue()
    author.roles = []
    author.status = discord.Status.online
    author.activity = None
    author.__str__ = MagicMock(return_value="TestUser")
    
    ctx.author = author
    ctx.message = MagicMock()
    ctx.message.channel = AsyncMock()
    ctx.prefix = "!"
    ctx.subcommand_passed = None
    ctx.send = AsyncMock()
    
    return ctx


@pytest.fixture
def mock_member():
    """Create a mock member."""
    member = MagicMock()
    member.id = 99999
    member.display_name = "TestMember"
    member.nick = "Nickname"
    member.avatar = MagicMock()
    member.avatar.url = "https://example.com/member_avatar.png"
    member.created_at = datetime.now(timezone.utc)
    member.joined_at = datetime.now(timezone.utc)
    member.color = discord.Color.green()
    member.roles = []
    member.status = discord.Status.idle
    member.activity = None
    member.__str__ = MagicMock(return_value="TestMember")
    return member


class TestMisc:
    """Test cases for Misc cog."""
    
    def test_init(self, mock_bot):
        """Test Misc cog initialization."""
        cog = Misc(mock_bot)
        assert cog.bot == mock_bot
        assert hasattr(cog, '_random')
    
    # Test pepe command
    @pytest.mark.asyncio
    @patch('src.bot.cogs.misc.pepedatabase', ['https://example.com/pepe1.jpg', 'https://example.com/pepe2.jpg'])
    async def test_pepe_command_success(self, misc_cog, mock_ctx):
        """Test successful pepe command execution."""
        mock_ctx.subcommand_passed = None
        
        with patch.object(misc_cog._random, 'choice', return_value='https://example.com/pepe1.jpg'):
            await misc_cog.pepe.callback(misc_cog, mock_ctx)
            
            mock_ctx.message.channel.typing.assert_called_once()
            mock_ctx.send.assert_called_once_with('https://example.com/pepe1.jpg')
    
    @pytest.mark.asyncio
    async def test_pepe_command_with_subcommand(self, misc_cog, mock_ctx):
        """Test pepe command with subcommand (should raise BadArgument)."""
        mock_ctx.subcommand_passed = "some_subcommand"
        
        with pytest.raises(commands.BadArgument):
            await misc_cog.pepe.callback(misc_cog, mock_ctx)
    
    # Test TTS command
    @pytest.mark.asyncio
    @patch('src.bot.cogs.misc.gTTS')
    @patch('src.bot.cogs.misc.bot_utils.send_error_msg')
    async def test_tts_command_success(self, mock_send_error, mock_gtts_class, misc_cog, mock_ctx):
        """Test successful TTS command execution."""
        # Setup TTS mock
        mock_tts = MagicMock()
        mock_gtts_class.return_value = mock_tts
        
        await misc_cog.tts.callback(misc_cog, mock_ctx, tts_text="Hello world")
        
        mock_ctx.message.channel.typing.assert_called_once()
        mock_gtts_class.assert_called_once_with(text="Hello world", lang="en", slow=False, timeout=10)
        mock_tts.write_to_fp.assert_called_once()
        mock_ctx.send.assert_called_once()
        
        # Verify file was sent
        sent_file = mock_ctx.send.call_args[1]['file']
        assert isinstance(sent_file, discord.File)
        assert sent_file.filename == "TestUser.mp3"
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.misc.gTTS')
    @patch('src.bot.cogs.misc.bot_utils.send_error_msg')
    async def test_tts_command_with_mentions(self, mock_send_error, mock_gtts_class, misc_cog, mock_ctx):
        """Test TTS command with user mentions."""
        # Setup mock member
        mock_member = MagicMock()
        mock_member.display_name = "MentionedUser"
        mock_ctx.guild.get_member.return_value = mock_member
        
        mock_tts = MagicMock()
        mock_gtts_class.return_value = mock_tts
        
        await misc_cog.tts.callback(misc_cog, mock_ctx, tts_text="Hello <@!123456789>")
        
        # Should process mention and call gTTS with processed text
        mock_gtts_class.assert_called_once()
        processed_text = mock_gtts_class.call_args[1]['text']
        assert "@MentionedUser" in processed_text
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.misc.gTTS')
    @patch('src.bot.cogs.misc.bot_utils.send_error_msg')
    async def test_tts_command_with_emojis(self, mock_send_error, mock_gtts_class, misc_cog, mock_ctx):
        """Test TTS command with custom emojis."""
        mock_tts = MagicMock()
        mock_gtts_class.return_value = mock_tts
        
        await misc_cog.tts.callback(misc_cog, mock_ctx, tts_text="Hello <:smile:123456789012345678>")
        
        # Should process emoji and call gTTS with processed text
        mock_gtts_class.assert_called_once()
        processed_text = mock_gtts_class.call_args[1]['text']
        assert "smile" in processed_text
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.misc.gTTS', side_effect=AssertionError("TTS Error"))
    @patch('src.bot.cogs.misc.bot_utils.send_error_msg')
    async def test_tts_command_error(self, mock_send_error, mock_gtts_class, misc_cog, mock_ctx):
        """Test TTS command with gTTS error."""
        await misc_cog.tts.callback(misc_cog, mock_ctx, tts_text="Hello world")
        
        mock_send_error.assert_called_once_with(mock_ctx, messages.INVALID_MESSAGE)
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.misc.bot_utils.send_error_msg')
    async def test_tts_command_empty_text(self, mock_send_error, misc_cog, mock_ctx):
        """Test TTS command with empty processed text."""
        await misc_cog.tts.callback(misc_cog, mock_ctx, tts_text="")
        
        mock_send_error.assert_called_once_with(mock_ctx, messages.INVALID_MESSAGE)
    
    # Test echo command
    @pytest.mark.asyncio
    @patch('src.bot.cogs.misc.bot_utils.send_msg')
    async def test_echo_command(self, mock_send_msg, misc_cog, mock_ctx):
        """Test echo command."""
        await misc_cog.echo.callback(misc_cog, mock_ctx, msg="Hello world!")
        
        mock_ctx.message.channel.typing.assert_called_once()
        mock_send_msg.assert_called_once_with(mock_ctx, "Hello world!")
    
    # Test ping command
    @pytest.mark.asyncio
    @patch('src.bot.cogs.misc.bot_utils.send_embed')
    async def test_ping_command_good_latency(self, mock_send_embed, misc_cog, mock_ctx):
        """Test ping command with good latency."""
        mock_ctx.subcommand_passed = None
        misc_cog.bot.ws.latency = 0.1  # 100ms
        
        await misc_cog.ping.callback(misc_cog, mock_ctx)
        
        mock_ctx.message.channel.typing.assert_called_once()
        mock_send_embed.assert_called_once()
        
        embed = mock_send_embed.call_args[0][1]
        assert "100 ms" in embed.description
        assert embed.color == discord.Color.green()
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.misc.bot_utils.send_embed')
    async def test_ping_command_bad_latency(self, mock_send_embed, misc_cog, mock_ctx):
        """Test ping command with bad latency."""
        mock_ctx.subcommand_passed = None
        misc_cog.bot.ws.latency = 0.3  # 300ms
        
        await misc_cog.ping.callback(misc_cog, mock_ctx)
        
        embed = mock_send_embed.call_args[0][1]
        assert "300 ms" in embed.description
        assert embed.color == discord.Color.red()
    
    @pytest.mark.asyncio
    async def test_ping_command_with_subcommand(self, misc_cog, mock_ctx):
        """Test ping command with subcommand (should raise BadArgument)."""
        mock_ctx.subcommand_passed = "some_subcommand"
        
        with pytest.raises(commands.BadArgument):
            await misc_cog.ping.callback(misc_cog, mock_ctx)
    
    # Test lmgtfy command
    @pytest.mark.asyncio
    @patch('src.bot.cogs.misc.bot_utils.send_msg')
    async def test_lmgtfy_command(self, mock_send_msg, misc_cog, mock_ctx):
        """Test lmgtfy command."""
        await misc_cog.lmgtfy.callback(misc_cog, mock_ctx, user_msg="how to code in python")
        
        mock_ctx.message.channel.typing.assert_called_once()
        mock_send_msg.assert_called_once()
        
        sent_url = mock_send_msg.call_args[0][1]
        assert variables.LMGTFY_URL in sent_url
        assert "how+to+code+in+python" in sent_url
    
    # Test invites command
    @pytest.mark.asyncio
    @patch('src.bot.cogs.misc.bot_utils.send_msg')
    @patch('src.bot.cogs.misc.chat_formatting.inline')
    async def test_invites_command_no_invites(self, mock_inline, mock_send_msg, misc_cog, mock_ctx):
        """Test invites command with no invites."""
        mock_ctx.subcommand_passed = None
        mock_ctx.guild.invites = AsyncMock(return_value=[])
        mock_inline.return_value = "inline_text"
        
        await misc_cog.invites.callback(misc_cog, mock_ctx)
        
        mock_ctx.message.channel.typing.assert_called_once()
        mock_send_msg.assert_called_once_with(mock_ctx, "inline_text")
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.misc.bot_utils.send_embed')
    async def test_invites_command_with_invites(self, mock_send_embed, misc_cog, mock_ctx):
        """Test invites command with various invite types."""
        mock_ctx.subcommand_passed = None
        
        # Create mock invites
        unlimited_invite = MagicMock()
        unlimited_invite.revoked = False
        unlimited_invite.max_age = 0
        unlimited_invite.code = "unlimited123"
        unlimited_invite.url = "https://discord.gg/unlimited123"
        unlimited_invite.channel = "general"
        unlimited_invite.inviter = "TestUser"
        
        limited_invite = MagicMock()
        limited_invite.revoked = False
        limited_invite.max_age = 3600
        limited_invite.code = "limited123"
        limited_invite.url = "https://discord.gg/limited123"
        limited_invite.channel = "random"
        limited_invite.inviter = "OtherUser"
        
        revoked_invite = MagicMock()
        revoked_invite.revoked = True
        revoked_invite.code = "revoked123"
        revoked_invite.channel = "old-channel"
        revoked_invite.inviter = "FormerUser"
        
        mock_ctx.guild.invites = AsyncMock(return_value=[unlimited_invite, limited_invite, revoked_invite])
        
        await misc_cog.invites.callback(misc_cog, mock_ctx)
        
        mock_send_embed.assert_called_once()
        embed = mock_send_embed.call_args[0][1]
        assert embed.title == messages.INVITE_TITLE
        assert len(embed.fields) == 3  # unlimited, limited, revoked
    
    @pytest.mark.asyncio
    async def test_invites_command_with_subcommand(self, misc_cog, mock_ctx):
        """Test invites command with subcommand (should raise BadArgument)."""
        mock_ctx.subcommand_passed = "some_subcommand"
        
        with pytest.raises(commands.BadArgument):
            await misc_cog.invites.callback(misc_cog, mock_ctx)
    
    # Test serverinfo command
    @pytest.mark.asyncio
    @patch('src.bot.cogs.misc.bot_utils.send_embed')
    @patch('src.bot.cogs.misc.bot_utils.get_current_date_time')
    @patch('src.bot.cogs.misc.bot_utils.convert_datetime_to_str_long')
    async def test_serverinfo_command(self, mock_convert_datetime, mock_get_current_time, 
                                    mock_send_embed, misc_cog, mock_ctx):
        """Test serverinfo command."""
        mock_ctx.subcommand_passed = None
        
        # Setup time mocks
        current_time = datetime.now(timezone.utc)
        mock_get_current_time.return_value = current_time
        mock_convert_datetime.return_value = "2023-01-01 12:00:00 UTC"
        
        # Setup guild members
        online_member = MagicMock()
        online_member.bot = False
        online_member.status = discord.Status.online
        
        idle_member = MagicMock()
        idle_member.bot = False
        idle_member.status = discord.Status.idle
        
        offline_member = MagicMock()
        offline_member.bot = False
        offline_member.status = discord.Status.offline
        
        bot_member = MagicMock()
        bot_member.bot = True
        bot_member.status = discord.Status.online
        
        mock_ctx.guild.members = [online_member, idle_member, offline_member, bot_member]
        
        await misc_cog.serverinfo.callback(misc_cog, mock_ctx)
        
        mock_ctx.message.channel.typing.assert_called_once()
        mock_send_embed.assert_called_once()
        
        embed = mock_send_embed.call_args[0][1]
        assert embed.author.name == "Test Server"
        assert len(embed.fields) == 9  # Users, Online, Offline, Bots, Text Channels, Voice Channels, Roles, Owner, Emojis
    
    @pytest.mark.asyncio
    async def test_serverinfo_command_with_subcommand(self, misc_cog, mock_ctx):
        """Test serverinfo command with subcommand (should raise BadArgument)."""
        mock_ctx.subcommand_passed = "some_subcommand"
        
        with pytest.raises(commands.BadArgument):
            await misc_cog.serverinfo.callback(misc_cog, mock_ctx)
    
    # Test userinfo command
    @pytest.mark.asyncio
    @patch('src.bot.cogs.misc.bot_utils.send_embed')
    @patch('src.bot.cogs.misc.bot_utils.get_object_member_by_str')
    @patch('src.bot.cogs.misc.bot_utils.get_current_date_time')
    async def test_userinfo_command_self(self, mock_get_current_time, mock_get_member, 
                                       mock_send_embed, misc_cog, mock_ctx):
        """Test userinfo command for self."""
        mock_get_current_time.return_value = datetime.now(timezone.utc)
        mock_get_member.return_value = None  # No member string provided
        
        # Setup guild members including the author for member number calculation
        mock_ctx.guild.members = [mock_ctx.author]
        
        await misc_cog.userinfo.callback(misc_cog, mock_ctx, member_str=None)
        
        mock_ctx.message.channel.typing.assert_called_once()
        mock_send_embed.assert_called_once()
        
        embed = mock_send_embed.call_args[0][1]
        assert embed.author.name.startswith("TestUser")
        assert embed.color == discord.Color.blue()
    
    @pytest.mark.asyncio
    @patch('src.bot.cogs.misc.bot_utils.send_embed')
    @patch('src.bot.cogs.misc.bot_utils.get_object_member_by_str')
    @patch('src.bot.cogs.misc.bot_utils.get_current_date_time')
    async def test_userinfo_command_other_user(self, mock_get_current_time, mock_get_member, 
                                             mock_send_embed, misc_cog, mock_ctx, mock_member):
        """Test userinfo command for other user."""
        mock_get_current_time.return_value = datetime.now(timezone.utc)
        mock_get_member.return_value = mock_member
        
        # Setup guild members including the target member for member number calculation
        mock_ctx.guild.members = [mock_member]
        
        await misc_cog.userinfo.callback(misc_cog, mock_ctx, member_str="TestMember")
        
        mock_get_member.assert_called_once_with(mock_ctx, "TestMember")
        mock_send_embed.assert_called_once()
        
        embed = mock_send_embed.call_args[0][1]
        assert "TestMember ~ Nickname" in embed.author.name
    
    # Test about command
    @pytest.mark.asyncio
    @patch('src.bot.cogs.misc.bot_utils.send_embed')
    @patch('src.bot.cogs.misc.bot_utils.get_bot_stats')
    async def test_about_command(self, mock_get_bot_stats, mock_send_embed, misc_cog, mock_ctx):
        """Test about command."""
        mock_ctx.subcommand_passed = None
        
        # Setup bot stats
        mock_get_bot_stats.return_value = {
            "servers": "5 servers",
            "users": "(100 users)(10 bots)[110 total]",
            "channels": "(50 text)(20 voice)[70 total]"
        }
        
        # Setup bot owner - make get_user return a regular mock, not coroutine
        mock_owner = MagicMock()
        mock_owner.avatar = MagicMock()
        mock_owner.avatar.url = "https://example.com/owner_avatar.png"
        misc_cog.bot.get_user = MagicMock(return_value=mock_owner)  # Not AsyncMock
        
        await misc_cog.about.callback(misc_cog, mock_ctx)
        
        mock_ctx.message.channel.typing.assert_called_once()
        mock_send_embed.assert_called_once()
        
        embed = mock_send_embed.call_args[0][1]
        assert embed.author.name.startswith("TestBot")
        assert embed.description == "Test bot description"
    
    @pytest.mark.asyncio
    async def test_about_command_with_subcommand(self, misc_cog, mock_ctx):
        """Test about command with subcommand (should raise BadArgument)."""
        mock_ctx.subcommand_passed = "some_subcommand"
        
        with pytest.raises(commands.BadArgument):
            await misc_cog.about.callback(misc_cog, mock_ctx)
    
    # Test TTS helper methods
    def test_has_special_tokens_true(self, misc_cog):
        """Test _has_special_tokens with special tokens."""
        assert misc_cog._has_special_tokens("Hello <@!123456789>") is True
        assert misc_cog._has_special_tokens("Hello <:emoji:123456789>") is True
    
    def test_has_special_tokens_false(self, misc_cog):
        """Test _has_special_tokens without special tokens."""
        assert misc_cog._has_special_tokens("Hello world") is False
        assert misc_cog._has_special_tokens("") is False
    
    def test_is_user_mention_true(self, misc_cog):
        """Test _is_user_mention with valid mention."""
        assert misc_cog._is_user_mention("<@!123456789>") is True
    
    def test_is_user_mention_false(self, misc_cog):
        """Test _is_user_mention with invalid mention."""
        assert misc_cog._is_user_mention("@user") is False
        assert misc_cog._is_user_mention("<@123456789>") is False
        assert misc_cog._is_user_mention("hello") is False
    
    def test_is_custom_emoji_true(self, misc_cog):
        """Test _is_custom_emoji with valid emoji."""
        assert misc_cog._is_custom_emoji("<:smile:123456789012345678>") is True
    
    def test_is_custom_emoji_false(self, misc_cog):
        """Test _is_custom_emoji with invalid emoji."""
        assert misc_cog._is_custom_emoji(":smile:") is False
        assert misc_cog._is_custom_emoji("hello") is False
        assert misc_cog._is_custom_emoji("<smile>") is False
        assert misc_cog._is_custom_emoji("<:smile") is False
    
    def test_process_user_mention_valid(self, misc_cog, mock_ctx):
        """Test _process_user_mention with valid mention."""
        mock_member = MagicMock()
        mock_member.display_name = "MentionedUser"
        mock_ctx.guild.get_member.return_value = mock_member
        
        result = misc_cog._process_user_mention(mock_ctx, "<@!123456789>")
        assert result == "@MentionedUser"
    
    def test_process_user_mention_invalid(self, misc_cog, mock_ctx):
        """Test _process_user_mention with invalid mention."""
        mock_ctx.guild.get_member.return_value = None
        
        result = misc_cog._process_user_mention(mock_ctx, "<@!123456789>")
        assert result == "<@!123456789>"
    
    def test_process_user_mention_value_error(self, misc_cog, mock_ctx):
        """Test _process_user_mention with invalid ID."""
        result = misc_cog._process_user_mention(mock_ctx, "<@!invalid>")
        assert result == "<@!invalid>"
    
    def test_process_custom_emoji_valid(self, misc_cog):
        """Test _process_custom_emoji with valid emoji."""
        result = misc_cog._process_custom_emoji("<:smile:123456789012345678>")
        assert result == "smile"
    
    def test_process_custom_emoji_invalid_length(self, misc_cog):
        """Test _process_custom_emoji with invalid ID length."""
        result = misc_cog._process_custom_emoji("<:smile:123>")
        assert result == "<:smile:123>"
    
    def test_process_custom_emoji_invalid_format(self, misc_cog):
        """Test _process_custom_emoji with invalid format."""
        result = misc_cog._process_custom_emoji("<:smile>")
        assert result == "<:smile>"
    
    # Test static helper methods
    def test_categorize_invites(self, misc_cog):
        """Test _categorize_invites static method."""
        # Create mock invites
        unlimited_invite = MagicMock()
        unlimited_invite.revoked = False
        unlimited_invite.max_age = 0
        unlimited_invite.code = "unlimited"
        unlimited_invite.channel = "general"
        unlimited_invite.inviter = "User1"
        unlimited_invite.url = "https://discord.gg/unlimited"
        
        limited_invite = MagicMock()
        limited_invite.revoked = False
        limited_invite.max_age = 3600
        limited_invite.code = "limited"
        limited_invite.channel = "random"
        limited_invite.inviter = "User2"
        limited_invite.url = "https://discord.gg/limited"
        
        revoked_invite = MagicMock()
        revoked_invite.revoked = True
        revoked_invite.code = "revoked"
        revoked_invite.channel = "old"
        revoked_invite.inviter = "User3"
        
        invites = [unlimited_invite, limited_invite, revoked_invite]
        result = misc_cog._categorize_invites(invites)
        
        assert len(result["unlimited"]) == 1
        assert len(result["limited"]) == 1
        assert len(result["revoked"]) == 1
        assert "unlimited" in result["unlimited"][0]
        assert "limited" in result["limited"][0]
        assert "revoked" in result["revoked"][0]
    
    def test_calculate_server_stats(self, misc_cog, mock_ctx):
        """Test _calculate_server_stats static method."""
        # Setup members
        online_user = MagicMock()
        online_user.bot = False
        online_user.status = discord.Status.online
        
        idle_user = MagicMock()
        idle_user.bot = False
        idle_user.status = discord.Status.idle
        
        offline_user = MagicMock()
        offline_user.bot = False
        offline_user.status = discord.Status.offline
        
        bot_user = MagicMock()
        bot_user.bot = True
        bot_user.status = discord.Status.online
        
        mock_ctx.guild.members = [online_user, idle_user, offline_user, bot_user]
        mock_ctx.guild.text_channels = ["ch1", "ch2"]
        mock_ctx.guild.voice_channels = ["vc1"]
        
        result = misc_cog._calculate_server_stats(mock_ctx.guild)
        
        assert result["online"] == 3  # online + idle (including bot)
        assert result["users"] == 3  # non-bot users
        assert result["bots"] == 1  # bot users
        assert result["text_channels"] == 2
        assert result["voice_channels"] == 1
    
    def test_get_user_info(self, misc_cog, mock_ctx, mock_member):
        """Test _get_user_info static method."""
        # Setup guild members for member number calculation
        older_member = MagicMock()
        older_member.joined_at = datetime(2020, 1, 1, tzinfo=timezone.utc)
        mock_member.joined_at = datetime(2021, 1, 1, tzinfo=timezone.utc)
        newer_member = MagicMock()
        newer_member.joined_at = datetime(2022, 1, 1, tzinfo=timezone.utc)
        
        # Important: use the exact same mock_member object in the list
        mock_ctx.guild.members = [older_member, mock_member, newer_member]
        
        # Setup member roles
        role1 = MagicMock()
        role1.name = "Role1"
        role2 = MagicMock()
        role2.name = "@everyone"
        role3 = MagicMock()
        role3.name = "Role3"
        mock_member.roles = [role1, role2, role3]
        
        with patch('src.bot.cogs.misc.bot_utils.get_current_date_time', return_value=datetime.now(timezone.utc)):
            result = misc_cog._get_user_info(mock_ctx.guild, mock_member)
        
        assert "created_on" in result
        assert "joined_on" in result
        assert result["member_number"] == 2  # Second to join
        assert result["roles"] == "Role1, Role3"  # Excludes @everyone
        assert result["user_id"] == 99999
    
    def test_get_activity_description_playing(self, misc_cog, mock_member):
        """Test _get_activity_description with playing activity."""
        mock_activity = MagicMock()
        mock_activity.type = discord.ActivityType.playing
        mock_activity.name = "Minecraft"
        mock_member.activity = mock_activity
        
        result = misc_cog._get_activity_description(mock_member)
        assert result == "Playing Minecraft"
    
    def test_get_activity_description_streaming(self, misc_cog, mock_member):
        """Test _get_activity_description with streaming activity."""
        mock_activity = MagicMock()
        mock_activity.type = discord.ActivityType.streaming
        mock_activity.name = "Game Stream"
        mock_activity.details = "https://twitch.tv/user"
        mock_member.activity = mock_activity
        
        result = misc_cog._get_activity_description(mock_member)
        assert result == "Streaming: [Game Stream](https://twitch.tv/user)"
    
    def test_get_activity_description_dnd(self, misc_cog, mock_member):
        """Test _get_activity_description with DND status."""
        mock_member.activity = None
        mock_member.status = discord.Status.dnd
        
        result = misc_cog._get_activity_description(mock_member)
        assert result == messages.DO_NOT_DISTURB
    
    def test_get_activity_description_other_activity(self, misc_cog, mock_member):
        """Test _get_activity_description with other activity type."""
        mock_activity = MagicMock()
        mock_activity.type = discord.ActivityType.listening
        mock_member.activity = mock_activity
        mock_member.status = discord.Status.online
        
        result = misc_cog._get_activity_description(mock_member)
        assert result == "online"
    
    def test_get_games_included_single(self, misc_cog):
        """Test _get_games_included with single game."""
        result = misc_cog._get_games_included(("Game1",))
        assert result == "Game1"
    
    def test_get_games_included_multiple(self, misc_cog):
        """Test _get_games_included with multiple games."""
        result = misc_cog._get_games_included(("Game1", "Game2", "Game3"))
        assert result == "(Game1) (Game2) (Game3)"
    
    def test_get_games_included_empty(self, misc_cog):
        """Test _get_games_included with empty tuple."""
        result = misc_cog._get_games_included(())
        assert result is None
    
    @pytest.mark.asyncio
    async def test_setup_function(self, mock_bot):
        """Test the setup function."""
        from src.bot.cogs.misc import setup
        
        await setup(mock_bot)
        
        mock_bot.add_cog.assert_called_once()
        added_cog = mock_bot.add_cog.call_args[0][0]
        assert isinstance(added_cog, Misc)
        assert added_cog.bot == mock_bot
    
    def test_misc_cog_inheritance(self, misc_cog):
        """Test that Misc cog properly inherits from commands.Cog."""
        assert isinstance(misc_cog, commands.Cog)
        assert hasattr(misc_cog, 'bot')
    
    def test_process_tts_text_no_special_tokens(self, misc_cog, mock_ctx):
        """Test _process_tts_text with no special tokens."""
        result = misc_cog._process_tts_text(mock_ctx, "Hello world")
        assert result == "Hello world"
    
    def test_process_tts_text_with_special_tokens(self, misc_cog, mock_ctx):
        """Test _process_tts_text with special tokens."""
        mock_member = MagicMock()
        mock_member.display_name = "TestUser"
        mock_ctx.guild.get_member.return_value = mock_member
        
        result = misc_cog._process_tts_text(mock_ctx, "Hello <@!123456789> <:smile:123456789012345678>")
        assert "@TestUser" in result
        assert "smile" in result
