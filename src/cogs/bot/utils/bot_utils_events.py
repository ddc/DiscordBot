#! /usr/bin/env python3
# |*****************************************************
# * Copyright         : Copyright (C) 2019
# * Author            : ddc
# * License           : GPL v3
# * Python            : 3.6
# |*****************************************************
# # -*- coding: utf-8 -*-

from src.sql.gw2.gw2_roles_sql import Gw2RolesSql
from src.sql.gw2.gw2_configs_sql import Gw2ConfigsSql
from src.sql.bot.initial_configs_sql import InitialConfigsSql
from src.cogs.bot.utils import chat_formatting as Formatting
from src.sql.bot.alter_tables_sql import AlterTablesSql
from src.sql.bot.server_configs_sql import ServerConfigsSql
from src.sql.bot.blacklists_sql import BlacklistsSql
from src.sql.bot.commands_sql import CommandsSql
from src.sql.bot.servers_sql import ServersSql
from src.sql.bot.users_sql import UsersSql
from src.cogs.bot.utils.bg_tasks import BgTasks
from src.sql.bot.triggers import Triggers
from src.cogs.bot.utils import constants
from src.cogs.bot.utils import bot_utils as BotUtils
from src.sql.bot.initial_tables_sql import InitialTablesSql
from src.sql.gw2.gw2_initial_tables_sql import Gw2InitialTablesSql
import discord
import random
import os


################################################################################
async def set_initial_sql_tables(bot):
    initialTablesSql = InitialTablesSql(bot)
    await initialTablesSql.create_initial_sqlite_bot_tables()
    gw2InitialTablesSql = Gw2InitialTablesSql(bot)
    await gw2InitialTablesSql.create_gw2_sqlite_tables()
    initialConfigsSql = InitialConfigsSql(bot)
    await initialConfigsSql.insert_initial_bot_configs(bot)


################################################################################
async def insert_default_initial_configs(bot):
    serversSql = ServersSql(bot)
    await serversSql.insert_default_initial_server_configs(bot.guilds)
    usersSql = UsersSql(bot)
    await usersSql.insert_all_server_users(bot.guilds)
    gw2Configs = Gw2ConfigsSql(bot)
    await gw2Configs.insert_default_initial_gw2_server_configs(bot.guilds, bot.gw2_settings["BGRoleTimer"])


################################################################################
async def set_others_sql_configs(bot):
    alterTablesSql = AlterTablesSql(bot)
    await alterTablesSql.alter_sqlite_tables()
    triggers = Triggers(bot)
    await triggers.create_triggers()


################################################################################
async def run_bg_tasks(bot):
    await set_presence(bot)
    await set_gw2_roles(bot)


################################################################################
async def set_presence(bot):
    prefix = bot.command_prefix[0]

    if bot.settings["ExclusiveUsers"] is not None:
        bot_game_desc = f"PRIVATE BOT | {prefix}help"
        await bot.change_presence(status=discord.Status.online, activity=discord.Game(name=bot_game_desc))
    elif bot.settings["BGChangeGame"].lower() == "yes":
        bgTasks = BgTasks(bot)
        bot.loop.create_task(bgTasks.bgtask_change_presence(bot.settings["BGActivityTimer"]))
    else:
        game = str(random.choice(constants.GAMES_INCLUDED))
        bot_game_desc = f"{game} | {prefix}help"
        await bot.change_presence(status=discord.Status.online, activity=discord.Game(name=bot_game_desc))


################################################################################
async def set_gw2_roles(bot):
    if bot.gw2_settings["BGCheckRoleTimer"].lower() == "yes":
        gw2Configs = Gw2ConfigsSql(bot)
        gw2Roles = Gw2RolesSql(bot)
        bgTasks = BgTasks(bot)

        for g in bot.guilds:
            rs_gw2_rl = await gw2Roles.get_all_gw2_server_roles(g.id)
            if len(rs_gw2_rl) > 0:
                for key, value in rs_gw2_rl.items():
                    role_name = value["role_name"]
                    for rol in g.roles:
                        if rol.name.lower() == role_name.lower():
                            rs_gw2_sc = await gw2Configs.get_gw2_server_configs(g.id)
                            if len(rs_gw2_sc) > 0:
                                role_timer = rs_gw2_sc[0]["role_timer"]
                            else:
                                role_timer = bot.gw2_settings["BGRoleTimer"]

                            bot.loop.create_task(bgTasks.bgtask_check_gw2_roles(g, rol, role_timer))


