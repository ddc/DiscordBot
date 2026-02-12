import discord
from discord.ext import commands
from src.bot.cogs.admin.admin import Admin
from src.bot.constants import messages
from src.bot.discord_bot import Bot
from src.bot.tools import bot_utils, chat_formatting
from src.bot.tools.cooldowns import CoolDowns
from src.database.dal.bot.custom_commands_dal import CustomCommandsDal


class CustomCommand(Admin):
    """Admin commands for managing server-specific custom commands."""

    def __init__(self, bot: Bot) -> None:
        super().__init__(bot)


@CustomCommand.admin.group(aliases=["cc"])
async def custom_command(ctx: commands.Context) -> commands.Command | None:
    """Manage server custom commands.

    Available subcommands:
        admin cc add <command> <text> - Add a new custom command
        admin cc edit <command> <text> - Edit existing custom command
        admin cc remove <command> - Remove a custom command
        admin cc removeall - Remove all custom commands
        admin cc list - List all custom commands
    """
    return await bot_utils.invoke_subcommand(ctx, "admin cc")


@custom_command.command(name="add")
@commands.cooldown(1, CoolDowns.CustomCommand.value, commands.BucketType.user)
async def add_custom_command(ctx: commands.Context, *, subcommand_passed: str) -> None:
    """Add a new custom command to the server.

    The command name must be unique and not conflict with existing bot commands.
    The Maximum command name length is 20 characters.

    Usage:
        admin cc add hello there!
        admin cc add rules Please read our server rules
    """

    await bot_utils.delete_message(ctx)

    # Parse command arguments
    args = subcommand_passed.split()
    if len(args) < 2:
        help_msg = (
            f"{messages.MISSING_REQUIRED_ARGUMENT_HELP_MESSAGE}: "
            f"{chat_formatting.inline(f'{ctx.prefix}help admin cc add')}"
        )
        return await bot_utils.send_error_msg(ctx, help_msg)

    new_cmd_name = args[0]
    new_cmd_description = " ".join(args[1:])

    # Validate command name length
    if len(new_cmd_name) > 20:
        return await bot_utils.send_error_msg(ctx, messages.COMMAND_LENGHT_ERROR)

    # Check for conflicts with existing bot commands
    existing_commands = {cmd.name.lower() for cmd in ctx.bot.commands}
    if new_cmd_name.lower() in existing_commands:
        error_msg = f"`{ctx.prefix}{new_cmd_name}` {messages.ALREADY_A_STANDARD_COMMAND}."
        return await bot_utils.send_error_msg(ctx, error_msg)

    # Check if command already exists
    commands_dal = CustomCommandsDal(ctx.bot.db_session, ctx.bot.log)
    existing_command = await commands_dal.get_command(ctx.guild.id, new_cmd_name)

    if existing_command:
        warning_msg = (
            f"{messages.COMMAND_ALREADY_EXISTS}: `{ctx.prefix}{new_cmd_name}`\n"
            f"To edit: `{ctx.prefix}admin cc edit {new_cmd_name} <text>`"
        )
        return await bot_utils.send_warning_msg(ctx, warning_msg)

    # Add new command
    await commands_dal.insert_command(ctx.guild.id, ctx.author.id, new_cmd_name, new_cmd_description)
    success_msg = f"{messages.CUSTOM_COMMAND_ADDED}:\n`{ctx.prefix}{new_cmd_name}`"
    await bot_utils.send_msg(ctx, success_msg)
    return None


@custom_command.command(name="edit")
@commands.cooldown(1, CoolDowns.CustomCommand.value, commands.BucketType.user)
async def edit_custom_command(ctx: commands.Context, *, subcommand_passed: str) -> None:
    """Edit an existing custom command.

    Usage:
        admin cc edit hello there, friend!
        admin cc edit rules Please read our updated server rules
    """

    await bot_utils.delete_message(ctx)

    # Parse command arguments
    args = subcommand_passed.split()
    if len(args) < 2:
        help_msg = (
            f"{messages.MISSING_REQUIRED_ARGUMENT_HELP_MESSAGE}: "
            f"{chat_formatting.inline(f'{ctx.prefix}help admin cc edit')}"
        )
        return await bot_utils.send_error_msg(ctx, help_msg)

    cmd_name = args[0]
    new_cmd_description = " ".join(args[1:])

    # Get server commands
    commands_dal = CustomCommandsDal(ctx.bot.db_session, ctx.bot.log)
    server_commands = await commands_dal.get_all_server_commands(ctx.guild.id)

    if not server_commands:
        return await bot_utils.send_error_msg(ctx, messages.NO_CUSTOM_COMMANDS_FOUND)

    # Check if command exists
    command_names = {cmd["name"] for cmd in server_commands}
    if cmd_name not in command_names:
        error_msg = f"{messages.COMMAND_NOT_FOUND}:\n`{ctx.prefix}{cmd_name}`"
        return await bot_utils.send_error_msg(ctx, error_msg)

    # Update command
    await commands_dal.update_command_description(ctx.guild.id, ctx.author.id, cmd_name, new_cmd_description)
    success_msg = f"{messages.CUSTOM_COMMAND_EDITED}:\n`{ctx.prefix}{cmd_name}`"
    await bot_utils.send_msg(ctx, success_msg)
    return None


