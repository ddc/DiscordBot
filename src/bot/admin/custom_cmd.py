# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from src.bot.admin.admin import Admin
from src.bot.constants import messages
from src.bot.tools import bot_utils, chat_formatting
from src.bot.tools.cooldowns import CoolDowns
from src.database.dal.bot.custom_commands_dal import CustomCommandsDal


class CustomCommand(Admin):
    """(Admin Users Custom Commands)"""
    def __init__(self, bot):
        super().__init__(bot)


@CustomCommand.admin.group(aliases=["cc"])
async def custom_command(ctx):
    """(Add, remove, edit, list custom commands)
            admin cc add <command> <text>
            admin cc edit <command> <text>
            admin cc remove <command>
            admin cc removeall
            admin cc list
    """

    await bot_utils.invoke_subcommand(ctx, "admin cc")


@custom_command.command(name="add")
@commands.cooldown(1, CoolDowns.CustomComand.value, BucketType.user)
async def add_custom_command(ctx, *, subcommand_passed):
    """(Adds a custom command)
            admin cc add <command> <text>
    """

    await bot_utils.delete_message(ctx)
    new_cmd_name = subcommand_passed.split()[0]
    new_cmd_description = " ".join(subcommand_passed.split()[1:])

    if not new_cmd_name or len(new_cmd_description) == 0:
        return await bot_utils.send_error_msg(ctx, f"{messages.MISSING_REQUIRED_ARGUMENT_HELP_MESSAGE}: "
                                                   f"{chat_formatting.inline(f'{ctx.prefix}help admin cc add')}")

    for cmd in ctx.bot.commands:
        if str(new_cmd_name) == str(cmd.name).lower():
            await bot_utils.send_error_msg(ctx, f"`{ctx.prefix}{new_cmd_name}` {messages.ALREADY_A_STANDARD_COMMAND}.")
            return

    if len(new_cmd_name) > 20:
        await bot_utils.send_error_msg(ctx, messages.COMMAND_LENGHT_ERROR)
        return

    commands_dal = CustomCommandsDal(ctx.bot.db_session, ctx.bot.log)
    rs = await commands_dal.get_command(ctx.guild.id, str(new_cmd_name))
    if not rs:
        await commands_dal.insert_command(ctx.guild.id, ctx.author.id, new_cmd_name, new_cmd_description)
        await bot_utils.send_msg(ctx, f"{messages.CUSTOM_COMMAND_ADDED}:\n`{ctx.prefix}{new_cmd_name}`")
    else:
        await bot_utils.send_warning_msg(ctx, f"{messages.COMMAND_ALREADY_EXISTS}: `{ctx.prefix}{new_cmd_name}`\n"
                                              f"To edit: `{ctx.prefix}admin cc edit {new_cmd_name} <text>`")


@custom_command.command(name="edit")
@commands.cooldown(1, CoolDowns.CustomComand.value, BucketType.user)
async def edit_custom_command(ctx, *, subcommand_passed):
    """(Edits a custom command)
            admin cc edit <command> <text>
    """

    await bot_utils.delete_message(ctx)
    cmd_name = subcommand_passed.split()[0]
    new_cmd_description = " ".join(subcommand_passed.split()[1:])

    if not cmd_name or len(new_cmd_description) == 0:
        return await bot_utils.send_error_msg(ctx, f"{messages.MISSING_REQUIRED_ARGUMENT_HELP_MESSAGE}: "
                                                   f"{chat_formatting.inline(f'{ctx.prefix}help admin cc edit')}")

    commands_dal = CustomCommandsDal(ctx.bot.db_session, ctx.bot.log)
    rs = await commands_dal.get_all_server_commands(ctx.guild.id)
    if not rs:
        return await bot_utils.send_error_msg(ctx, messages.NO_CUSTOM_COMMANDS_FOUND)

    if cmd_name in [x.name for x in rs]:
        await commands_dal.update_command_description(ctx.guild.id, ctx.author.id, cmd_name, new_cmd_description)
        await bot_utils.send_msg(ctx, f"{messages.CUSTOM_COMMAND_EDITED}:\n`{ctx.prefix}{cmd_name}`")
    else:
        await bot_utils.send_error_msg(ctx, f"{messages.COMMAND_NOT_FOUND}:\n`{ctx.prefix}{cmd_name}`")


