import discord
from discord.ext import commands
from src.bot.tools import bot_utils, chat_formatting
from src.database.dal.gw2.gw2_configs_dal import Gw2ConfigsDal
from src.database.dal.gw2.gw2_key_dal import Gw2KeyDal
from src.database.dal.gw2.gw2_session_chars_dal import Gw2SessionCharsDal
from src.database.dal.gw2.gw2_sessions_dal import Gw2SessionsDal
from src.gw2.cogs.gw2 import GuildWars2
from src.gw2.constants import gw2_messages
from src.gw2.constants.gw2_currencies import WALLET_DISPLAY_NAMES
from src.gw2.tools import gw2_utils
from src.gw2.tools.gw2_cooldowns import GW2CoolDowns


class GW2Session(GuildWars2):
    """Guild Wars 2 commands for player session tracking."""

    def __init__(self, bot):
        super().__init__(bot)


@GW2Session.gw2.command()
@commands.guild_only()
@commands.cooldown(1, GW2CoolDowns.Session.seconds, commands.BucketType.user)
async def session(ctx):
    """Display information about your last Guild Wars 2 game session.

    Required API permissions: Account, Characters, Progression, Wallet

    Requirements:
        1) Start Discord, make sure you are not set to invisible
        2) Add GW2 API Key (gw2 key add api_key)
        3) Show on Discord that you are playing Guild Wars 2
        4) Start GW2

    Usage:
        gw2 session
    """

    user_id = ctx.message.author.id
    gw2_key_dal = Gw2KeyDal(ctx.bot.db_session, ctx.bot.log)
    rs_api_key = await gw2_key_dal.get_api_key_by_user(user_id)
    if not rs_api_key:
        msg = gw2_messages.NO_API_KEY
        msg += gw2_messages.key_add_info_help(ctx.prefix)
        msg += gw2_messages.key_more_info_help(ctx.prefix)
        return await bot_utils.send_error_msg(ctx, msg)

    gw2_configs = Gw2ConfigsDal(ctx.bot.db_session, ctx.bot.log)
    rs_gw2_sc = await gw2_configs.get_gw2_server_configs(ctx.guild.id)
    if len(rs_gw2_sc) == 0 or (len(rs_gw2_sc) > 0 and not rs_gw2_sc[0]["session"]):
        return await bot_utils.send_warning_msg(ctx, gw2_messages.session_not_active(ctx.prefix))

    api_key = rs_api_key[0]["key"]
    gw2_server = rs_api_key[0]["server"]
    key_permissions = rs_api_key[0]["permissions"]
    account = True
    wallet = True
    progression = True
    characters = True

    if "account" not in key_permissions:
        account = False
    if "wallet" not in key_permissions:
        wallet = False
    if "progression" not in key_permissions:
        progression = False
    if "characters" not in key_permissions:
        characters = False

    if not any([account, wallet, progression, characters]):
        error_msg = f"{gw2_messages.SESSION_MISSING_PERMISSIONS_TITLE}:\n"
        error_msg += "- account is OK\n" if account is True else "- account is MISSING\n"
        error_msg += "- characters is OK\n" if characters is True else "- characters is MISSING\n"
        error_msg += "- progression is OK\n" if progression is True else "- progression is MISSING\n"
        error_msg += "- wallet is OK\n" if wallet is True else "- wallet is MISSING\n"
        error_msg += (
            f"{gw2_messages.ADD_RIGHT_API_KEY_PERMISSIONS}\n"
            f"{gw2_messages.key_add_info_help(ctx.prefix)}"
            f"{gw2_messages.key_more_info_help(ctx.prefix)}"
        )
        return await bot_utils.send_error_msg(ctx, error_msg)

    gw2_session_dal = Gw2SessionsDal(ctx.bot.db_session, ctx.bot.log)
    rs_session = await gw2_session_dal.get_user_last_session(user_id)
    if not rs_session:
        return await bot_utils.send_error_msg(ctx, gw2_messages.USER_NO_SESSION_FOUND)

    rs_start = rs_session[0]["start"]
    rs_end = rs_session[0]["end"]

    if rs_end is None:
        # Check if the user is currently playing GW2
        is_playing = (
            not isinstance(ctx.channel, discord.DMChannel)
            and hasattr(ctx.message.author, "activity")
            and ctx.message.author.activity is not None
            and "guild wars 2" in str(ctx.message.author.activity.name).lower()
        )
        if is_playing:
            return await gw2_utils.send_msg(ctx, gw2_messages.SESSION_IN_PROGRESS)
        # Game stopped but end data not saved yet — bot may still be updating
        return await gw2_utils.send_msg(ctx, gw2_messages.SESSION_BOT_STILL_UPDATING)

    progress_msg = await gw2_utils.send_progress_embed(
        ctx, "Please wait, I'm fetching your session data... (this may take a moment)"
    )

    try:
        color = ctx.bot.settings["gw2"]["EmbedColor"]

        # Use JSONB date fields for session duration
        start_time = bot_utils.convert_str_to_datetime_short(rs_start["date"])
        end_time = bot_utils.convert_str_to_datetime_short(rs_end["date"])

        time_passed = gw2_utils.get_time_passed(start_time, end_time)
        player_wait_minutes = 1
        if time_passed.hours == 0 and time_passed.minutes < player_wait_minutes:
            wait_time = str(player_wait_minutes - time_passed.minutes)
            m = "minute" if wait_time == "1" else "minutes"
            await progress_msg.delete()
            return await gw2_utils.send_msg(
                ctx, f"{gw2_messages.SESSION_BOT_STILL_UPDATING}\n {gw2_messages.WAITING_TIME}: `{wait_time} {m}`"
            )

        acc_name = rs_session[0]["acc_name"]
        session_date = rs_start["date"].split()[0]
        embed = discord.Embed(color=color)
        embed.set_author(
            name=f"{ctx.message.author.display_name}'s {gw2_messages.SESSION_TITLE} ({session_date})",
            icon_url=ctx.message.author.display_avatar.url,
        )
        embed.add_field(name=gw2_messages.ACCOUNT_NAME, value=chat_formatting.inline(acc_name))
        embed.add_field(name=gw2_messages.SERVER, value=chat_formatting.inline(gw2_server))

        # Play time from DB timestamps (session duration)
        play_time_str = gw2_utils.format_seconds_to_time(int(time_passed.timedelta.total_seconds()))
        embed.add_field(name=gw2_messages.PLAY_TIME, value=chat_formatting.inline(play_time_str))

        # Gold (special formatting)
        _add_gold_field(embed, rs_start, rs_end)

        # Deaths
        gw2_session_chars_dal = Gw2SessionCharsDal(ctx.bot.db_session, ctx.bot.log)
        rs_chars_start = await gw2_session_chars_dal.get_all_start_characters(user_id)
        if rs_chars_start:
            rs_chars_end = await gw2_session_chars_dal.get_all_end_characters(user_id)
            _add_deaths_field(embed, rs_chars_start, rs_chars_end)

        # WvW achievement-based stats
        _add_wvw_stats(embed, rs_start, rs_end)

        # All wallet currencies (except gold, handled above)
        _add_wallet_currency_fields(embed, rs_start, rs_end)

        embed.set_footer(
            icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None,
            text=f"{bot_utils.get_current_date_time_str_long()} UTC",
        )

        if (
            not (isinstance(ctx.channel, discord.DMChannel))
            and hasattr(ctx.message.author, "activity")
            and ctx.message.author.activity is not None
            and "guild wars 2" in str(ctx.message.author.activity.name).lower()
        ):
            still_playing_msg = f"{ctx.message.author.mention}\n {gw2_messages.SESSION_USER_STILL_PLAYING}"
            await gw2_utils.end_session(ctx.bot, ctx.message.author, api_key)
            await ctx.send(still_playing_msg)

        await progress_msg.delete()
        await bot_utils.send_paginated_embed(ctx, embed)
    except Exception as e:
        await progress_msg.delete()
        await bot_utils.send_error_msg(ctx, e)
        return ctx.bot.log.error(ctx, e)
    return None