@custom_command.command(name="remove")
@commands.cooldown(1, CoolDowns.CustomCommand.value, commands.BucketType.user)
async def remove_custom_command(ctx: commands.Context, cmd_name: str) -> None:
    """Remove a specific custom command.

    Usage:
        admin cc remove hello
        admin cc remove rules
    """

    # Get server commands
    commands_dal = CustomCommandsDal(ctx.bot.db_session, ctx.bot.log)
    server_commands = await commands_dal.get_all_server_commands(ctx.guild.id)

    if not server_commands:
        return await bot_utils.send_warning_msg(ctx, messages.NO_CUSTOM_COMMANDS_FOUND)

    # Check if command exists
    command_names = {cmd["name"] for cmd in server_commands}
    if cmd_name not in command_names:
        error_msg = (
            f"{messages.CUSTOM_COMMAND_UNABLE_REMOVE}\n"
            f"{messages.COMMAND_NOT_FOUND}: {chat_formatting.inline(cmd_name)}"
        )
        return await bot_utils.send_error_msg(ctx, error_msg)

    # Remove command
    await commands_dal.delete_server_command(ctx.guild.id, cmd_name)
    success_msg = f"{messages.CUSTOM_COMMAND_REMOVED}:\n`{ctx.prefix}{cmd_name}`"
    await bot_utils.send_msg(ctx, success_msg)
    return None


@custom_command.command(name="removeall")
@commands.cooldown(1, CoolDowns.CustomCommand.value, commands.BucketType.user)
async def remove_all_custom_commands(ctx: commands.Context) -> None:
    """Remove all custom commands from the server.

    Usage:
        admin cc removeall
    """

    # Check if any commands exist
    commands_dal = CustomCommandsDal(ctx.bot.db_session, ctx.bot.log)
    server_commands = await commands_dal.get_all_server_commands(ctx.guild.id)

    if not server_commands:
        return await bot_utils.send_error_msg(ctx, messages.NO_CUSTOM_COMMANDS_FOUND)

    # Remove all commands
    await commands_dal.delete_all_commands(ctx.guild.id)
    await bot_utils.send_msg(ctx, messages.CUSTOM_COMMAND_ALL_REMOVED)
    return None


@custom_command.command(name="list")
@commands.cooldown(1, CoolDowns.CustomCommand.value, commands.BucketType.user)
async def list_custom_commands(ctx: commands.Context) -> None:
    """Display all custom commands for this server.

    Usage:
        admin cc list
    """

    # Get server commands
    commands_dal = CustomCommandsDal(ctx.bot.db_session, ctx.bot.log)
    server_commands = await commands_dal.get_all_server_commands(ctx.guild.id)

    if not server_commands:
        return await bot_utils.send_warning_msg(ctx, messages.NO_CUSTOM_COMMANDS_FOUND)

    # Format command data
    command_list = []
    author_list = []
    date_list = []

    for i, command_data in enumerate(server_commands, 1):
        # Get author info
        author = bot_utils.get_member_by_id(ctx.guild, command_data["created_by"])
        author_name = author.display_name if author else "Unknown User"

        # Format data
        command_list.append(f"{i}) {command_data['name']}")
        author_list.append(author_name)
        date_list.append(bot_utils.convert_datetime_to_str_short(command_data["created_at"])[:-7])

    # Create embed
    embed = discord.Embed()
    guild_icon_url = ctx.guild.icon.url if ctx.guild.icon else None
    embed.set_author(name=messages.CUSTOM_COMMANDS_SERVER, icon_url=guild_icon_url)

    embed.add_field(name="Command", value=chat_formatting.inline("\n".join(command_list)))
    embed.add_field(name="Created by", value=chat_formatting.inline("\n".join(author_list)))
    embed.add_field(name="Created at", value=chat_formatting.inline("\n".join(date_list)))
    embed.set_footer(text=f"For more info: {ctx.prefix}help admin cc")

    await bot_utils.send_embed(ctx, embed)
    return None


async def setup(bot: Bot) -> None:
    """Setup function to add the CustomCommand cog to the bot."""
    bot.remove_command("admin")
    await bot.add_cog(CustomCommand(bot))