@custom_command.command(name="remove")
@commands.cooldown(1, CoolDowns.CustomComand.value, BucketType.user)
async def remove_custom_command(ctx, cmd_name):
    """(Removes a custom command)
            admin cc remove <command>
    """

    if not cmd_name:
        return await bot_utils.send_error_msg(ctx, f"{messages.MISSING_REQUIRED_ARGUMENT_HELP_MESSAGE}: "
                                                   f"{chat_formatting.inline(f'{ctx.prefix}help admin cc remove')}")

    commands_dal = CustomCommandsDal(ctx.bot.db_session, ctx.bot.log)
    rs = await commands_dal.get_all_server_commands(ctx.guild.id)
    if not rs:
        return await bot_utils.send_warning_msg(ctx, messages.NO_CUSTOM_COMMANDS_FOUND)

    if cmd_name in [x.name for x in rs]:
        await commands_dal.delete_server_command(ctx.guild.id, str(cmd_name))
        await bot_utils.send_msg(ctx, f"{messages.CUSTOM_COMMAND_REMOVED}:\n`{ctx.prefix}{cmd_name}`")
    else:
        await bot_utils.send_error_msg(ctx, f"{messages.CUSTOM_COMMAND_UNABLE_REMOVE}\n"
                                            f"{messages.COMMAND_NOT_FOUND}: {chat_formatting.inline(cmd_name)}")


@custom_command.command(name="removeall")
@commands.cooldown(1, CoolDowns.CustomComand.value, BucketType.user)
async def remove_all_custom_commands(ctx):
    """(Removes all custom commands)
            admin cc removeall
    """

    commands_dal = CustomCommandsDal(ctx.bot.db_session, ctx.bot.log)
    rs = await commands_dal.get_all_server_commands(ctx.guild.id)
    if not rs:
        return await bot_utils.send_error_msg(ctx, messages.NO_CUSTOM_COMMANDS_FOUND)

    await commands_dal.delete_all_commands(ctx.guild.id)
    await bot_utils.send_msg(ctx, messages.CUSTOM_COMMAND_ALL_REMOVED)


@custom_command.command(name="list")
@commands.cooldown(1, CoolDowns.CustomComand.value, BucketType.user)
async def list_custom_commands(ctx):
    """(Shows custom commands list)
            admin cc list
    """

    commands_dal = CustomCommandsDal(ctx.bot.db_session, ctx.bot.log)
    rs = await commands_dal.get_all_server_commands(ctx.guild.id)
    if not rs:
        return await bot_utils.send_warning_msg(ctx, messages.NO_CUSTOM_COMMANDS_FOUND)

    command = []
    author = []
    date = []
    for i, each in enumerate(rs, 1):
        author_name = bot_utils.get_member_by_id(ctx.guild, each["created_by"])
        command.append(f"{i}) {each['name']}")
        author.append(author_name.display_name)
        date.append(bot_utils.convert_datetime_to_str_short(each["created_at"])[:-7])

    cmd = "\n".join(command)
    authors = "\n".join(author)
    dates = "\n".join(date)

    embed = discord.Embed()
    embed.set_author(name=messages.CUSTOM_COMMANDS_SERVER, icon_url=f"{ctx.guild.icon.url}")
    embed.add_field(name="Command", value=chat_formatting.inline(cmd))
    embed.add_field(name="Created by", value=chat_formatting.inline(authors))
    embed.add_field(name="Created at", value=chat_formatting.inline(dates))
    embed.set_footer(text=f"For more info: {ctx.prefix}help admin cc")
    await bot_utils.send_embed(ctx, embed)


async def setup(bot):
    bot.remove_command("admin")
    await bot.add_cog(CustomCommand(bot))
