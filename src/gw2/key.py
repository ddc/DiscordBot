# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from src.bot.utils import bot_utils, chat_formatting
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
            gw2 key add <api_key>       (Adds a key and associates it with your discord account)
            gw2 key remove              (Removes your GW2 API key from the bot)
            gw2 key info                (Information about all your GW2 API keys)
            gw2 key info <api_key_name> (Information about your GW2 API keys)
    """

    await bot_utils.invoke_subcommand(ctx, "gw2 key")


@key.command(name="add")
@commands.cooldown(1, GW2CoolDowns.ApiKeys.value, BucketType.user)
async def add(ctx, api_key: str):
    """(Adds a key and associates it with your discord account)
        Required API permissions: account
            gw2 key add <api_key>
    """

    await bot_utils.delete_message(ctx, warning=True)
    user_id = ctx.message.author.id
    embed_color = ctx.bot.settings["gw2"]["EmbedColor"]

    # checking API Key with gw2 servers
    gw2_api = Gw2Api(ctx.bot)
    is_valid_key = await gw2_api.check_api_key(api_key)
    if not isinstance(is_valid_key, dict):
        return await bot_utils.send_error_msg(ctx, f"{is_valid_key.args[1]}\n`{api_key}`", True)

    key_name = is_valid_key["name"]
    permissions = ",".join(is_valid_key["permissions"])

    try:
        # getting gw2 acc name
        api_req_acc_info = await gw2_api.call_api("account", api_key)
        gw2_acc_name = api_req_acc_info["name"]
        member_server_id = api_req_acc_info["world"]
    except Exception as e:
        await bot_utils.send_error_msg(ctx, e, True)
        return ctx.bot.log.error(ctx, e)

    try:
        # getting gw2 server name
        uri = f"worlds/{member_server_id}"
        api_req_server = await gw2_api.call_api(uri, api_key)
        gw2_server_name = api_req_server["name"]
    except Exception as e:
        await bot_utils.send_error_msg(ctx, e, True)
        ctx.bot.log.error(ctx, e)
        return

    api_key_args = {
        "user_id": user_id,
        "key_name": key_name,
        "gw2_acc_name": gw2_acc_name,
        "server_name": gw2_server_name,
        "permissions": permissions,
        "api_key": api_key
    }

    # searching if API key in local database
    gw2_key_dal = Gw2KeyDal(ctx.bot.db_session, ctx.bot.log)
    rs = await gw2_key_dal.get_api_key(api_key)
    if not rs:
        await gw2_key_dal.insert_api_key(api_key_args)
        msg = f"Your key was verified and was **added** to your discord account.\n" \
              f"Key: `{key_name}`\n" \
              f"Server: `{gw2_server_name}`\n" \
              f"To get info about your api key: `{ctx.prefix}gw2 key info`"
        await bot_utils.send_msg(ctx, msg, True, embed_color)
    elif rs[0]["user_id"] == user_id:
        await gw2_key_dal.update_api_key(api_key_args)
        msg = f"Your API key `{rs[0]['name']}` was **replaced** with your new key: `{key_name}`\n" \
              f"Server: `{gw2_server_name}`\n" \
              f"To get info about your new api key: `{ctx.prefix}gw2 key info`"
        await bot_utils.send_msg(ctx, msg, True, embed_color)
    else:
        await bot_utils.send_error_msg(ctx, "That API key is already in use by someone else.", True)


@key.command(name="remove")
@commands.cooldown(1, GW2CoolDowns.ApiKeys.value, BucketType.user)
async def remove(ctx):
    """(Removes your GW2 API key from the bot)
            gw2 key remove
    """

    user_id = ctx.message.author.id
    gw2_key_dal = Gw2KeyDal(ctx.bot.db_session, ctx.bot.log)

    rs = await gw2_key_dal.get_api_key_by_user(user_id)
    if not rs:
        await bot_utils.send_error_msg(ctx, "You dont have an API key registered.\n"
                                            f"To add or replace an API key send a DM with: `{ctx.prefix}gw2 key add <api_key>`\n"
                                            f"To check your API key: `{ctx.prefix}gw2 key info`",
                                            True)
    else:
        color = ctx.bot.settings["gw2"]["EmbedColor"]
        await gw2_key_dal.delete_user_api_key(user_id)
        await bot_utils.send_msg(ctx, "Your GW2 API Key has been deleted successfully.", True, color)


@key.command(name="info", aliases=["list"])
@commands.cooldown(1, GW2CoolDowns.ApiKeys.value, BucketType.user)
async def info(ctx, key_name: str = None):
    """(Removes your GW2 API key from the bot)
            gw2 key remove
    """

    user_id = ctx.message.author.id
    author_icon_url = ctx.message.author.avatar.url
    color = ctx.bot.settings["gw2"]["EmbedColor"]
    gw2_key_dal = Gw2KeyDal(ctx.bot.db_session, ctx.bot.log)
    gw2_api = Gw2Api(ctx.bot)
    no_user_key_found_error = ("You dont have an API key registered.\n"
                               f"To add or replace an API key send a DM with: `{ctx.prefix}gw2 key add <api_key>`\n"
                               f"To check your API key: `{ctx.prefix}gw2 key info`")

    if key_name is None:
        rs = await gw2_key_dal.get_api_key_by_user(user_id)
    else:
        rs = await gw2_key_dal.get_api_key_by_name(key_name)

    if not rs:
        await bot_utils.send_error_msg(ctx, no_user_key_found_error, True)
    else:
        try:
            api_key = rs[0]["key"]
            is_valid_key = await gw2_api.check_api_key(api_key)
            if not isinstance(is_valid_key, dict):
                is_valid_key = "NO"
                name = "***This API Key is INVALID or no longer exists in gw2 api database***"
            else:
                is_valid_key = "YES"
                name = f"{ctx.message.author}"
        except Exception as e:
            await bot_utils.send_error_msg(ctx, e, True)
            ctx.bot.log.error(ctx, e)
            return

        embed = discord.Embed(title="Account Name", description=chat_formatting.inline(rs[0]["gw2_acc_name"]), color=color)
        embed.set_author(name=name, icon_url=author_icon_url)
        embed.add_field(name="Server", value=chat_formatting.inline(rs[0]["server"]))
        embed.add_field(name="Key Name", value=chat_formatting.inline(rs[0]["name"]))
        embed.add_field(name="Valid", value=chat_formatting.inline(is_valid_key))
        embed.add_field(name="Permissions", value=chat_formatting.inline(rs[0]["permissions"].replace(",", "|")), inline=False)
        embed.add_field(name="Key", value=chat_formatting.inline(rs[0]["key"]), inline=False)
        embed.set_footer(icon_url=ctx.bot.user.avatar.url, text=f"{bot_utils.get_current_date_time_str_long()} UTC")
        await bot_utils.send_embed(ctx, embed, dm=True)


async def setup(bot):
    bot.remove_command("gw2")
    await bot.add_cog(GW2Key(bot))
