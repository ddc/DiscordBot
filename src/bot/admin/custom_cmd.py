# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from src.bot.admin.admin import Admin
from src.bot.utils import bot_utils, chat_formatting
from src.bot.utils.cooldowns import CoolDowns
from src.database.dal.bot.custom_commands_dal import CustomCommandsDal


class CustomCommand(Admin):
    """(Admin custom commands)"""
    def __init__(self, bot):
        super().__init__(bot)


@CustomCommand.admin.group(aliases=["cc"])
async def custom_command(ctx, subcommand):
    """(Add, remove, edit, list custom commands)

    Example:
    admin cc add <command> <text/url>
    admin cc edit <command> <text/url>
    admin cc remove <command>
    admin cc removeall
    admin cc list
    """

    match subcommand:
        case "add":
            await add_custom_command(ctx)
        case "edit":
            await edit_custom_command(ctx)
        case "remove":
            await remove_custom_command(ctx)
        case "removeall":
            await remove_all_custom_commands(ctx)
        case "list":
            await list_custom_commands(ctx)
        case _:
            if ctx.command is not None:
                cmd = ctx.command
            else:
                cmd = ctx.bot.get_command("admin config")
            await bot_utils.send_help_msg(ctx, cmd)


@custom_command.command(name="add")
@commands.cooldown(1, CoolDowns.CustomComand.value, BucketType.user)
async def add_custom_command(ctx):
    """(Adds a custom command)

    Example:
    admin cc add <command> <text/url>
    """

    await bot_utils.delete_channel_message(ctx)
    cmd_name = ctx.subcommand_passed
    description = " ".join(ctx.message.content.split()[4:])

    if not cmd_name or len(description) == 0:
        return await bot_utils.send_error_msg(ctx, "Missing required argument!!!\n"
                                                   "For more info on this command use: "
                                                   f"{chat_formatting.inline('?help admin cc add')}")

    for cmd in ctx.bot.commands:
        if str(cmd_name) == str(cmd.name).lower():
            await bot_utils.send_error_msg(ctx, f"`{ctx.prefix}{cmd_name}` is already a standard command.")
            return

    if len(cmd_name) > 20:
        await bot_utils.send_error_msg(ctx, "Command names cannot exceed 20 characters.\n"
                                            "Please try again with another name.")
        return

    commands_dal = CustomCommandsDal(ctx.bot.db_session, ctx.bot.log)
    rs = await commands_dal.get_command(ctx.guild.id, str(cmd_name))
    if len(rs) == 0:
        await commands_dal.insert_command(ctx.guild.id, ctx.author.id, cmd_name, description)
        await bot_utils.send_msg(ctx, f"Custom command successfully added:\n`{ctx.prefix}{cmd_name}`")
    else:
        await bot_utils.send_warning_msg(ctx, f"Command already exists: `{ctx.prefix}{cmd_name}`\n"
                                              f"To edit use: `{ctx.prefix}admin cc edit {cmd_name} <text/url>`")


@custom_command.command(name="remove")
@commands.cooldown(1, CoolDowns.CustomComand.value, BucketType.user)
async def remove_custom_command(ctx):
    """(Removes a custom command)

    Example:
    admin cc remove <command>
    """

    cmd_name = ctx.subcommand_passed
    if not cmd_name:
        return await bot_utils.send_error_msg(ctx, "Missing required argument!!!\n"
                                                   "For more info on this command use: "
                                                   f"{chat_formatting.inline('?help admin cc remove')}")

    commands_dal = CustomCommandsDal(ctx.bot.db_session, ctx.bot.log)
    rs = await commands_dal.get_all_server_commands(ctx.guild.id)
    if len(rs) == 0:
        return await bot_utils.send_warning_msg(ctx, "There are no custom commands in this server.")

    if cmd_name in [x.name for x in rs]:
        await commands_dal.delete_server_command(ctx.guild.id, str(cmd_name))
        await bot_utils.send_msg(ctx, f"Custom command successfully removed:\n`{ctx.prefix}{cmd_name}`")
    else:
        await bot_utils.send_error_msg(ctx, "That command doesn't exist.")


@custom_command.command(name="edit")
@commands.cooldown(1, CoolDowns.CustomComand.value, BucketType.user)
async def edit_custom_command(ctx):
    """(Edits a custom command)

    Example:
    admin cc edit <command> <text/url>
    """

    await bot_utils.delete_channel_message(ctx)
    cmd_name = ctx.subcommand_passed
    description = " ".join(ctx.message.content.split()[4:])

    if not cmd_name or len(description) == 0:
        return await bot_utils.send_error_msg(ctx, "Missing required argument!!!\n"
                                                   "For more info on this command use: "
                                                   f"{chat_formatting.inline('?help admin cc edit')}")

    commands_dal = CustomCommandsDal(ctx.bot.db_session, ctx.bot.log)
    rs = await commands_dal.get_all_server_commands(ctx.guild.id)
    if len(rs) == 0:
        await bot_utils.send_error_msg(ctx, "There are no custom commands in this server.")
        return

    if cmd_name in [x.name for x in rs]:
        await commands_dal.update_command_description(ctx.guild.id, ctx.author.id, cmd_name, description)
        await bot_utils.send_msg(ctx, f"Custom command successfully edited:\n`{ctx.prefix}{cmd_name}`")
    else:
        await bot_utils.send_error_msg(ctx, f"Command doesn't exist:\n`{ctx.prefix}{cmd_name}`")


@custom_command.command(name="removeall")
@commands.cooldown(1, CoolDowns.CustomComand.value, BucketType.user)
async def remove_all_custom_commands(ctx):
    """(Removes all custom commands)

    Example:
    admin cc removeall
    """

    commands_dal = CustomCommandsDal(ctx.bot.db_session, ctx.bot.log)
    rs = await commands_dal.get_all_server_commands(ctx.guild.id)
    if len(rs) == 0:
        await bot_utils.send_error_msg(ctx, "There are no custom commands in this server.")
        return

    await commands_dal.delete_all_commands(ctx.guild.id)
    await bot_utils.send_msg(ctx, "All custom commands from this server were successfully removed.")


@custom_command.command(name="list")
@commands.cooldown(1, CoolDowns.CustomComand.value, BucketType.user)
async def list_custom_commands(ctx):
    """(Shows custom commands list)

    Example:
    admin cc list
    """

    commands_dal = CustomCommandsDal(ctx.bot.db_session, ctx.bot.log)
    rs = await commands_dal.get_all_server_commands(ctx.guild.id)
    if len(rs) == 0:
        await bot_utils.send_warning_msg(ctx, "There are no custom commands in this server.")
        return

    command = []
    author = []
    date = []
    for i, each in enumerate(rs, 1):
        author_name = bot_utils.get_member_name_by_id(ctx, each["created_by"])
        command.append(f"{i}) {each['name']}")
        author.append(author_name)
        date.append(str(each['created_at'])[:-7])

    cmd = '\n'.join(command)
    authors = '\n'.join(author)
    dates = '\n'.join(date)

    embed = discord.Embed()
    embed.set_footer(text=f"For more info: {ctx.prefix}help admin cc")
    embed.set_author(name="Custom commands in this server", icon_url=f"{ctx.guild.icon.url}")
    embed.add_field(name="Command", value=chat_formatting.inline(cmd), inline=True)
    embed.add_field(name="Created by", value=chat_formatting.inline(authors), inline=True)
    embed.add_field(name="Created at", value=chat_formatting.inline(dates), inline=True)
    await bot_utils.send_embed(ctx, embed)


async def setup(bot):
    bot.remove_command("admin")
    await bot.add_cog(CustomCommand(bot))
