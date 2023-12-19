# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from src.bot.utils import bot_utils, chat_formatting
from src.database.dal.bot.servers_dal import ServersDal
from src.database.dal.gw2.gw2_configs_dal import Gw2ConfigsDal
from src.database.dal.gw2.gw2_key_dal import Gw2KeyDal
from src.gw2.gw2 import GuildWars2
from src.gw2.utils.gw2_api import Gw2Api
from src.gw2.utils.gw2_cooldowns import GW2CoolDowns


class GW2Key(GuildWars2):
    """(Commands related to GW2 API keys)"""
    def __init__(self, bot):
        super().__init__(bot)


@GW2Key.gw2.group()
async def key(ctx):
    """(Commands related to GW2 API keys)
        To generate an API key, head to https://account.arena.net, and log in.
        In the "Applications" tab, generate a new key, with all permissions.
        Required API permissions: account
            gw2 key info          (Information about your GW2 API keys)
            gw2 key info all      (Information about all your GW2 API keys)
            gw2 key add <api_key> (Adds a key and associates it with your discord account)
            gw2 key remove        (Removes your GW2 API key from the bot)
    """

    await bot_utils.invoke_subcommand(ctx, "gw2 key")


@key.command(name="info")
@commands.cooldown(1, GW2CoolDowns.ApiKeys.value, BucketType.user)
async def info(ctx, sub_command: str = None):
    user_id = ctx.message.author.id
    server_id = ctx.message.guild.id
    author_icon_url = ctx.message.author.avatar.url
    color = ctx.bot.settings["gw2"]["EmbedColor"]
    gw2_key_dal = Gw2KeyDal(ctx.bot.db_session, ctx.bot.log)
    gw2_api = Gw2Api(ctx.bot)
    servers_dal = ServersDal(ctx.bot.db_session, ctx.bot.log)
    no_user_key_found_error = ("You dont have an API key registered in this server.\n"
                               f"To add or replace an API key: `{ctx.prefix}gw2 key add <api_key>`\n"
                               f"To check for all your API keys: `{ctx.prefix}gw2 key info all`")

    if sub_command and sub_command.lower() == "all":
        rs_all = await gw2_key_dal.get_all_user_api_key(user_id)
        if len(rs_all) == 0:
            await bot_utils.send_private_error_msg(ctx, no_user_key_found_error)
        else:
            for x in range(0, len(rs_all)):
                rs_guild_info = await servers_dal.get_server(rs_all[x]["server_id"])
                footer_guild_name = rs_guild_info[0]["server_name"]
                footer_icon_url = rs_guild_info[0]["icon_url"]

                try:
                    api_key = rs_all[x]["key"]
                    is_valid_key = await gw2_api.check_api_key(api_key)
                    if not isinstance(is_valid_key, dict):
                        is_valid_key = "NO"
                        name = "***This API Key is INVALID or no longer exists in gw2 api database***"
                    else:
                        is_valid_key = "YES"
                        name = f"{ctx.message.author}"
                except Exception as e:
                    await bot_utils.send_private_error_msg(ctx, e)
                    ctx.bot.log.error(ctx, e)
                    return

                embed = discord.Embed(title="Account Name", description=chat_formatting.inline(rs_all[x]["gw2_acc_name"]), color=color)
                embed.set_author(name=name, icon_url=author_icon_url)
                embed.add_field(name="Server", value=chat_formatting.inline(rs_all[x]["server_name"]), inline=True)
                embed.add_field(name="Key Name", value=chat_formatting.inline(rs_all[x]["key_name"]), inline=True)
                embed.add_field(name="Valid", value=chat_formatting.inline(is_valid_key), inline=True)
                embed.add_field(name="Permissions", value=chat_formatting.inline(rs_all[x]["permissions"].replace(",", "|")), inline=False)
                embed.add_field(name="Key", value=chat_formatting.inline(rs_all[x]["key"]), inline=False)
                embed.set_footer(text=footer_guild_name, icon_url=footer_icon_url)
                await bot_utils.send_embed(ctx, embed, True)
    elif sub_command is None:
        footer_guild_name = str(ctx.message.guild)
        footer_icon_url = ctx.message.guild.icon.url
        rs = await gw2_key_dal.get_server_user_api_key(server_id, user_id)
        if len(rs) == 0:
            await bot_utils.send_private_error_msg(ctx, no_user_key_found_error)
        else:
            try:
                api_key = rs[0]["key"]
                is_valid_key = await gw2_api.check_api_key(api_key)
                if not isinstance(is_valid_key, dict):
                    is_valid_key = "NO"
                    name = "***This API Key is INVALID (or no longer exists in gw2 api database)***"
                else:
                    is_valid_key = "YES"
                    name = f"{ctx.message.author}"
            except Exception as e:
                await bot_utils.send_private_error_msg(ctx, e)
                ctx.bot.log.error(ctx, e)
                return

            embed = discord.Embed(
                title="Account Name",
                description=chat_formatting.inline(rs[0]["gw2_acc_name"]),
                color=color
            )
            embed.set_author(name=name, icon_url=author_icon_url)
            embed.add_field(name="Server", value=chat_formatting.inline(rs[0]["server_name"]), inline=True)
            embed.add_field(name="Key Name", value=chat_formatting.inline(rs[0]["key_name"]), inline=True)
            embed.add_field(name="Valid", value=chat_formatting.inline(is_valid_key), inline=True)
            embed.add_field(name="Permissions", value=chat_formatting.inline(rs[0]["permissions"].replace(",", "|")), inline=False)
            embed.add_field(name="Key", value=chat_formatting.inline(rs[0]["key"]), inline=False)
            embed.set_footer(text=footer_guild_name, icon_url=footer_icon_url)
            await bot_utils.send_embed(ctx, embed, True)
    else:
        raise commands.BadArgument(message="BadArgument")


