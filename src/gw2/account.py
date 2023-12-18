# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from src.bot.utils import bot_utils, chat_formatting
from src.database.dal.gw2.gw2_key_dal import Gw2KeyDal
from src.gw2.utils import gw2_utils
from src.gw2.utils.gw2_api import Gw2Api
from src.gw2.utils.gw2_exceptions import APIError


class GW2Account(commands.Cog):
    """(Commands related to users account)"""
    def __init__(self, bot):
        self.bot = bot

    async def account(self, ctx):
        """(General information about your GW2 account)
            Required API permissions: account
                gw2 account
        """

        await ctx.message.channel.typing()
        user_id = ctx.message.author.id
        gw2_api = Gw2Api(self.bot)
        gw2_key_dal = Gw2KeyDal(self.bot.db_session, self.bot.log)

        rs = await gw2_key_dal.get_server_user_api_key(ctx.guild.id, user_id)
        if len(rs) == 0:
            await ctx.message.channel.typing()
            await bot_utils.send_error_msg(
                ctx,
                "You dont have an API key registered in this server.\n"
                f"To add or replace an API key use: `{ctx.prefix}gw2 key add <api_key>`\n"
                f"To check your API key use: `{ctx.prefix}gw2 key info`"
            )
        else:
            permissions = str(rs[0]["permissions"])
            api_key = str(rs[0]["key"])
            is_valid_key = await gw2_api.check_api_key(api_key)
            if not isinstance(is_valid_key, dict):
                return await bot_utils.send_error_msg(
                    ctx,
                    is_valid_key.args[1] + "\n"
                    "This API Key is INVALID or no longer exists in gw2 api database.\n\n"
                    f"To add or replace an API key use: {ctx.prefix}gw2 key add <api_key>\n"
                    f"To check your API key use: `{ctx.prefix}gw2 key info`"
                )

            await ctx.message.channel.typing()
            if "account" not in permissions:
                return await bot_utils.send_private_error_msg(
                    ctx,
                    "Your API key doesnt have permission to access your gw2 account.\n"
                    "Please add one key with account permission."
                )
            else:
                try:
                    # getting infos gw2 api
                    await ctx.message.channel.typing()
                    endpoint = "account"
                    api_req_acc = await gw2_api.call_api(endpoint, key=api_key)

                    server_id = api_req_acc["world"]
                    endpoint = f"worlds/{server_id}"
                    api_req_server = await gw2_api.call_api(endpoint, key=api_key)

                    if "pvp" in permissions:
                        await ctx.message.channel.typing()
                        endpoint = "pvp/stats"
                        api_req_pvp = await gw2_api.call_api(endpoint, key=api_key)
                        pvprank = api_req_pvp["pvp_rank"] + api_req_pvp["pvp_rank_rollovers"]

                    # if "characters" in permissions:
                    #     api_req_characters= await gw2_api.call_api("characters", key=api_key)
                    #     char_names = dict()
                    #     for i, char_name in enumerate(api_req_characters):
                    #         await ctx.message.channel.typing()
                    #         endpoint = f"characters/{char_name}/core"
                    #         current_char = await gw2_api.call_api(endpoint, key=api_key)
                    #         char_names[char_name] = dict()
                    #         char_names[char_name]["race"]       = current_char["race"]
                    #         char_names[char_name]["gender"]     = current_char["gender"]
                    #         char_names[char_name]["profession"] = current_char["profession"]
                    #         char_names[char_name]["level"]      = current_char["level"]
                    #         char_names[char_name]["age"]        = current_char["age"]
                    #         char_names[char_name]["created"]    = current_char["created"]
                    #         char_names[char_name]["deaths"]     = current_char["deaths"]
                    #
                    # if "progression" in permissions:
                    #     await ctx.message.channel.typing()
                    #     endpoint = "account/achievements"
                    #     api_req_acc_achiev = await gw2_api.call_api(endpoint, key=api_key)
                    #     achiev_points = await gw2_utils.calculate_user_achiev_points(self, api_req_acc_achiev, api_req_acc)
                except Exception as e:
                    await bot_utils.send_error_msg(ctx, e)
                    return self.bot.log.error(ctx, e)

                await ctx.message.channel.typing()
                # acc_id          = api_req_acc["id"]
                age = api_req_acc["age"]
                guilds = api_req_acc["guilds"]
                acc_name = api_req_acc["name"]
                access = ' | '.join(api_req_acc["access"])
                access = access.replace("GuildWars2", "Guild Wars 2")
                access = access.replace("HeartOfThorns", "Heart Of Thorns")
                access = access.replace("PathOfFire", "Path Of Fire")
                is_commander = "Yes" if api_req_acc["commander"] else "No"
                created = api_req_acc["created"].split("T", 1)[0]
                server_name = api_req_server["name"]
                population = api_req_server["population"]

                color = self.bot.gw2_settings["EmbedColor"]
                embed = discord.Embed(title="Account Name", description=chat_formatting.inline(acc_name), color=color)
                embed.set_author(name=ctx.message.author.display_name, icon_url=ctx.message.author.avatar.url)
                await ctx.message.channel.typing()

                try:
                    guilds_names = []
                    guild_leader_names = []
                    if "guilds" in api_req_acc:
                        for i in range(0, len(guilds)):
                            guild_id = guilds[i]
                            try:
                                endpoint = "guild/" + guild_id
                                api_req_guild = await gw2_api.call_api(endpoint, key=api_key)
                            except Exception as e:
                                await bot_utils.send_error_msg(ctx, e)
                                return self.bot.log.error(ctx, e)
                            name = api_req_guild["name"]
                            tag = api_req_guild["tag"]
                            full_name = f"[{tag}] {name}"
                            guilds_names.insert(i, full_name)

                            if "guild_leader" in api_req_acc:
                                guild_leader = ','.join(api_req_acc["guild_leader"])
                                if len(guild_leader) > 0:
                                    if guild_id in guild_leader:
                                        guild_leader_names.insert(i, full_name)
                except APIError as e:
                    return self.bot.log.error(ctx, e)

                if "progression" in permissions:
                    await ctx.message.channel.typing()
                    fractallevel = api_req_acc["fractal_level"]
                    # daily_ap        = api_req_acc["daily_ap"]
                    # monthly_ap      = api_req_acc["monthly_ap"]
                    wvwrank = api_req_acc["wvw_rank"]
                    wvw_title = gw2_utils.get_wvw_rank_title(int(wvwrank))
                    embed.add_field(name="Fractal Level", value=chat_formatting.inline(fractallevel))
                    embed.add_field(name="WvW Rank", value=chat_formatting.inline(f"{wvw_title}\n({wvwrank})"))
                    # embed.add_field(name="Achievements Points", value=chat_formatting.inline(achiev_points))

                if "pvp" in permissions:
                    pvp_title = str(gw2_utils.get_pvp_rank_title(pvprank))
                    embed.add_field(name="PVP Rank", value=chat_formatting.inline(f"{pvp_title}\n({pvprank})"))

                embed.add_field(name="Commander Tag", value=chat_formatting.inline(is_commander))
                embed.add_field(name="Server", value=chat_formatting.inline(f"{server_name}\n({population})"))
                embed.add_field(name="Access", value=chat_formatting.inline(access), inline=False)

                if len(guilds_names) > 0:
                    embed.add_field(name="Guilds", value=chat_formatting.inline('\n'.join(guilds_names)), inline=False)

                if len(guild_leader_names) > 0:
                    embed.add_field(name="Guild Leader", value=chat_formatting.inline('\n'.join(guild_leader_names)),
                                    inline=False)

                hours = age / 60
                days = hours / 24
                # years = days / 365.25
                embed.add_field(name="Created", value=chat_formatting.inline(f"{created} ({round(days)} days ago)"),
                                inline=False)

                await bot_utils.send_embed(ctx, embed)
