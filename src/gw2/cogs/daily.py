import discord
from discord.ext import commands
from src.bot.tools import bot_utils
from src.database.dal.gw2.gw2_key_dal import Gw2KeyDal
from src.gw2.cogs.gw2 import GuildWars2
from src.gw2.constants import gw2_messages, gw2_variables
from src.gw2.tools import gw2_utils
from src.gw2.tools.gw2_client import Gw2Client
from src.gw2.tools.gw2_cooldowns import GW2CoolDowns

PERIODS = ("daily", "weekly", "special")


class GW2Daily(GuildWars2):
    """Guild Wars 2 Wizard's Vault objectives (the replacement for the old dailies)."""

    def __init__(self, bot):
        super().__init__(bot)


@GW2Daily.gw2.command()
@commands.cooldown(1, GW2CoolDowns.Daily.seconds, commands.BucketType.user)
async def daily(ctx, period: str = "daily"):
    """Display your Wizard's Vault objectives and progress.

    Required API permissions: account, progression

    Usage:
        gw2 daily
        gw2 daily weekly
        gw2 daily special
    """

    period = period.lower()
    if period not in PERIODS:
        raise commands.BadArgument(message="BadArgument")

    gw2_key_dal = Gw2KeyDal(ctx.bot.db_session, ctx.bot.log)
    rs = await gw2_key_dal.get_api_key_by_user(ctx.message.author.id)
    if not rs:
        msg = gw2_messages.Key.NO_API_KEY
        msg += gw2_messages.Key.add_info_help(ctx.prefix)
        msg += gw2_messages.Key.more_info_help(ctx.prefix)
        return await bot_utils.send_error_msg(ctx, msg)

    api_key = str(rs[0]["key"])
    progress_msg = await gw2_utils.send_progress_embed(ctx)
    try:
        gw2_api = Gw2Client(ctx.bot)
        vault = await gw2_api.call_api(f"{gw2_variables.API_ACCOUNT_WIZARDSVAULT}/{period}", api_key)
    except Exception as e:
        await progress_msg.delete()
        await bot_utils.send_error_msg(ctx, e)
        return ctx.bot.log.error(ctx, e)

    await progress_msg.delete()
    objectives = (vault or {}).get("objectives") or []
    if not objectives:
        return await bot_utils.send_warning_msg(ctx, gw2_messages.Daily.NO_OBJECTIVES)

    embed = _build_vault_embed(ctx, period, vault, objectives)
    await bot_utils.send_paginated_embed(ctx, embed)
    return None


def _build_vault_embed(ctx, period: str, vault: dict, objectives: list[dict]) -> discord.Embed:
    embed = discord.Embed(
        title=gw2_messages.Daily.title(period),
        description=_meta_progress_line(vault),
        color=ctx.bot.settings["gw2"]["EmbedColor"],
    )
    embed.set_author(name=ctx.message.author.display_name, icon_url=ctx.message.author.display_avatar.url)
    for objective in objectives:
        embed.add_field(name=objective["title"][:256], value=_objective_line(objective), inline=False)
    embed.set_footer(text=f"{bot_utils.get_current_date_time_str_long()} UTC")
    return embed


def _meta_progress_line(vault: dict) -> str | None:
    """Daily/weekly responses carry a meta reward; special objectives do not."""
    if "meta_progress_complete" not in vault:
        return None
    line = (
        f"{gw2_messages.Daily.META_PROGRESS}: `{vault['meta_progress_current']}/{vault['meta_progress_complete']}`"
        f" · {vault.get('meta_reward_astral', 0)} Astral Acclaim"
    )
    if vault.get("meta_reward_claimed"):
        line += f" ({gw2_messages.Daily.CLAIMED})"
    return line


def _objective_line(objective: dict) -> str:
    done = "✅ " if objective.get("claimed") else ""
    return (
        f"{done}`{objective['track']}` · {objective['acclaim']} AA · "
        f"`{objective['progress_current']}/{objective['progress_complete']}`"
    )


async def setup(bot):
    bot.remove_command("gw2")
    await bot.add_cog(GW2Daily(bot))
