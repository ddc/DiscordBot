import discord
import pytest

# Mock problematic imports before importing the module
import sys
from unittest.mock import AsyncMock, MagicMock, Mock, patch

sys.modules["ddcDatabases"] = Mock()

from src.bot.cogs.dice_rolls import DiceRolls
from src.bot.constants import messages


@pytest.fixture
def mock_bot():
    bot = AsyncMock()
    bot.db_session = MagicMock()
    bot.log = MagicMock()
    return bot


@pytest.fixture
def dice_cog(mock_bot):
    return DiceRolls(mock_bot)


@pytest.fixture
def mock_ctx():
    ctx = AsyncMock()
    ctx.guild = MagicMock()
    ctx.guild.id = 12345
    ctx.guild.name = "Test Server"
    ctx.guild.icon = MagicMock()
    ctx.guild.icon.url = "https://example.com/icon.png"

    # Set author as the actual attributes, not AsyncMock
    author = MagicMock()
    author.id = 67890
    author.display_name = "TestUser"
    author.avatar = MagicMock()
    author.avatar.url = "https://example.com/avatar.png"

    ctx.author = author  # Direct assignment
    ctx.message = MagicMock()
    ctx.message.author = author  # Same reference
    ctx.message.channel = AsyncMock()
    ctx.message.content = "!roll"

    ctx.invoked_subcommand = None
    ctx.subcommand_passed = None
    ctx.prefix = "!"

    return ctx


