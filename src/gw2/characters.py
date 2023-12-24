# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from src.bot.utils import bot_utils, chat_formatting
from src.database.dal.gw2.gw2_key_dal import Gw2KeyDal
from src.gw2.gw2 import GuildWars2
from src.gw2.utils import gw2_utils
from src.gw2.utils.gw2_api import Gw2Api
from src.gw2.utils.gw2_cooldowns import GW2CoolDowns
from src.gw2.utils.gw2_exceptions import APIError


class GW2Characters(GuildWars2):
    """(Commands related to users characters)"""
    def __init__(self, bot):
        super().__init__(bot)


@GW2Characters.gw2.command()
@commands.cooldown(1, GW2CoolDowns.Account.value, BucketType.user)
async def characters(ctx):
    """(General information about your GW2 characters)
        Required API permissions: account
            gw2 characters
    """

    await ctx.message.channel.typing()

    gw2_key_dal = Gw2KeyDal(ctx.bot.db_session, ctx.bot.log)
    rs = await gw2_key_dal.get_api_key_by_user(ctx.message.author.id)
    if not rs:
        return await bot_utils.send_error_msg(
            ctx,
            "You dont have an API key registered.\n"
            f"To add or replace an API key send a DM with: `{ctx.prefix}gw2 key add <api_key>`\n"
            f"To check your API key: `{ctx.prefix}gw2 key info`"
        )

    api_key = str(rs[0]["key"])
    gw2_api = Gw2Api(ctx.bot)
    is_valid_key = await gw2_api.check_api_key(api_key)
    if not isinstance(is_valid_key, dict):
        return await bot_utils.send_error_msg(
            ctx,
            is_valid_key.args[1] + "\n"
            "This API Key is INVALID or no longer exists in gw2 api database.\n"
            f"To add or replace an API key send a DM with: `{ctx.prefix}gw2 key add <api_key>`\n"
            f"To check your API key: `{ctx.prefix}gw2 key info`"
        )

    permissions = str(rs[0]["permissions"])
    if "characters" not in permissions or "account" not in permissions:
        return await bot_utils.send_error_msg(
            ctx,
            "Your API key doesnt have permission to access your gw2 account.\n"
            "Please add one key with account and characters permission.",
            True
        )

    try:
        await ctx.message.channel.typing()
        api_req_acc = await gw2_api.call_api("account", key=api_key)

        color = ctx.bot.settings["gw2"]["EmbedColor"]
        embed = discord.Embed(title="Account Name", description=chat_formatting.inline(api_req_acc["name"]), color=color)
        embed.set_thumbnail(url=ctx.message.author.avatar.url)
        embed.set_author(name=ctx.message.author.display_name, icon_url=ctx.message.author.avatar.url)

        api_req_characters = await gw2_api.call_api("characters", key=api_key)
        for char_name in api_req_characters:
            await ctx.message.channel.typing()
            current_char = await gw2_api.call_api(f"characters/{char_name}/core", key=api_key)
            days = (current_char["age"] / 60) / 24
            created = current_char["created"].split("T", 1)[0]
            embed.add_field(name=char_name, value=chat_formatting.inline(
                f"Race: {current_char['race']}\n"
                f"Gender: {current_char['gender']}\n"
                f"Profession: {current_char['profession']}\n"
                f"Level: {current_char['level']}\n"
                f"Deaths: {current_char['deaths']}\n"
                f"Age: {round(days)} days\n"
                f"Date: {created}\n"
            ))

        embed.set_footer(icon_url=ctx.bot.user.avatar.url, text=f"{bot_utils.get_current_date_time_str()} UTC")
        await bot_utils.send_embed(ctx, embed)

    except Exception as e:
        await bot_utils.send_error_msg(ctx, e)
        return ctx.bot.log.error(ctx, e)


async def setup(bot):
    bot.remove_command("gw2")
    await bot.add_cog(GW2Characters(bot))
