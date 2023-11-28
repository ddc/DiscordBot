# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from src.bot.utils import bot_utils, chat_formatting
from src.gw2.utils.gw2_api import Gw2Api
from src.gw2.utils import gw2_utils
from src.database.dal.bot.servers_dal import ServersDal
#from src.database.dal.gw2.gw2_roles_sql import Gw2RolesSql
from src.database.dal.gw2.gw2_key_dal import Gw2KeyDal
from src.database.dal.gw2.gw2_configs_dal import Gw2ConfigsDal


class GW2Key(commands.Cog):
    """(Commands related to GW2 API keys)"""
    def __init__(self, bot):
        self.bot = bot

    async def gw2_key(self, ctx, cmd_api_key: str):
        await gw2_utils.delete_api_key(self, ctx)
        command = str(cmd_api_key.replace(f"{ctx.prefix}gw2 key ", "")).split(' ', 1)[0]

        if command == "info":
            sub_command = ctx.message.clean_content.replace(f"{ctx.prefix}gw2 key info", "")
            if len(sub_command) > 0:
                raise commands.BadArgument(message="BadArgument")
            else:
                await _info_key(self, ctx)
        elif command == "add":
            api_key = ctx.message.clean_content.replace(f"{ctx.prefix}gw2 key add ", "")
            await _add_key(self, ctx, api_key)
        elif command == "remove":
            sub_command = ctx.message.clean_content.replace(f"{ctx.prefix}gw2 key remove", "")
            if len(sub_command) > 0:
                raise commands.BadArgument(message="BadArgument")
            else:
                await _remove_key(self, ctx)
        else:
            msg = "Wrong command.\n Command needs to be [add | remove | info]\nPlease try again."
            await bot_utils.send_error_msg(self, ctx, msg)


async def _info_key(self, ctx, sub_command=None):
    user_id = ctx.message.author.id
    server_id = ctx.message.guild.id
    author_icon_url = ctx.message.author.avatar.url
    color = self.bot.gw2_settings["EmbedColor"]
    gw2KeySql = Gw2KeyDal(self.bot.db_session, self.bot.log)
    gw2Api = Gw2Api(self.bot)
    serversSql = ServersDal(self.bot.db_session, self.bot.log)

    if sub_command is not None and sub_command.lower() == "all":
        rs_all = await gw2KeySql.get_all_user_api_key(user_id)
        if len(rs_all) == 0:
            await bot_utils.send_private_error_msg(self, ctx,
                                                  "You dont have an API key registered in this server.\n"
                                                  f"To add or replace an API key use: `{ctx.prefix}gw2 key add <api_key>`\n"
                                                  f"To check your API key use: `{ctx.prefix}gw2 key info`")
        else:
            for x in range(0, len(rs_all)):
                rs_guild_info = await serversSql.get_server_by_id(rs_all[x]["server_id"])
                footer_guild_name = rs_guild_info[0]["server_name"]
                footer_icon_url = rs_guild_info[0]["icon_url"]

                try:
                    api_key = rs_all[x]["key"]
                    is_valid_key = await gw2Api.check_api_key(api_key)
                    if not isinstance(is_valid_key, dict):
                        is_valid_key = "NO"
                        name = "***This API Key is INVALID or no longer exists in gw2 api database***"
                    else:
                        is_valid_key = "YES"
                        name = f"{ctx.message.author}"
                except Exception as e:
                    await bot_utils.send_private_error_msg(self, ctx, e)
                    self.bot.log.error(ctx, e)
                    return

                _embed = discord.Embed(title="Account Name",
                                       description=chat_formatting.inline(rs_all[x]["gw2_acc_name"]),
                                       color=color)
                _embed.set_author(name=name, icon_url=author_icon_url)
                _embed.add_field(name="Server", value=chat_formatting.inline(rs_all[x]["server_name"]), inline=True)
                _embed.add_field(name="Key Name", value=chat_formatting.inline(rs_all[x]["key_name"]), inline=True)
                _embed.add_field(name="Valid", value=chat_formatting.inline(is_valid_key), inline=True)
                _embed.add_field(name="Permissions",
                                 value=chat_formatting.inline(rs_all[x]["permissions"].replace(",", "|")), inline=False)
                _embed.add_field(name="Key", value=chat_formatting.inline(rs_all[x]["key"]), inline=False)
                _embed.set_footer(text=footer_guild_name, icon_url=footer_icon_url)
                await bot_utils.send_embed(self, ctx, _embed, True)
    elif sub_command is None:
        footer_guild_name = str(ctx.message.guild)
        footer_icon_url = ctx.message.guild.icon.url

        rs = await gw2KeySql.get_server_user_api_key(server_id, user_id)
        if len(rs) == 0:
            await bot_utils.send_private_error_msg(self, ctx,
                                                  "You dont have an API key registered in this server.\n"
                                                  f"To add or replace an API key use: `{ctx.prefix}gw2 key add <api_key>`\n"
                                                  f"To check your API key use: `{ctx.prefix}gw2 key info`")
        else:
            try:
                api_key = rs[0]["key"]
                is_valid_key = await gw2Api.check_api_key(api_key)
                if not isinstance(is_valid_key, dict):
                    is_valid_key = "NO"
                    name = "***This API Key is INVALID (or no longer exists in gw2 api database)***"
                else:
                    is_valid_key = "YES"
                    name = f"{ctx.message.author}"
            except Exception as e:
                await bot_utils.send_private_error_msg(self, ctx, e)
                self.bot.log.error(ctx, e)
                return

            _embed = discord.Embed(title="Account Name",
                                   description=chat_formatting.inline(rs[0]["gw2_acc_name"]),
                                   color=color)
            _embed.set_author(name=name, icon_url=author_icon_url)
            _embed.add_field(name="Server", value=chat_formatting.inline(rs[0]["server_name"]), inline=True)
            _embed.add_field(name="Key Name", value=chat_formatting.inline(rs[0]["key_name"]), inline=True)
            _embed.add_field(name="Valid", value=chat_formatting.inline(is_valid_key), inline=True)
            _embed.add_field(name="Permissions", value=chat_formatting.inline(rs[0]["permissions"].replace(",", "|")),
                             inline=False)
            _embed.add_field(name="Key", value=chat_formatting.inline(rs[0]["key"]), inline=False)
            _embed.set_footer(text=footer_guild_name, icon_url=footer_icon_url)
            await bot_utils.send_embed(self, ctx, _embed, True)
    else:
        raise commands.BadArgument(message="BadArgument")