class TestDiceRolls:
    @pytest.mark.asyncio
    async def test_init(self, mock_bot):
        cog = DiceRolls(mock_bot)
        assert cog.bot == mock_bot

    @pytest.mark.asyncio
    @patch("src.bot.cogs.dice_rolls.random.SystemRandom")
    @patch("src.bot.cogs.dice_rolls.DiceRollsDal")
    @patch("src.bot.cogs.dice_rolls.bot_utils.send_embed")
    async def test_roll_default_dice_size(self, mock_send_embed, mock_dal_class, mock_random, dice_cog, mock_ctx):
        # Setup
        mock_random_instance = MagicMock()
        mock_random.return_value = mock_random_instance
        mock_random_instance.randint.return_value = 42

        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_user_roll_by_dice_size.return_value = None
        mock_dal.insert_user_roll.return_value = None
        mock_dal.get_server_max_roll.return_value = []

        # Execute
        await dice_cog.roll.callback(dice_cog, mock_ctx)

        # Verify
        mock_ctx.message.channel.typing.assert_called_once()
        mock_random_instance.randint.assert_called_once_with(1, 100)
        mock_dal.get_user_roll_by_dice_size.assert_called_once_with(12345, 67890, 100)
        mock_dal.insert_user_roll.assert_called_once_with(12345, 67890, 100, 42)
        mock_send_embed.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.bot.cogs.dice_rolls.random.SystemRandom")
    @patch("src.bot.cogs.dice_rolls.DiceRollsDal")
    @patch("src.bot.cogs.dice_rolls.bot_utils.send_embed")
    async def test_roll_custom_dice_size(self, mock_send_embed, mock_dal_class, mock_random, dice_cog, mock_ctx):
        # Setup
        mock_ctx.subcommand_passed = "20"
        mock_random_instance = MagicMock()
        mock_random.return_value = mock_random_instance
        mock_random_instance.randint.return_value = 15

        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_user_roll_by_dice_size.return_value = None
        mock_dal.insert_user_roll.return_value = None
        mock_dal.get_server_max_roll.return_value = []

        # Execute
        await dice_cog.roll.callback(dice_cog, mock_ctx)

        # Verify
        mock_random_instance.randint.assert_called_once_with(1, 20)
        mock_dal.get_user_roll_by_dice_size.assert_called_once_with(12345, 67890, 20)
        mock_dal.insert_user_roll.assert_called_once_with(12345, 67890, 20, 15)

    @pytest.mark.asyncio
    @patch("src.bot.cogs.dice_rolls.bot_utils.send_error_msg")
    async def test_roll_invalid_dice_size(self, mock_send_error, dice_cog, mock_ctx):
        # Setup
        mock_ctx.subcommand_passed = "invalid"

        # Execute
        await dice_cog.roll.callback(dice_cog, mock_ctx)

        # Verify
        mock_send_error.assert_called_once_with(mock_ctx, messages.DICE_SIZE_NOT_VALID)

    @pytest.mark.asyncio
    @patch("src.bot.cogs.dice_rolls.bot_utils.send_error_msg")
    async def test_roll_dice_size_too_small(self, mock_send_error, dice_cog, mock_ctx):
        # Setup
        mock_ctx.subcommand_passed = "1"

        # Execute
        await dice_cog.roll.callback(dice_cog, mock_ctx)

        # Verify
        mock_send_error.assert_called_once_with(mock_ctx, messages.DICE_SIZE_HIGHER_ONE)

    @pytest.mark.asyncio
    @patch("src.bot.cogs.dice_rolls.random.SystemRandom")
    @patch("src.bot.cogs.dice_rolls.DiceRollsDal")
    @patch("src.bot.cogs.dice_rolls.bot_utils.send_embed")
    @patch("src.bot.cogs.dice_rolls.bot_utils.get_member_by_id")
    async def test_roll_new_personal_record(
        self, mock_get_member, mock_send_embed, mock_dal_class, mock_random, dice_cog, mock_ctx
    ):
        # Setup
        mock_random_instance = MagicMock()
        mock_random.return_value = mock_random_instance
        mock_random_instance.randint.return_value = 90

        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_user_roll_by_dice_size.return_value = [{"roll": 50}]
        mock_dal.update_user_roll.return_value = None
        # Set up an existing server record higher than current roll so it's not a server record
        mock_dal.get_server_max_roll.return_value = [{"user_id": 99999, "max_roll": 95}]

        # Mock the other user who holds the server record
        other_user = MagicMock()
        other_user.id = 99999
        other_user.display_name = "OtherUser"
        mock_get_member.return_value = other_user

        # Execute
        await dice_cog.roll.callback(dice_cog, mock_ctx)

        # Verify
        mock_dal.update_user_roll.assert_called_once_with(12345, 67890, 100, 90)
        mock_send_embed.assert_called_once()

        # Check that embed contains personal record message
        embed_call = mock_send_embed.call_args[0][1]
        assert messages.MEMBER_HIGHEST_ROLL in embed_call.description

    @pytest.mark.asyncio
    @patch("src.bot.cogs.dice_rolls.random.SystemRandom")
    @patch("src.bot.cogs.dice_rolls.DiceRollsDal")
    @patch("src.bot.cogs.dice_rolls.bot_utils.send_embed")
    @patch("src.bot.cogs.dice_rolls.bot_utils.get_member_by_id")
    async def test_roll_new_server_record(
        self, mock_get_member, mock_send_embed, mock_dal_class, mock_random, dice_cog, mock_ctx
    ):
        # Setup
        mock_random_instance = MagicMock()
        mock_random.return_value = mock_random_instance
        mock_random_instance.randint.return_value = 95

        other_user = MagicMock()
        other_user.id = 11111
        mock_get_member.return_value = other_user

        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_user_roll_by_dice_size.return_value = [{"roll": 50}]
        mock_dal.update_user_roll.return_value = None
        mock_dal.get_server_max_roll.return_value = [{"user_id": 11111, "max_roll": 80}]

        # Execute
        await dice_cog.roll.callback(dice_cog, mock_ctx)

        # Verify
        embed_call = mock_send_embed.call_args[0][1]
        assert messages.SERVER_HIGHEST_ROLL_ANOUNCE in embed_call.description

    @pytest.mark.asyncio
    async def test_roll_with_invoked_subcommand(self, dice_cog, mock_ctx):
        # Setup
        mock_ctx.invoked_subcommand = "results"

        # Execute
        result = await dice_cog.roll.callback(dice_cog, mock_ctx)

        # Verify
        assert result == "results"
        mock_ctx.message.channel.typing.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.bot.cogs.dice_rolls.DiceRollsDal")
    @patch("src.bot.cogs.dice_rolls.bot_utils.send_embed")
    @patch("src.bot.cogs.dice_rolls.bot_utils.get_member_by_id")
    async def test_roll_results_default_dice_size(
        self, mock_get_member, mock_send_embed, mock_dal_class, dice_cog, mock_ctx
    ):
        # Setup
        mock_ctx.message.content = "!roll results"

        user1 = MagicMock()
        user1.display_name = "User1"
        user2 = MagicMock()
        user2.display_name = "User2"

        mock_get_member.side_effect = [user1, user2]

        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_all_server_rolls.return_value = [{"user_id": 1, "roll": 95}, {"user_id": 2, "roll": 80}]

        # Execute
        await dice_cog.roll_results.callback(dice_cog, mock_ctx)

        # Verify
        mock_dal.get_all_server_rolls.assert_called_once_with(12345, 100)
        mock_send_embed.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.bot.cogs.dice_rolls.DiceRollsDal")
    @patch("src.bot.cogs.dice_rolls.bot_utils.send_embed")
    @patch("src.bot.cogs.dice_rolls.bot_utils.get_member_by_id")
    async def test_roll_results_custom_dice_size(
        self, mock_get_member, mock_send_embed, mock_dal_class, dice_cog, mock_ctx
    ):
        # Setup
        mock_ctx.message.content = "!roll results 20"

        user1 = MagicMock()
        user1.display_name = "User1"

        mock_get_member.return_value = user1

        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_all_server_rolls.return_value = [{"user_id": 1, "roll": 18}]

        # Execute
        await dice_cog.roll_results.callback(dice_cog, mock_ctx)

        # Verify
        mock_dal.get_all_server_rolls.assert_called_once_with(12345, 20)

    @pytest.mark.asyncio
    @patch("src.bot.cogs.dice_rolls.DiceRollsDal")
    @patch("src.bot.cogs.dice_rolls.bot_utils.send_error_msg")
    async def test_roll_results_no_rolls_found(self, mock_send_error, mock_dal_class, dice_cog, mock_ctx):
        # Setup
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_all_server_rolls.return_value = None

        # Execute
        await dice_cog.roll_results.callback(dice_cog, mock_ctx)

        # Verify
        mock_send_error.assert_called_once_with(mock_ctx, messages.no_dice_size_rolls(100))

    @pytest.mark.asyncio
    @patch("src.bot.cogs.dice_rolls.bot_utils.send_error_msg")
    async def test_roll_results_invalid_dice_size(self, mock_send_error, dice_cog, mock_ctx):
        # Setup
        mock_ctx.message.content = "!roll results invalid"

        # Execute
        await dice_cog.roll_results.callback(dice_cog, mock_ctx)

        # Verify
        mock_send_error.assert_called_once_with(mock_ctx, messages.DICE_SIZE_NOT_VALID)

    @pytest.mark.asyncio
    @patch("src.bot.cogs.dice_rolls.DiceRollsDal")
    @patch("src.bot.cogs.dice_rolls.bot_utils.send_msg")
    async def test_roll_reset(self, mock_send_msg, mock_dal_class, dice_cog, mock_ctx):
        # Setup
        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.delete_all_server_rolls.return_value = None

        # Execute
        await dice_cog.roll_reset.callback(dice_cog, mock_ctx)

        # Verify
        mock_ctx.message.channel.typing.assert_called_once()
        mock_dal.delete_all_server_rolls.assert_called_once_with(12345)
        mock_send_msg.assert_called_once_with(mock_ctx, messages.DELETED_ALL_ROLLS)

    @pytest.mark.asyncio
    @patch("src.bot.cogs.dice_rolls.random.SystemRandom")
    @patch("src.bot.cogs.dice_rolls.DiceRollsDal")
    @patch("src.bot.cogs.dice_rolls.bot_utils.send_embed")
    @patch("src.bot.cogs.dice_rolls.bot_utils.get_member_by_id")
    async def test_roll_existing_user_no_new_record(
        self, mock_get_member, mock_send_embed, mock_dal_class, mock_random, dice_cog, mock_ctx
    ):
        # Setup
        mock_random_instance = MagicMock()
        mock_random.return_value = mock_random_instance
        mock_random_instance.randint.return_value = 30

        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_user_roll_by_dice_size.return_value = [{"roll": 80}]
        mock_dal.update_user_roll.return_value = None
        mock_dal.get_server_max_roll.return_value = []

        # Execute
        await dice_cog.roll.callback(dice_cog, mock_ctx)

        # Verify - should not call update_user_roll since 30 < 80
        mock_dal.update_user_roll.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.bot.cogs.dice_rolls.random.SystemRandom")
    @patch("src.bot.cogs.dice_rolls.DiceRollsDal")
    @patch("src.bot.cogs.dice_rolls.bot_utils.send_embed")
    @patch("src.bot.cogs.dice_rolls.bot_utils.get_member_by_id")
    async def test_roll_server_highest_user_is_current_user(
        self, mock_get_member, mock_send_embed, mock_dal_class, mock_random, dice_cog, mock_ctx
    ):
        # Setup
        mock_random_instance = MagicMock()
        mock_random.return_value = mock_random_instance
        mock_random_instance.randint.return_value = 95

        mock_get_member.return_value = mock_ctx.message.author

        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_user_roll_by_dice_size.return_value = [{"roll": 50}]
        mock_dal.update_user_roll.return_value = None
        mock_dal.get_server_max_roll.return_value = [{"user_id": 67890, "max_roll": 80}]

        # Execute
        await dice_cog.roll.callback(dice_cog, mock_ctx)

        # Verify
        embed_call = mock_send_embed.call_args[0][1]
        assert messages.MEMBER_SERVER_WINNER_ANOUNCE in embed_call.description

    @pytest.mark.asyncio
    @patch("src.bot.cogs.dice_rolls.random.SystemRandom")
    @patch("src.bot.cogs.dice_rolls.DiceRollsDal")
    @patch("src.bot.cogs.dice_rolls.bot_utils.send_embed")
    @patch("src.bot.cogs.dice_rolls.bot_utils.get_member_by_id")
    async def test_roll_server_highest_user_is_different_user(
        self, mock_get_member, mock_send_embed, mock_dal_class, mock_random, dice_cog, mock_ctx
    ):
        # Setup
        mock_random_instance = MagicMock()
        mock_random.return_value = mock_random_instance
        mock_random_instance.randint.return_value = 70

        other_user = MagicMock()
        other_user.id = 11111
        mock_get_member.side_effect = [other_user, other_user]

        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_user_roll_by_dice_size.return_value = [{"roll": 50}]
        mock_dal.update_user_roll.return_value = None
        mock_dal.get_server_max_roll.return_value = [{"user_id": 11111, "max_roll": 95}]

        # Execute
        await dice_cog.roll.callback(dice_cog, mock_ctx)

        # Verify
        embed_call = mock_send_embed.call_args[0][1]
        assert messages.MEMBER_HAS_HIGHEST_ROLL in embed_call.description
        assert messages.MEMBER_HIGHEST_ROLL in embed_call.description

    @pytest.mark.asyncio
    @patch("src.bot.cogs.dice_rolls.random.SystemRandom")
    @patch("src.bot.cogs.dice_rolls.DiceRollsDal")
    @patch("src.bot.cogs.dice_rolls.bot_utils.send_embed")
    async def test_roll_server_max_roll_with_null_max_roll(
        self, mock_send_embed, mock_dal_class, mock_random, dice_cog, mock_ctx
    ):
        # Setup
        mock_random_instance = MagicMock()
        mock_random.return_value = mock_random_instance
        mock_random_instance.randint.return_value = 50

        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_user_roll_by_dice_size.return_value = [{"roll": 30}]
        mock_dal.update_user_roll.return_value = None
        mock_dal.get_server_max_roll.return_value = [{"user_id": 11111, "max_roll": None}]

        # Execute
        await dice_cog.roll.callback(dice_cog, mock_ctx)

        # Verify - should handle None max_roll gracefully
        mock_send_embed.assert_called_once()

    @pytest.mark.asyncio
    async def test_setup_function(self, mock_bot):
        # Import the setup function
        from src.bot.cogs.dice_rolls import setup

        # Execute
        await setup(mock_bot)

        # Verify
        mock_bot.add_cog.assert_called_once()
        added_cog = mock_bot.add_cog.call_args[0][0]
        assert isinstance(added_cog, DiceRolls)
        assert added_cog.bot == mock_bot

    @pytest.mark.asyncio
    @patch("src.bot.cogs.dice_rolls.DiceRollsDal")
    @patch("src.bot.cogs.dice_rolls.bot_utils.send_embed")
    @patch("src.bot.cogs.dice_rolls.chat_formatting.inline")
    @patch("src.bot.cogs.dice_rolls.bot_utils.get_member_by_id")
    async def test_roll_results_embed_formatting(
        self, mock_get_member, mock_inline, mock_send_embed, mock_dal_class, dice_cog, mock_ctx
    ):
        # Setup
        user1 = MagicMock()
        user1.display_name = "User1"
        user2 = MagicMock()
        user2.display_name = "User2"

        mock_get_member.side_effect = [user1, user2]
        mock_inline.side_effect = lambda x: f"inline({x})"

        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_all_server_rolls.return_value = [{"user_id": 1, "roll": 95}, {"user_id": 2, "roll": 80}]

        # Execute
        await dice_cog.roll_results.callback(dice_cog, mock_ctx)

        # Verify embed structure
        mock_send_embed.assert_called_once()
        embed = mock_send_embed.call_args[0][1]

        # Check embed author
        assert embed.author.name == "Test Server (Dice Size: 100)"
        assert embed.author.icon_url == "https://example.com/icon.png"

        # Check fields
        assert len(embed.fields) == 2
        assert embed.fields[0].name == "Member"
        assert embed.fields[1].name == "Roll"

        # Check footer
        assert embed.footer.text == f"{messages.RESET_ALL_ROLLS}: !roll reset"

    @pytest.mark.asyncio
    @patch("src.bot.cogs.dice_rolls.random.SystemRandom")
    @patch("src.bot.cogs.dice_rolls.DiceRollsDal")
    @patch("src.bot.cogs.dice_rolls.bot_utils.send_embed")
    async def test_roll_embed_properties(self, mock_send_embed, mock_dal_class, mock_random, dice_cog, mock_ctx):
        # Setup
        mock_random_instance = MagicMock()
        mock_random.return_value = mock_random_instance
        mock_random_instance.randint.return_value = 42

        mock_dal = AsyncMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_user_roll_by_dice_size.return_value = None
        mock_dal.insert_user_roll.return_value = None
        mock_dal.get_server_max_roll.return_value = []

        # Execute
        await dice_cog.roll.callback(dice_cog, mock_ctx)

        # Verify embed properties
        embed = mock_send_embed.call_args[0][1]
        assert embed.color == discord.Color.red()
        assert embed.author.name == "TestUser"
        assert embed.author.icon_url == "https://example.com/avatar.png"
        assert ":game_die: 42 :game_die:" in embed.description