@key.command(name="add")
@commands.cooldown(1, GW2CoolDowns.ApiKeys.value, BucketType.user)
async def add(ctx, api_key: str):
    if isinstance(ctx.channel, discord.DMChannel):
        msg = "GW2 add api command needs to be used in a server channel for proper roles to be assign!!!"
        await bot_utils.send_private_error_msg(ctx, msg)
        return

    await bot_utils.delete_message(ctx, warning=True)
    gw2_configs = Gw2ConfigsDal(ctx.bot.db_session, ctx.bot.log)
    rs_gw2_sc = await gw2_configs.get_gw2_server_configs(ctx.guild.id)
    if len(rs_gw2_sc) == 0 or (len(rs_gw2_sc) > 0 and not rs_gw2_sc[0]["session"]):
        return await bot_utils.send_info_msg(ctx, "GW2 sessions is not active on this server.\n"
                                                  f"To activate: `{ctx.prefix}gw2 config session on`")
    user_id = ctx.message.author.id
    server_id = ctx.message.guild.id

    # searching if API key already exists in bot database
    gw2_key_dal = Gw2KeyDal(ctx.bot.db_session, ctx.bot.log)
    rs = await gw2_key_dal.get_server_api_key(server_id, api_key)
    if len(rs) == 0:
        gw2_api = Gw2Api(ctx.bot)
        is_valid_key = await gw2_api.check_api_key(api_key)
        if not isinstance(is_valid_key, dict):
            return await bot_utils.send_private_error_msg(ctx, f"{is_valid_key.args[1]}\n`{api_key}`")

        key_name = is_valid_key["name"]
        permissions = ",".join(is_valid_key["permissions"])

        try:
            # getting gw2 acc name
            api_req_acc_info = await gw2_api.call_api("account", key=api_key)
            gw2_acc_name = api_req_acc_info["name"]
            member_server_id = api_req_acc_info["world"]
        except Exception as e:
            await bot_utils.send_private_error_msg(ctx, e)
            return ctx.bot.log.error(ctx, e)

        try:
            # getting gw2 server name
            endpoint = f"worlds/{member_server_id}"
            api_req_server = await gw2_api.call_api(endpoint, key=api_key)
            gw2_server_name = api_req_server["name"]
        except Exception as e:
            await bot_utils.send_private_error_msg(ctx, e)
            ctx.bot.log.error(ctx, e)
            return

        kwargs = {
            "server_id": server_id,
            "user_id": user_id,
            "key_name": key_name,
            "gw2_acc_name": gw2_acc_name,
            "server_name": gw2_server_name,
            "permissions": permissions,
            "api_key": api_key
        }

        rs = await gw2_key_dal.get_server_user_api_key(server_id, user_id)
        if len(rs) > 0:
            await gw2_key_dal.update_api_key(**kwargs)
            msg = "Your API key was **replaced**.\n" \
                  f"Server: `{gw2_server_name}`\n" \
                  f"To get info about your new api key: `{ctx.prefix}gw2 key info`"
            color = ctx.bot.settings["gw2"]["EmbedColor"]
            await bot_utils.send_private_msg(ctx, msg, color)
        else:
            await gw2_key_dal.insert_api_key(**kwargs)
            msg = "Your key was verified and was **added** to your discord account.\n" \
                  f"Server: `{gw2_server_name}`\n" \
                  f"To get info about your api key: `{ctx.prefix}gw2 key info`"
            color = ctx.bot.settings["gw2"]["EmbedColor"]
            await bot_utils.send_private_msg(ctx, msg, color)
    elif len(rs) == 1 and rs[0]["user_id"] == user_id:
        msg = "That API key is already registered by you or someone else.\n" \
              f"To get info about your api key: `{ctx.prefix}gw2 key info`"
        await bot_utils.send_private_error_msg(ctx, msg)
    else:
        await bot_utils.send_private_error_msg(ctx, "That API key is already in use by someone else.")


@key.command(name="remove")
@commands.cooldown(1, GW2CoolDowns.ApiKeys.value, BucketType.user)
async def remove(ctx):
    user_id = ctx.message.author.id
    server_id = ctx.message.guild.id
    gw2_key_dal = Gw2KeyDal(ctx.bot.db_session, ctx.bot.log)

    rs_key = await gw2_key_dal.get_server_user_api_key(server_id, user_id)
    if len(rs_key) == 0:
        await bot_utils.send_private_error_msg(ctx, "You dont have an API key registered in this server.\n"
                                                    f"To add or replace an API key: `{ctx.prefix}gw2 key add <api_key>`\n"
                                                    f"To check your API key: `{ctx.prefix}gw2 key info`")
    else:
        color = ctx.bot.settings["gw2"]["EmbedColor"]
        await gw2_key_dal.delete_server_user_api_key(server_id, user_id)
        await bot_utils.send_private_msg(ctx, "Your GW2 API Key has been deleted successfully.", color)


async def setup(bot):
    bot.remove_command("gw2")
    await bot.add_cog(GW2Key(bot))