async def _add_key(self, ctx, api_key: str):
    #     if (isinstance(ctx.channel, discord.DMChannel)):
    #         msg = "GW2 add api command needs to be used in a server channel for proper roles to be assign!!!"
    #         await bot_utils.send_private_error_msg(self, ctx, msg)
    #         return

    gw2Configs = Gw2ConfigsDal(self.bot.db_session, self.bot.log)
    rs_gw2_sc = await gw2Configs.get_gw2_server_configs(ctx.guild.id)
    if len(rs_gw2_sc) == 0 or (len(rs_gw2_sc) > 0 and rs_gw2_sc[0]["last_session"] == "N"):
        return await bot_utils.send_error_msg(self, ctx, "Unable to add api key.\n"
                                                        "Last session is not active on this server.\n"
                                                        f"To activate use: `{ctx.prefix}gw2 config lastsession on`")
    user_id = ctx.message.author.id
    server_id = ctx.message.guild.id

    # searching if API key already exists in bot database
    gw2KeySql = Gw2KeyDal(self.bot.db_session, self.bot.log)
    rs = await gw2KeySql.get_api_key(server_id, api_key)
    if len(rs) == 0:
        gw2Api = Gw2Api(self.bot)
        is_valid_key = await gw2Api.check_api_key(api_key)
        if not isinstance(is_valid_key, dict):
            return await bot_utils.send_private_error_msg(self, ctx, f"{is_valid_key.args[1]}\n`{api_key}`")

        key_name = is_valid_key["name"]
        permissions = ','.join(is_valid_key["permissions"])

        try:
            # getting gw2 acc name
            api_req_acc_info = await gw2Api.call_api("account", key=api_key)
            gw2_acc_name = api_req_acc_info["name"]
            member_server_id = api_req_acc_info["world"]
        except Exception as e:
            await bot_utils.send_private_error_msg(self, ctx, e)
            return self.bot.log.error(ctx, e)

        try:
            # getting gw2 server name
            endpoint = f"worlds/{member_server_id}"
            api_req_server = await gw2Api.call_api(endpoint, key=api_key)
            gw2_server_name = api_req_server["name"]
        except Exception as e:
            await bot_utils.send_private_error_msg(self, ctx, e)
            self.bot.log.error(ctx, e)
            return

        # searching if user has 1 api key already
        rs = await gw2KeySql.get_server_user_api_key(server_id, user_id)
        if len(rs) > 0:
            # update key
            updateObject = bot_utils.Object()
            updateObject.user_id = user_id
            updateObject.server_id = server_id
            updateObject.key_name = key_name
            updateObject.gw2_acc_name = gw2_acc_name
            updateObject.permissions = permissions
            updateObject.key = api_key
            updateObject.server_name = gw2_server_name
            await gw2KeySql.update_api_key(updateObject)
            msg = "Your API key was **replaced**.\n" \
                  f"Server: `{gw2_server_name}`\n" \
                  f"To get info about your new api key use: `{ctx.prefix}gw2 key info`"
            color = self.bot.gw2_settings["EmbedColor"]
            await bot_utils.send_private_msg(self, ctx, color, msg)
        else:
            # insert key
            insertObject = bot_utils.Object()
            insertObject.user_id = user_id
            insertObject.server_id = server_id
            insertObject.key_name = key_name
            insertObject.gw2_acc_name = gw2_acc_name
            insertObject.permissions = permissions
            insertObject.key = api_key
            insertObject.server_name = gw2_server_name
            await gw2KeySql.insert_api_key(insertObject)
            msg = "Your key was verified and was **added** to your discord account.\n" \
                  f"Server: `{gw2_server_name}`\n" \
                  f"To get info about your api key use: `{ctx.prefix}gw2 key info`"
            color = self.bot.gw2_settings["EmbedColor"]
            await bot_utils.send_private_msg(self, ctx, color, msg)

        # # checking if the bot needs to assign gw2 server roles to user
        # gw2Roles = Gw2RolesSql(self.bot)
        # rs = await gw2Roles.get_gw2_server_role(ctx.message.channel.guild.id, gw2_server_name.lower())
        # if len(rs) > 0:
        #     new_role = bot_utils.check_server_has_role(self, ctx.guild, gw2_server_name.lower())
        #     if new_role is not None:
        #         await gw2_utils.assignGw2GuildRoles(self, ctx, ctx.message.author, new_role, api_key)
        # else:
        #     await gw2_utils.removeAllGw2RolesFromUser(self, ctx.message.author)

    elif len(rs) == 1 and rs[0]["user_id"] == user_id:
        msg = "That API key is already registered by you or someone else.\n" \
              f"To get info about your api key use: `{ctx.prefix}gw2 key info`"
        await bot_utils.send_private_error_msg(self, ctx, msg)
    else:
        await bot_utils.send_private_error_msg(self, ctx, "That API key is already in use by someone else.")


