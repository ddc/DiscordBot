import asyncio
import discord
from discord.ext import commands
from src.bot.tools import bot_utils, chat_formatting
from src.database.dal.gw2.gw2_key_dal import Gw2KeyDal
from src.gw2.cogs.gw2 import GuildWars2
from src.gw2.constants import gw2_messages
from src.gw2.tools import gw2_utils
from src.gw2.tools.gw2_client import Gw2Client
from src.gw2.tools.gw2_cooldowns import GW2CoolDowns


class GW2Characters(GuildWars2):
    """Guild Wars 2 commands for character information."""

    def __init__(self, bot):
        super().__init__(bot)


@GW2Characters.gw2.command()
@commands.cooldown(1, GW2CoolDowns.Characters.seconds, commands.BucketType.user)
async def characters(ctx):
    """Display information about your Guild Wars 2 characters.

    Required API permissions: account, characters

    Usage:
        gw2 characters
    """

    await ctx.message.channel.typing()
    gw2_key_dal = Gw2KeyDal(ctx.bot.db_session, ctx.bot.log)
    rs = await gw2_key_dal.get_api_key_by_user(ctx.message.author.id)
    if not rs:
        msg = gw2_messages.NO_API_KEY
        msg += gw2_messages.key_add_info_help(ctx.prefix)
        msg += gw2_messages.key_more_info_help(ctx.prefix)
        return await bot_utils.send_error_msg(ctx, msg)

    api_key = str(rs[0]["key"])
    gw2_api = Gw2Client(ctx.bot)
    is_valid_key = await gw2_api.check_api_key(api_key)
    if not isinstance(is_valid_key, dict):
        msg = f"{is_valid_key.args[1]}\n"
        msg += gw2_messages.INVALID_API_KEY_HELP_MESSAGE
        msg += gw2_messages.key_add_info_help(ctx.prefix)
        msg += gw2_messages.key_more_info_help(ctx.prefix)
        return await bot_utils.send_error_msg(ctx, msg)

    permissions = str(rs[0]["permissions"])
    if "characters" not in permissions or "account" not in permissions:
        return await bot_utils.send_error_msg(ctx, gw2_messages.API_KEY_NO_PERMISSION, True)

    progress_msg = await gw2_utils.send_progress_embed(
        ctx, "Please wait, I'm fetching your character data... (this may take a moment)"
    )

    try:
        # Fetch account info and all characters in parallel
        api_req_acc, characters_data = await asyncio.gather(
            gw2_api.call_api("account", api_key),
            gw2_api.call_api("characters?ids=all", api_key),
        )

        color = ctx.bot.settings["gw2"]["EmbedColor"]
        embed = discord.Embed(
            title="Account Name",
            description=chat_formatting.inline(api_req_acc["name"]),
            color=color,
        )
        embed.set_thumbnail(url=ctx.message.author.display_avatar.url)
        embed.set_author(name=ctx.message.author.display_name, icon_url=ctx.message.author.display_avatar.url)

        for char in characters_data:
            days = (char["age"] / 60) / 24
            created = char["created"].split("T", 1)[0]
            embed.add_field(
                name=char["name"],
                value=chat_formatting.inline(
                    f"Race: {char['race']}\n"
                    f"Gender: {char['gender']}\n"
                    f"Profession: {char['profession']}\n"
                    f"Level: {char['level']}\n"
                    f"Deaths: {char['deaths']}\n"
                    f"Age: {round(days)} days\n"
                    f"Date: {created}\n"
                ),
            )

        embed.set_footer(
            icon_url=ctx.bot.user.display_avatar.url, text=f"{bot_utils.get_current_date_time_str_long()} UTC"
        )
        await progress_msg.delete()
        await bot_utils.send_embed(ctx, embed)

    except Exception as e:
        await progress_msg.delete()
        await bot_utils.send_error_msg(ctx, e)
        return ctx.bot.log.error(ctx, e)


async def setup(bot):
    bot.remove_command("gw2")
    await bot.add_cog(GW2Characters(bot))
