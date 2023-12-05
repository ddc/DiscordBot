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
    dmin cc remove <command>
    admin cc removeall
    admin cc list
    """

    match subcommand:
        case "add":
            await add_custom_command()
        case "edit":
            await edit_custom_command()
        case "remove":
            await remove_custom_command()
        case "removeall":
            await remove_all_custom_commands()
        case "list":
            await list_custom_commands()
        case _:
            if ctx.command is not None:
                cmd = ctx.command
            else:
                cmd = ctx.bot.get_command("admin config")
            await bot_utils.send_help_msg(ctx, cmd)


@custom_command.command(name="add")
@commands.cooldown(1, CoolDowns.CustomComand.value, BucketType.user)
async def add_custom_command(self, ctx, command_name: str, *, text: str):
    """(Adds a custom command)

    Example:
    admin cc add <command> <text/url>
    """

    await bot_utils.delete_channel_message(ctx)
    server = ctx.guild
    command_name = command_name.lower()
    for cmd in self.bot.commands:
        if str(command_name) == str(cmd.name).lower():
            await bot_utils.send_error_msg(ctx, f"`{ctx.prefix}{command_name}` is already a standard command.")
            return

    if len(command_name) > 20:
        await bot_utils.send_error_msg(ctx, "Command names cannot exceed 20 characters.\n" \
                                              "Please try again with another name.")
        return

    commands_dal = CustomCommandsDal(self.bot.db_session, self.bot.log)
    rs = await commands_dal.get_command(server.id, str(command_name))
    if len(rs) == 0:
        await commands_dal.insert_command(ctx.author, str(command_name), str(text))
        await bot_utils.send_msg(ctx, f"Custom command successfully added:\n`{ctx.prefix}{command_name}`")
    else:
        await bot_utils.send_error_msg(ctx,
                                   f"Command already exists: `{ctx.prefix}{command_name}`\n"
                                   f"To edit use: `{ctx.prefix}admin cc edit {command_name} <text/url>`")


@custom_command.command(name="remove")
@commands.cooldown(1, CoolDowns.CustomComand.value, BucketType.user)
async def remove_custom_command(self, ctx, command_name: str):
    """(Removes a custom command)

    Example:
    admin cc remove <command>
    """

    server = ctx.guild
    command_name = command_name.lower()

    commands_dal = CustomCommandsDal(self.bot.db_session, self.bot.log)
    rs = await commands_dal.get_all_commands(server.id)
    if len(rs) == 0:
        await bot_utils.send_error_msg(ctx, "There are no custom commands in this server.")
        return

    rs = await commands_dal.get_command(server.id, str(command_name))
    if len(rs) > 0:
        await commands_dal.delete_command(server.id, str(command_name))
        await bot_utils.send_msg(ctx, f"Custom command successfully removed:\n`{ctx.prefix}{command_name}`")
    else:
        await bot_utils.send_error_msg(ctx, "That command doesn't exist.")


@custom_command.command(name="edit")
@commands.cooldown(1, CoolDowns.CustomComand.value, BucketType.user)
async def edit_custom_command(self, ctx, command_name: str, *, text: str):
    """(Edits a custom command)

    Example:
    admin cc edit <command> <text/url>
    """

    await bot_utils.delete_channel_message(ctx)
    server = ctx.guild
    command_name = command_name.lower()

    commands_dal = CustomCommandsDal(self.bot.db_session, self.bot.log)
    rs = await commands_dal.get_all_commands(server.id)
    if len(rs) == 0:
        await bot_utils.send_error_msg(ctx, "There are no custom commands in this server.")
        return

    rs = await commands_dal.get_command(server.id, str(command_name))
    if len(rs) > 0:
        await commands_dal.update_command(server.id, str(command_name), str(text))
        await bot_utils.send_msg(ctx, f"Custom command successfully edited:\n`{ctx.prefix}{command_name}`")
    else:
        await bot_utils.send_error_msg(ctx, f"Command doesn't exist in this server:\n`{ctx.prefix}{command_name}`")


@custom_command.command(name="removeall")
@commands.cooldown(1, CoolDowns.CustomComand.value, BucketType.user)
async def remove_all_custom_commands(self, ctx):
    """(Removes all custom commands)

    Example:
    admin cc removeall
    """

    server = ctx.guild
    commands_dal = CustomCommandsDal(self.bot.db_session, self.bot.log)
    rs = await commands_dal.get_all_commands(server.id)
    if len(rs) == 0:
        await bot_utils.send_error_msg(ctx, "There are no custom commands in this server.")
        return

    await commands_dal.delete_all_commands(server.id)
    await bot_utils.send_msg(ctx, "All custom commands successfully removed.")


@custom_command.command(name="list")
@commands.cooldown(1, CoolDowns.CustomComand.value, BucketType.user)
async def list_custom_commands(self, ctx):
    """(Shows custom commands list)

    Example:
    admin cc list
    """

    server = ctx.guild
    commands_dal = CustomCommandsDal(self.bot.db_session, self.bot.log)
    rs = await commands_dal.get_all_commands(server.id)
    if len(rs) == 0:
        await bot_utils.send_error_msg(ctx, "There are no custom commands in this server.")
        return

    command = []
    author = []
    date = []
    position = 1
    for key, value in rs.items():
        author_name = bot_utils.get_member_name_by_id(ctx, value["discord_author_id"])
        command.append(f"{position}) {value['command_name']}")
        author.append(str(author_name))
        date.append(str(f"{value['date'].split()[0]}"))
        position += 1

    cmd = '\n'.join(command)
    authors = '\n'.join(author)
    dates = '\n'.join(date)

    embed = discord.Embed()
    embed.set_footer(text=f"For more info: {ctx.prefix}help cc")
    embed.set_author(name="Custom commands in this server", icon_url=f"{ctx.guild.icon.url}")
    embed.add_field(name="Command", value=chat_formatting.inline(cmd), inline=True)
    embed.add_field(name="Created by", value=chat_formatting.inline(authors), inline=True)
    embed.add_field(name="Date Created", value=chat_formatting.inline(dates), inline=True)
    await bot_utils.send_embed(ctx, embed)


async def setup(bot):
    bot.remove_command("admin")
    await bot.add_cog(CustomCommand(bot))