async def _remove_key(self, ctx):
    user_id = ctx.message.author.id
    server_id = ctx.message.guild.id
    gw2KeySql = Gw2KeyDal(self.bot.db_session, self.bot.log)

    rs_key = await gw2KeySql.get_server_user_api_key(server_id, user_id)
    server_name = rs_key[0]["server_name"].lower()

    if len(rs_key) == 0:
        await gw2_utils.removeAllGw2RolesFromUser(self, ctx.message.author)
        await bot_utils.send_private_error_msg(self, ctx, "You dont have an API key registered in this server.\n" \
                                                      f"To add or replace an API key use: `{ctx.prefix}gw2 key add <api_key>`\n"
                                                      f"To check your API key use: `{ctx.prefix}gw2 key info`")
    else:
        color = self.bot.gw2_settings["EmbedColor"]
        await gw2KeySql.delete_server_user_api_key(server_id, user_id)
        await bot_utils.send_private_msg(self, ctx, color, "Your GW2 API Key has been deleted successfully.")

        # # checking if the bot needs to assign gw2 server roles to user
        # gw2Roles = Gw2RolesSql(self.bot)
        # rs_role = await gw2Roles.get_gw2_server_role(ctx.message.channel.guild.id, server_name)
        # if len(rs_role) > 0:
        #     new_role = None
        #     for rol in ctx.message.channel.guild.roles:
        #         if rol.name.lower() == server_name:
        #             new_role = rol
        #             break
        #
        #     if new_role is not None:
        #         await gw2_utils.removeGw2RoleFromUser(self, ctx.message.author, new_role)