################################################################################
async def execute_private_msg(self, ctx):
    is_command = True if ctx.prefix is not None else False
    if is_command is False:
        # checking for custom messages
        customMessages = await _check_custom_messages(self, ctx.message)
        if customMessages:
            return

        if BotUtils.is_bot_owner(ctx, ctx.message.author):
            msg = f"Hello master.\nWhat can i do for you?"
            embed = discord.Embed(color=discord.Color.green(), description=f"{Formatting.inline(msg)}")
            await ctx.message.author.send(embed=embed)

            cmd = self.bot.get_command("owner")
            await ctx.author.send(Formatting.box(cmd.help))
        else:
            msg = "Hello, I don't accept direct messages."
            embed = discord.Embed(color=discord.Color.red(), description=f"{Formatting.error_inline(msg)}")
            await ctx.message.author.send(embed=embed)
    else:
        if not (await _check_exclusive_users(self, ctx)):
            return

        blacklistsSql = BlacklistsSql(self.bot)
        bl = await blacklistsSql.get_blacklisted_user(ctx.message.author.id)
        if len(bl) > 0:
            if ctx.message.content.startswith(ctx.prefix):
                servers_lst = []
                reason_lst = []
                for key, value in bl.items():
                    servers_lst.append(value["server_name"])
                    if value["reason"] is None:
                        reason_lst.append("---")
                    else:
                        reason_lst.append(value["reason"])

            servers = '\n'.join(servers_lst)
            if len(reason_lst) > 0:
                reason = '\n'.join(reason_lst)
            msg = "You are blacklisted.\n" \
                  "You cannot execute any Bot commands until your are removed from all servers."
            embed = discord.Embed(title="", color=discord.Color.red(), description=Formatting.error_inline(msg))
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            embed.add_field(name="You are blacklisted on following servers:",
                            value=Formatting.inline(servers),
                            inline=True)
            embed.add_field(name="Reason", value=Formatting.inline(reason), inline=True)
            await ctx.message.channel.send(embed=embed)
            return

        msg = "That command is not allowed in direct messages."
        embed = discord.Embed(color=discord.Color.red(), description=f"{Formatting.error_inline(msg)}")
        user_cmd = ctx.message.content.split(' ', 1)[0]
        allowed_DM_commands = self.bot.settings["DMCommands"]

        if allowed_DM_commands is not None:
            if (isinstance(allowed_DM_commands, tuple)):  # more than 1 command, between quotes
                sorted_cmds = sorted(sorted(allowed_DM_commands))
            elif (isinstance(allowed_DM_commands, str)):
                if "," in allowed_DM_commands:
                    sorted_cmds = allowed_DM_commands.split(",")
                else:
                    sorted_cmds = allowed_DM_commands.split()

            for allowed_cmd in sorted_cmds:
                if user_cmd == ctx.prefix + allowed_cmd:
                    await self.bot.process_commands(ctx.message)
                    return

            allowed_cmds = '\n'.join(sorted_cmds)
            embed.add_field(name="Commands allowed in direct messages:",
                            value=f"{Formatting.inline(allowed_cmds)}",
                            inline=False)

        await ctx.message.author.send(embed=embed)


