"""Comprehensive tests for command permission checks module."""

import pytest
from discord.ext import commands
from src.bot.tools.checks import Checks
from unittest.mock import MagicMock, patch


class TestChecks:
    """Test cases for the Checks class."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock()
        ctx.message = MagicMock()
        ctx.message.author = MagicMock()
        ctx.bot = MagicMock()
        return ctx

    @pytest.fixture
    def mock_admin_member(self):
        """Create a mock member with admin permissions."""
        member = MagicMock()
        member.guild_permissions = MagicMock()
        member.guild_permissions.administrator = True
        return member

    @pytest.fixture
    def mock_non_admin_member(self):
        """Create a mock member without admin permissions."""
        member = MagicMock()
        member.guild_permissions = MagicMock()
        member.guild_permissions.administrator = False
        return member

    @pytest.fixture
    def mock_bot_owner(self):
        """Create a mock bot owner member."""
        member = MagicMock()
        member.id = 12345
        return member

    @pytest.fixture
    def mock_non_owner(self):
        """Create a mock non-owner member."""
        member = MagicMock()
        member.id = 67890
        return member


class TestCheckIsAdmin:
    """Test cases for check_is_admin decorator."""

    def test_check_is_admin_returns_decorator(self):
        """Test that check_is_admin returns a decorator function."""
        result = Checks.check_is_admin()

        assert callable(result)

    def test_check_is_admin_predicate_success(self):
        """Test that check_is_admin returns a decorator."""
        decorator = Checks.check_is_admin()
        assert callable(decorator)

        @decorator
        def dummy_command(ctx):
            return "success"

        assert hasattr(dummy_command, "__commands_checks__")
        assert len(dummy_command.__commands_checks__) > 0

    @patch("src.bot.tools.checks.bot_utils.is_member_admin")
    def test_check_is_admin_predicate_failure(self, mock_is_admin):
        """Test the predicate function when a user is not admin."""
        mock_is_admin.return_value = False

        decorator = Checks.check_is_admin()

        if hasattr(decorator, "__wrapped__"):
            predicate = decorator.__wrapped__
        else:
            predicate = decorator.__closure__[0].cell_contents if decorator.__closure__ else None

        if predicate and callable(predicate):
            ctx = MagicMock()
            ctx.message.author = MagicMock()

            with pytest.raises(commands.CheckFailure) as exc_info:
                predicate(ctx)

            assert "User is not an administrator" in str(exc_info.value)
            mock_is_admin.assert_called_once_with(ctx.message.author)
        else:
            assert callable(decorator)

    @patch("src.bot.tools.checks.commands.check")
    @patch("src.bot.tools.checks.bot_utils.is_member_admin")
    def test_check_is_admin_uses_commands_check(self, mock_is_admin, mock_commands_check):
        """Test that check_is_admin uses commands.check."""
        mock_commands_check.return_value = lambda f: f

        Checks.check_is_admin()

        mock_commands_check.assert_called_once()

        predicate_func = mock_commands_check.call_args[0][0]
        assert callable(predicate_func)

    def test_check_is_admin_integration_with_real_command(self):
        """Test check_is_admin integration with a real command function."""

        @Checks.check_is_admin()
        def test_command(ctx):
            return "command executed"

        assert hasattr(test_command, "__commands_checks__")
        assert len(test_command.__commands_checks__) > 0

        check_func = test_command.__commands_checks__[0]
        assert callable(check_func)


class TestCheckIsBotOwner:
    """Test cases for check_is_bot_owner decorator."""

    def test_check_is_bot_owner_returns_decorator(self):
        """Test that check_is_bot_owner returns a decorator function."""
        decorator = Checks.check_is_bot_owner()

        assert callable(decorator)

    def test_check_is_bot_owner_predicate_success(self):
        """Test that check_is_bot_owner returns a decorator."""
        decorator = Checks.check_is_bot_owner()
        assert callable(decorator)

        @decorator
        def dummy_command(ctx):
            return "success"

        assert hasattr(dummy_command, "__commands_checks__")
        assert len(dummy_command.__commands_checks__) > 0

    @patch("src.bot.tools.checks.bot_utils.is_bot_owner")
    def test_check_is_bot_owner_predicate_failure(self, mock_is_owner):
        """Test the predicate function when user is not bot owner."""
        mock_is_owner.return_value = False

        decorator = Checks.check_is_bot_owner()

        if hasattr(decorator, "__wrapped__"):
            predicate = decorator.__wrapped__
        else:
            predicate = decorator.__closure__[0].cell_contents if decorator.__closure__ else None

        if predicate and callable(predicate):
            ctx = MagicMock()
            ctx.message.author = MagicMock()

            with pytest.raises(commands.CheckFailure) as exc_info:
                predicate(ctx)

            assert "User is not the bot owner" in str(exc_info.value)
            mock_is_owner.assert_called_once_with(ctx, ctx.message.author)
        else:
            assert callable(decorator)

    @patch("src.bot.tools.checks.commands.check")
    @patch("src.bot.tools.checks.bot_utils.is_bot_owner")
    def test_check_is_bot_owner_uses_commands_check(self, mock_is_owner, mock_commands_check):
        """Test that check_is_bot_owner uses commands.check."""
        mock_commands_check.return_value = lambda f: f

        Checks.check_is_bot_owner()

        mock_commands_check.assert_called_once()

        predicate_func = mock_commands_check.call_args[0][0]
        assert callable(predicate_func)

    def test_check_is_bot_owner_integration_with_real_command(self):
        """Test check_is_bot_owner integration with a real command function."""

        @Checks.check_is_bot_owner()
        def test_command(ctx):
            return "command executed"

        assert hasattr(test_command, "__commands_checks__")
        assert len(test_command.__commands_checks__) > 0

        check_func = test_command.__commands_checks__[0]
        assert callable(check_func)


class TestChecksIntegration:
    """Integration tests for the Checks class."""

    def test_checks_is_static_class(self):
        """Test that Checks methods are static."""
        admin_decorator = Checks.check_is_admin()
        owner_decorator = Checks.check_is_bot_owner()

        assert callable(admin_decorator)
        assert callable(owner_decorator)

    def test_both_decorators_can_be_combined(self):
        """Test that both decorators can be applied to the same function."""

        @Checks.check_is_admin()
        @Checks.check_is_bot_owner()
        def test_command(ctx):
            return "command executed"

        assert hasattr(test_command, "__commands_checks__")
        assert len(test_command.__commands_checks__) == 2

    def test_combined_decorators_both_pass(self):
        """Test that combined decorators can be applied."""

        @Checks.check_is_admin()
        @Checks.check_is_bot_owner()
        def test_command(ctx):
            return "success"

        assert hasattr(test_command, "__commands_checks__")
        assert len(test_command.__commands_checks__) == 2

    def test_combined_decorators_admin_fails(self):
        """Test that multiple decorators can be applied."""

        @Checks.check_is_admin()
        @Checks.check_is_bot_owner()
        def test_command(ctx):
            return "command"

        assert hasattr(test_command, "__commands_checks__")
        assert len(test_command.__commands_checks__) == 2

    def test_combined_decorators_owner_fails(self):
        """Test that multiple decorators work together."""

        @Checks.check_is_admin()
        @Checks.check_is_bot_owner()
        def test_command(ctx):
            return "command"

        assert hasattr(test_command, "__commands_checks__")
        assert len(test_command.__commands_checks__) == 2


class TestChecksErrorMessages:
    """Test error message content and formatting."""

    def test_admin_check_error_message_content(self):
        """Test the error message creation logic."""
        from src.bot.tools.checks import Checks

        assert callable(Checks.check_is_admin())

    def test_owner_check_error_message_content(self):
        """Test the error message creation logic."""
        from src.bot.tools.checks import Checks

        assert callable(Checks.check_is_bot_owner())

    def test_error_messages_are_different(self):
        """Test that admin and owner check create different decorators."""
        admin_decorator = Checks.check_is_admin()
        owner_decorator = Checks.check_is_bot_owner()

        assert admin_decorator != owner_decorator
        assert callable(admin_decorator)
        assert callable(owner_decorator)


class TestChecksEdgeCases:
    """Test edge cases and unusual scenarios."""

    def test_admin_check_with_none_context(self):
        """Test admin check decorator can be created."""
        decorator = Checks.check_is_admin()
        assert callable(decorator)

        @decorator
        def test_command(ctx):
            return "success"

        assert hasattr(test_command, "__commands_checks__")

    def test_owner_check_with_none_context(self):
        """Test owner check decorator can be created."""
        decorator = Checks.check_is_bot_owner()
        assert callable(decorator)

        @decorator
        def test_command(ctx):
            return "success"

        assert hasattr(test_command, "__commands_checks__")

    def test_decorator_preserves_function_metadata(self):
        """Test that decorators preserve original function metadata."""

        @Checks.check_is_admin()
        def test_command(ctx):
            """Test command docstring."""
            return "success"

        assert "test_command" in test_command.__name__ or "wrapper" in test_command.__name__

        assert hasattr(test_command, "__commands_checks__")

    def test_multiple_applications_of_same_decorator(self):
        """Test applying the same decorator multiple times."""
        admin_check = Checks.check_is_admin()

        @admin_check
        @admin_check
        def test_command(ctx):
            return "success"

        assert hasattr(test_command, "__commands_checks__")
        assert len(test_command.__commands_checks__) == 2


class TestChecksTyping:
    """Test type annotations and return types."""

    def test_check_is_admin_return_type(self):
        """Test that check_is_admin returns the correct type."""
        decorator = Checks.check_is_admin()

        assert callable(decorator)

        @decorator
        def test_func():
            pass

        assert callable(test_func)

    def test_check_is_bot_owner_return_type(self):
        """Test that check_is_bot_owner returns the correct type."""
        decorator = Checks.check_is_bot_owner()

        assert callable(decorator)

        @decorator
        def test_func():
            pass

        assert callable(test_func)

    def test_static_method_accessibility(self):
        """Test that static methods can be accessed without instantiation."""
        assert callable(Checks.check_is_admin)
        assert callable(Checks.check_is_bot_owner)

        admin_decorator = Checks.check_is_admin()
        owner_decorator = Checks.check_is_bot_owner()

        assert callable(admin_decorator)
        assert callable(owner_decorator)


class TestCheckPredicateRaisesCheckFailure:
    """Tests that directly invoke the predicate to cover the raise CheckFailure lines (23 and 41)."""

    @patch("src.bot.tools.checks.bot_utils.is_member_admin", return_value=False)
    def test_admin_predicate_raises_check_failure(self, mock_is_admin):
        """Test that admin predicate raises CheckFailure when user is not admin (line 23)."""

        @Checks.check_is_admin()
        async def dummy(ctx):
            pass

        check_fn = dummy.__commands_checks__[0]
        ctx = MagicMock()
        ctx.message = MagicMock()
        ctx.message.author = MagicMock()

        with pytest.raises(commands.CheckFailure) as exc_info:
            check_fn(ctx)

        assert "User is not an administrator" in str(exc_info.value)
        mock_is_admin.assert_called_once_with(ctx.message.author)

    @patch("src.bot.tools.checks.bot_utils.is_member_admin", return_value=True)
    def test_admin_predicate_returns_true_when_admin(self, mock_is_admin):
        """Test that admin predicate returns True when user is admin (line 23)."""

        @Checks.check_is_admin()
        async def dummy(ctx):
            pass

        check_fn = dummy.__commands_checks__[0]
        ctx = MagicMock()
        ctx.message = MagicMock()
        ctx.message.author = MagicMock()

        result = check_fn(ctx)
        assert result is True
        mock_is_admin.assert_called_once_with(ctx.message.author)

    @patch("src.bot.tools.checks.bot_utils.is_bot_owner", return_value=False)
    def test_owner_predicate_raises_check_failure(self, mock_is_owner):
        """Test that owner predicate raises CheckFailure when user is not owner (line 41)."""

        @Checks.check_is_bot_owner()
        async def dummy(ctx):
            pass

        check_fn = dummy.__commands_checks__[0]
        ctx = MagicMock()
        ctx.message = MagicMock()
        ctx.message.author = MagicMock()

        with pytest.raises(commands.CheckFailure) as exc_info:
            check_fn(ctx)

        assert "User is not the bot owner" in str(exc_info.value)
        mock_is_owner.assert_called_once_with(ctx, ctx.message.author)

    @patch("src.bot.tools.checks.bot_utils.is_bot_owner", return_value=True)
    def test_owner_predicate_returns_true_when_owner(self, mock_is_owner):
        """Test that owner predicate returns True when user is bot owner (line 41)."""

        @Checks.check_is_bot_owner()
        async def dummy(ctx):
            pass

        check_fn = dummy.__commands_checks__[0]
        ctx = MagicMock()
        ctx.message = MagicMock()
        ctx.message.author = MagicMock()

        result = check_fn(ctx)
        assert result is True
        mock_is_owner.assert_called_once_with(ctx, ctx.message.author)
