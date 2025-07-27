import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from src.bot.tools import bot_utils, chat_formatting
from src.database.dal.gw2.gw2_key_dal import Gw2KeyDal
from src.gw2.cogs.gw2 import GuildWars2
from src.gw2.constants import gw2_messages
from src.gw2.tools import gw2_utils
from src.gw2.tools.gw2_client import Gw2Client
from src.gw2.tools.gw2_cooldowns import GW2CoolDowns


class GW2Account(GuildWars2):
    """(Commands related to users account)"""

    def __init__(self, bot):
        super().__init__(bot)


@GW2Account.gw2.command()
@commands.cooldown(1, GW2CoolDowns.Account.value, BucketType.user)
async def account(ctx):
    """(General information about your GW2 account)
    Required API permissions: account
        gw2 account
    """

    await ctx.message.channel.typing()
    gw2_key_dal = Gw2KeyDal(ctx.bot.db_session, ctx.bot.log)
    rs = await gw2_key_dal.get_api_key_by_user(ctx.message.author.id)
    if not rs:
        msg = gw2_messages.NO_API_KEY
        msg += gw2_messages.KEY_ADD_INFO_HELP.format(ctx.prefix)
        msg += gw2_messages.KEY_MORE_INFO_HELP.format(ctx.prefix)
        return await bot_utils.send_error_msg(ctx, msg)

    api_key = str(rs[0]["key"])
    gw2_api = Gw2Client(ctx.bot)
    is_valid_key = await gw2_api.check_api_key(api_key)
    if not isinstance(is_valid_key, dict):
        msg = f"{is_valid_key.args[1]}\n"
        msg += gw2_messages.INVALID_API_KEY_HELP_MESSAGE.format(ctx.prefix)
        msg += gw2_messages.KEY_ADD_INFO_HELP.format(ctx.prefix)
        msg += gw2_messages.KEY_MORE_INFO_HELP.format(ctx.prefix)
        return await bot_utils.send_error_msg(ctx, msg)

    permissions = str(rs[0]["permissions"])
    if "account" not in permissions:
        return await bot_utils.send_error_msg(ctx, gw2_messages.API_KEY_NO_PERMISSION, True)

    try:
        # getting infos gw2 api
        await ctx.message.channel.typing()
        api_req_acc = await gw2_api.call_api("account", api_key)

        server_id = api_req_acc["world"]
        api_req_server = await gw2_api.call_api(f"worlds/{server_id}", api_key)

        await ctx.message.channel.typing()
        acc_name = api_req_acc["name"]

        access_normalized = []
        for each in api_req_acc["access"]:
            normalized = "".join([f" {c.upper()}" if c.isupper() or c.isdigit() else c for c in each]).lstrip()
            access_normalized.append(normalized)
        access = '\n'.join(access_normalized)

        is_commander = "Yes" if api_req_acc["commander"] else "No"
        server_name = api_req_server["name"]
        population = api_req_server["population"]

        color = ctx.bot.settings["gw2"]["EmbedColor"]
        embed = discord.Embed(title="Account Name", description=chat_formatting.inline(acc_name), color=color)
        embed.set_thumbnail(url=ctx.message.author.avatar.url)
        embed.set_author(name=ctx.message.author.display_name, icon_url=ctx.message.author.avatar.url)
        embed.add_field(name="Access", value=chat_formatting.inline(access), inline=False)
        embed.add_field(name="Commander Tag", value=chat_formatting.inline(is_commander))
        embed.add_field(name="Server", value=chat_formatting.inline(f"{server_name} ({population})"))

        if "characters" in permissions:
            api_req_characters = await gw2_api.call_api("characters", api_key)
            embed.add_field(name="Characters", value=chat_formatting.inline(len(api_req_characters)), inline=False)

        if "progression" in permissions:
            await ctx.message.channel.typing()
            fractallevel = api_req_acc["fractal_level"]
            embed.add_field(name="Fractal Level", value=chat_formatting.inline(fractallevel), inline=False)

            api_req_acc_achiev = await gw2_api.call_api("account/achievements", api_key)
            achiev_points = await gw2_utils.calculate_user_achiev_points(ctx, api_req_acc_achiev, api_req_acc)
            embed.add_field(name="Achievements Points", value=chat_formatting.inline(achiev_points), inline=False)

            wvwrank = api_req_acc["wvw_rank"]
            wvw_title = gw2_utils.get_wvw_rank_title(int(wvwrank))
            embed.add_field(name="WvW Rank", value=chat_formatting.inline(f"{wvw_title} ({wvwrank})"), inline=False)

        if "pvp" in permissions:
            await ctx.message.channel.typing()
            api_req_pvp = await gw2_api.call_api("pvp/stats", api_key)
            pvprank = api_req_pvp["pvp_rank"] + api_req_pvp["pvp_rank_rollovers"]
            pvp_title = str(gw2_utils.get_pvp_rank_title(pvprank))
            embed.add_field(name="PVP Rank", value=chat_formatting.inline(f"{pvp_title} ({pvprank})"), inline=False)

        await ctx.message.channel.typing()
        guilds_names = []
        guild_leader_names = []
        if "guilds" in api_req_acc:
            guilds = api_req_acc["guilds"]
            for i in range(0, len(guilds)):
                guild_id = guilds[i]
                try:
                    api_req_guild = await gw2_api.call_api(f"guild/{guild_id}", api_key)
                except Exception as e:
                    await bot_utils.send_error_msg(ctx, e)
                    return ctx.bot.log.error(ctx, e)
                name = api_req_guild["name"]
                tag = api_req_guild["tag"]
                full_name = f"[{tag}] {name}"
                guilds_names.insert(i, full_name)

                if "guild_leader" in api_req_acc:
                    guild_leader = ",".join(api_req_acc["guild_leader"])
                    if len(guild_leader) > 0 and guild_id in guild_leader:
                        guild_leader_names.insert(i, full_name)

        if len(guilds_names) > 0:
            embed.add_field(name="Guilds", value=chat_formatting.inline("\n".join(guilds_names)), inline=False)
        if len(guild_leader_names) > 0:
            embed.add_field(
                name="Guild Leader",
                value=chat_formatting.inline("\n".join(guild_leader_names)),
                inline=False,
            )

        days = (api_req_acc["age"] / 60) / 24
        created = api_req_acc["created"].split("T", 1)[0]
        embed.add_field(
            name="Created",
            value=chat_formatting.inline(f"{created} ({round(days)} days ago)"),
            inline=False,
        )

        embed.set_footer(icon_url=ctx.bot.user.avatar.url, text=f"{bot_utils.get_current_date_time_str_long()} UTC")
        await bot_utils.send_embed(ctx, embed)

    except Exception as e:
        await bot_utils.send_error_msg(ctx, e)
        return ctx.bot.log.error(ctx, e)


async def setup(bot):
    bot.remove_command("gw2")
    await bot.add_cog(GW2Account(bot))