################################################################################
async def execute_server_msg(self, ctx):
    is_command = True if ctx.prefix is not None else False
    serverConfigsSql = ServerConfigsSql(self.bot)
    rs_user_channel_configs = await serverConfigsSql.get_user_channel_configs(ctx.author, ctx.message.channel.id)

    if len(rs_user_channel_configs) == 0:
        self.bot.log.error("error with serverConfigsSql.get_user_channel_configs")
        return

    # block messages from invisible members
    if rs_user_channel_configs[0]["block_invis_members"] == "Y":
        is_member_invis = _check_member_invisible(self, ctx)
        if is_member_invis:
            await BotUtils.delete_last_channel_message(self, ctx)
            msg = "You are Invisible (offline)\n" \
                  f"Server \"{ctx.guild.name}\" does not allow messages from invisible members.\n" \
                  "Please change your status if you want to send messages to this server."
            embed = discord.Embed(title="", color=discord.Color.red(), description=Formatting.error_inline(msg))
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            try:
                await ctx.message.author.send(embed=embed)
            except discord.HTTPException:
                try:
                    await ctx.send(embed=embed)
                except discord.HTTPException:
                    await ctx.send(f"{ctx.message.author.mention} {msg}")
            return

    # block bad words profanity filter "on" current channel
    if rs_user_channel_configs[0]["profanity_filter"] is not None and rs_user_channel_configs[0][
        "profanity_filter"] == 'Y':
        bad_word = await _check_profanity_filter_words(self, ctx.message)
        if bad_word: return

    # check for custom messages
    if rs_user_channel_configs[0]["bot_word_reactions"] == "Y":
        customMessages = await _check_custom_messages(self, ctx.message)
        if customMessages: return

    # checking if member is muted in the current server
    if rs_user_channel_configs[0]["muted"] is not None and rs_user_channel_configs[0]["muted"] == 'Y':
        try:
            await ctx.message.delete()
        except:
            msg = "Bot does not have permission to delete messages.\n" \
                  "Missing permission: \"Manage Messages\"`"
            embed = discord.Embed(title="", color=discord.Color.red(), description=msg)
            try:
                await ctx.channel.send(embed=embed)
            except discord.HTTPException:
                await ctx.channel.send(f"{msg}")
            return

        msg = "You are muted.\n" \
              f"Server: {ctx.guild}\n" \
              "You cannot type anything.\n" \
              "Please do not insist.\n"
        if rs_user_channel_configs[0]['muted_reason'] is not None:
            msg += f"\nReason: {rs_user_channel_configs[0]['muted_reason']}"
        embed = discord.Embed(title="", color=discord.Color.red(), description=Formatting.error_inline(msg))
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        try:
            await ctx.message.author.send(embed=embed)
        except:
            await ctx.send(f"{ctx.message.author.mention}\n{msg}")
        return

    if is_command:
        ignore_prefixes_characteres = await _check_prefixes_characteres(self, ctx.message)
        if ignore_prefixes_characteres: return

        if not (await _check_exclusive_users(self, ctx)):
            return

        # checking if member is blacklisted
        if rs_user_channel_configs[0]["blacklisted"] is not None and rs_user_channel_configs[0]["blacklisted"] == 'Y':
            if ctx.message.content.startswith(ctx.prefix):
                msg = "You are blacklisted.\n" \
                      "You cannot execute any Bot commands.\n" \
                      "Please do not insist.\n"
                if rs_user_channel_configs[0]['blacklisted_reason'] is not None:
                    msg += f"\nReason: {rs_user_channel_configs[0]['blacklisted_reason']}"
                embed = discord.Embed(title="", color=discord.Color.red(), description=Formatting.error_inline(msg))
                embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
                try:
                    await ctx.message.channel.send(embed=embed)
                except discord.HTTPException:
                    await ctx.send(f"{ctx.message.author.mention}\n{msg}")
                return

        # execute custom commands
        commandsSql = CommandsSql(self.bot)
        rs_command = await commandsSql.get_command(ctx.author.guild.id, str(ctx.invoked_with))
        if len(rs_command) > 0:
            await ctx.message.channel.trigger_typing()
            await ctx.message.channel.send(str(rs_command[0]["description"]))
            return

        await self.bot.process_commands(ctx.message)


################################################################################
async def _check_prefixes_characteres(self, message):
    # ignore 2 sequence of characters ?_? ???
    second_char = message.content[1:2]
    if not second_char.isalpha():
        return True