def _add_gold_field(embed: discord.Embed, rs_start: dict, rs_end: dict) -> None:
    """Add gold gained/lost field to embed."""
    if "gold" not in rs_start or "gold" not in rs_end:
        return
    start_gold = rs_start["gold"]
    end_gold = rs_end["gold"]
    if start_gold != end_gold:
        diff = end_gold - start_gold
        full_gold = str(diff)
        formatted_gold = gw2_utils.format_gold(full_gold)
        if diff > 0:
            embed.add_field(
                name="Gold",
                value=chat_formatting.inline(f"+{formatted_gold}"),
                inline=False,
            )
        elif diff < 0:
            final_result = f"{formatted_gold}"
            if formatted_gold[0] != "-":
                final_result = f"-{formatted_gold}"
            embed.add_field(name="Gold", value=chat_formatting.inline(str(final_result)), inline=False)


def _add_deaths_field(embed: discord.Embed, rs_chars_start: list[dict], rs_chars_end: list[dict]) -> None:
    """Add deaths field to embed.

    Uses a dict keyed on character name to deduplicate entries from
    multiple guild event firings.
    """
    if not rs_chars_end:
        return

    # Build lookup from end chars, deduplicating by name (keep first occurrence)
    end_lookup: dict[str, dict] = {}
    for char_end in rs_chars_end:
        name = char_end["name"]
        if name not in end_lookup:
            end_lookup[name] = char_end

    death_lines: list[str] = []
    total_deaths = 0

    for char_start in rs_chars_start:
        name = char_start["name"]
        char_end = end_lookup.get(name)
        if char_end and char_start["deaths"] != char_end["deaths"]:
            profession = char_start["profession"]
            time_deaths = int(char_end["deaths"]) - int(char_start["deaths"])
            total_deaths += time_deaths
            death_lines.append(f"{name} ({profession}): {time_deaths}")

    if death_lines:
        death_lines.append(f"Total: {total_deaths}")
        value = "\n".join(death_lines)
        # Truncate if it would exceed Discord's 1024-char field value limit
        if len(value) > 1020:
            value = value[:1017] + "..."
        embed.add_field(
            name=gw2_messages.TIMES_YOU_DIED,
            value=chat_formatting.inline(value),
            inline=False,
        )


