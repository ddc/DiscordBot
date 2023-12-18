# -*- coding: utf-8 -*-
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from src.bot.utils import bot_utils
from src.bot.utils.checks import Checks
from src.gw2.account import GW2Account
from src.gw2.config import GW2Config
from src.gw2.daily import GW2Daily
from src.gw2.key import GW2Key
from src.gw2.misc import GW2Misc
from src.gw2.sessions import GW2Session
from src.gw2.utils.gw2_cooldowns import GW2CoolDowns
from src.gw2.wvw import GW2WvW


class GuildWars2(commands.Cog):
    """(Commands related to Guild Wars 2)"""
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="gw2")
    async def gw2_group(self, ctx):
        """(Guild Wars 2 group command)
            gw2 config
            gw2 worlds
            gw2 account
            gw2 lastsession
            gw2 kdr world_name
            gw2 wvwinfo world_name
            gw2 wiki name_to_search
            gw2 info info_to_search
            gw2 [match | wvwinfo] world_name
            gw2 daily [pve | pvp | wvw | fractals]
            gw2 key add api_key
            gw2 key [remove | info]
        """
        await bot_utils.invoke_subcommand(ctx, "gw2")

    @gw2_group.command()
    @commands.cooldown(1, GW2CoolDowns.Account.value, BucketType.user)
    async def account(self, ctx):
        gw2_account = GW2Account(self.bot)
        await gw2_account.account(ctx)

    @gw2_group.command()
    @commands.cooldown(1, GW2CoolDowns.ApiKeys.value, BucketType.user)
    @Checks.check_is_admin()
    async def config(self, ctx, *, sub_command: str = None):
        """(Guild Wars 2 configurations commands - Admin)
            ------------------------------------------------------
            List all gw2 configurations in the current server:
                gw2 config list
            ------------------------------------------------------
            Configure if the bot should record users last sessions:
                gw2 config lastsession [on | off]
            ------------------------------------------------------
        """

        if sub_command is not None:
            gw2_config = GW2Config(self.bot)
            await gw2_config.config(ctx, sub_command)
        else:
            cmd = self.bot.get_command("gw2 config")
            await bot_utils.send_help_msg(ctx, cmd)

    @gw2_group.command()
    @commands.cooldown(1, GW2CoolDowns.Daily.value, BucketType.user)
    async def daily(self, ctx, *, daily_type: str = None):
        """(Show today's Dailies)
            gw2 daily pve
            gw2 daily pvp
            gw2 daily wvw
            gw2 daily fractals
        """
        if daily_type is not None:
            gw2_daily = GW2Daily(self.bot)
            await gw2_daily.daily(ctx, daily_type)
        else:
            cmd = self.bot.get_command("gw2 daily")
            await bot_utils.send_help_msg(ctx, cmd)

    @gw2_group.command()
    @commands.cooldown(1, GW2CoolDowns.ApiKeys.value, BucketType.user)
    async def key(self, ctx, *, cmd_api_key: str = None):
        """(Commands related to GW2 API keys)
            To generate an API key, head to https://account.arena.net, and log in.
            In the "Applications" tab, generate a new key, with all permissions.
            Required API permissions: account
                gw2 key add api_key   (Adds a key and associates it with your discord account)
                gw2 key remove        (Removes your GW2 API key from the bot)
                gw2 key info          (Information about your GW2 API keys)
        """

        if cmd_api_key is not None:
            gw2_key = GW2Key(self.bot)
            await gw2_key.key(ctx, cmd_api_key)
        else:
            cmd = self.bot.get_command("gw2 key")
            await bot_utils.send_help_msg(ctx, cmd)

    @gw2_group.command(name="lastsession")
    @commands.cooldown(1, GW2CoolDowns.LastSession.value, BucketType.user)
    async def last_session(self, ctx):
        gw2_session = GW2Session(self.bot)
        await gw2_session.lastSession(ctx)

    @gw2_group.command()
    @commands.cooldown(1, GW2CoolDowns.Wvw.value, BucketType.user)
    async def wvwinfo(self, ctx, *, world: str = None):
        gw2_wvw = GW2WvW(self.bot)
        await gw2_wvw.wvwinfo(ctx, world)

    @gw2_group.command()
    @commands.cooldown(1, GW2CoolDowns.Wvw.value, BucketType.user)
    async def match(self, ctx, *, world: str = None):
        gw2_wvw = GW2WvW(self.bot)
        await gw2_wvw.match(ctx, world)

    @gw2_group.command()
    @commands.cooldown(1, GW2CoolDowns.Wvw.value, BucketType.user)
    async def kdr(self, ctx, *, world: str = None):
        gw2_wvw = GW2WvW(self.bot)
        await gw2_wvw.kdr(ctx, world)

    @gw2_group.command()
    @commands.cooldown(1, GW2CoolDowns.Misc.value, BucketType.user)
    async def wiki(self, ctx, *, search: str = None):
        """ (Search the Guild wars 2 wiki)
            gw2 wiki name_to_search
        """

        if search is not None:
            gw2_misc = GW2Misc(self.bot)
            await gw2_misc.wiki(ctx, search)
        else:
            cmd = self.bot.get_command("gw2 wiki")
            await bot_utils.send_help_msg(ctx, cmd)

    @gw2_group.command()
    @commands.cooldown(1, GW2CoolDowns.Misc.value, BucketType.user)
    async def info(self, ctx, *, skill: str = None):
        """ (Information about a given name/skill/rune)
            gw2 info info_to_search
        """

        if skill is not None:
            gw2_misc = GW2Misc(self.bot)
            await gw2_misc.info(ctx, skill)
        else:
            cmd = self.bot.get_command("gw2 info")
            await bot_utils.send_help_msg(ctx, cmd)

    @gw2_group.command()
    @commands.cooldown(1, GW2CoolDowns.Misc.value, BucketType.user)
    async def worlds(self, ctx):
        gw2_misc = GW2Misc(self.bot)
        await gw2_misc.worlds(ctx)


async def setup(bot):
    await bot.add_cog(GuildWars2(bot))