################################################################################
async def _send_custom_message(message, send_msg: str):
    await message.channel.trigger_typing()
    desc = f":rage: :middle_finger:\n{Formatting.inline(send_msg)}"
    if not (isinstance(message.channel, discord.DMChannel)):
        desc = f"{desc}\n{message.author.mention}"
    embed = discord.Embed(color=discord.Color.red(), description=desc)
    await message.channel.send(embed=embed)


################################################################################
def _check_bad_words_file(self):
    if not os.path.isfile(constants.SWEAR_WORDS_FILENAME):
        self.bot.log.error(f"File \"{constants.SWEAR_WORDS_FILENAME}\" was not found.")
        return False
    return True


################################################################################
async def _check_custom_messages(self, message):
    msg = message.system_content.lower()
    cwords = "🖕," + self.bot.settings["BotReactWords"]
    config_word_found = False
    bot_word_found = False

    if cwords is not None:
        for cw in cwords.split(","):
            for mw in msg.split():
                if str(cw) == str(mw):
                    config_word_found = True
                if str(mw).lower() == "bot" or str(mw).lower() == self.bot.user.mention:
                    bot_word_found = True

    if isinstance(message.channel, discord.DMChannel):
        bot_word_found = True

    if config_word_found is True and bot_word_found is True:
        send_msg = "fu ufk!!!"
        if "stupid" in msg.lower():
            send_msg = "I'm not stupid, fu ufk!!!"
        elif "retard" in msg.lower():
            send_msg = "I'm not retard, fu ufk!!!"
        await _send_custom_message(message, send_msg)
        return True
    return False


################################################################################
async def _check_profanity_filter_words(self, message):
    if _check_bad_words_file(self):
        f = open(constants.SWEAR_WORDS_FILENAME)
    else:
        return

    filecontents = f.readlines()
    f.close()
    user_msg = message.system_content.split()
    prefix = str(self.bot.command_prefix[0])
    for word in user_msg:
        for line in filecontents:
            if str(word.lower()) == str(line.lower().strip('\n')) \
                    or str(word.lower()) == str((prefix + line).lower().strip('\n')):
                self.bot.log.info(f"({message.author})" \
                                  f"(Word:{word})" \
                                  f"(Server:{message.guild.name})" \
                                  f"(Channel:{message.channel})")
                if not isinstance(message.channel, discord.DMChannel):
                    try:
                        await message.delete()
                        msg = constants.PROFANITY_FILTER_MSG
                        embed = discord.Embed(title="", color=discord.Color.red(), description=msg)
                        embed.set_author(name=message.author.display_name, icon_url=message.author.avatar_url)
                        try:
                            await message.channel.send(embed=embed)
                        except discord.HTTPException:
                            await message.channel.send(f"{message.author.mention} {msg}")
                        return True
                    except:
                        msg = f"`{Formatting.NO_ENTRY} Profanity filter is on but Bot does not have permission to delete messages.\n" \
                              "Missing permission: \"Manage Messages\"`"
                        embed = discord.Embed(title="", color=discord.Color.red(), description=msg)
                        try:
                            await message.channel.send(embed=embed)
                        except discord.HTTPException:
                            await message.channel.send(f"{msg}")
                        return True
    return False


################################################################################
def _check_member_invisible(self, ctx):
    if ctx.author.status.name == "offline":
        return True
    return False


################################################################################
async def _check_exclusive_users(self, ctx):
    exclusive_users_id = self.bot.settings["ExclusiveUsers"]
    user_found = False

    if exclusive_users_id is not None:
        if isinstance(exclusive_users_id, tuple):
            for ids in exclusive_users_id:
                if ctx.message.author.id == ids:
                    user_found = True
        else:
            if ctx.message.author.id == exclusive_users_id:
                user_found = True

    if user_found is False and exclusive_users_id is not None:
        msg = "This is a Private Bot.\n" \
              "You are not allowed to execute any commands.\n" \
              "Only a few users are allowed to use it.\n" \
              "Please don't insist. Thank You!!!"
        await BotUtils.send_private_error_msg(self, ctx, msg)
        return False

    return True