def _add_wvw_stats(embed: discord.Embed, rs_start: dict, rs_end: dict) -> None:
    """Add WvW achievement-based stats to embed."""
    wvw_fields = [
        ("wvw_rank", gw2_messages.WVW_RANKS),
        ("yaks", gw2_messages.YAKS_KILLED),
        ("yaks_scorted", gw2_messages.YAKS_SCORTED),
        ("players", gw2_messages.PLAYERS_KILLED),
        ("keeps", gw2_messages.KEEPS_CAPTURED),
        ("towers", gw2_messages.TOWERS_CAPTURED),
        ("camps", gw2_messages.CAMPS_CAPTURED),
        ("castles", gw2_messages.SMC_CAPTURED),
    ]

    for stat_key, field_name in wvw_fields:
        if stat_key not in rs_start or stat_key not in rs_end:
            continue
        start_val = rs_start[stat_key]
        end_val = rs_end[stat_key]
        if start_val != end_val:
            diff = end_val - start_val
            embed.add_field(name=field_name, value=chat_formatting.inline(str(diff)))


def _add_wallet_currency_fields(embed: discord.Embed, rs_start: dict, rs_end: dict) -> None:
    """Add wallet currency fields to embed (all except gold, which has special formatting).

    Each changed currency gets its own inline field for clean Discord rendering.
    """
    for stat_key, display_name in WALLET_DISPLAY_NAMES.items():
        if stat_key == "gold":
            continue
        if stat_key not in rs_start or stat_key not in rs_end:
            continue

        start_val = rs_start[stat_key]
        end_val = rs_end[stat_key]
        if start_val != end_val:
            diff = end_val - start_val
            embed.add_field(
                name=display_name,
                value=chat_formatting.inline(f"+{diff}" if diff > 0 else str(diff)),
                inline=True,
            )


async def setup(bot):
    bot.remove_command("gw2")
    await bot.add_cog(GW2Session(bot))
