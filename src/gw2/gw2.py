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
        """(Commands related to Guild Wars 2)

        Examples:

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

        if ctx.invoked_subcommand is None:
            if ctx.command is not None:
                cmd = ctx.command
            else:
                cmd = self.bot.get_command("gw2")

            await bot_utils.send_help_msg(self, ctx, cmd)
            return
        ctx.invoked_subcommand

    @gw2_group.command()
    @commands.cooldown(1, GW2CoolDowns.Account.value, BucketType.user)
    async def account(self, ctx):
        await GW2Account.gw2_account(self, ctx)

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
        Configure the timer the bot should check for api roles in seconds:
            gw2 config roletimer 3600
        ------------------------------------------------------
        Configure if the bot should add role that matches gw2 servers:

            * Categories with "Public" names in it wont be affect it. *
            Examples that wont be affected it:
            Public Chat
            Public Raids
            Public Informations

            Example:
            gw2 config apirole [on | off] Blackgate
        ------------------------------------------------------
        """

        if sub_command is not None:
            await GW2Config.gw2_config(self, ctx, sub_command)
        else:
            cmd = self.bot.get_command("gw2 config")
            await bot_utils.send_help_msg(self, ctx, cmd)

    @gw2_group.command()
    @commands.cooldown(1, GW2CoolDowns.Daily.value, BucketType.user)
    async def daily(self, ctx, *, daily_type: str = None):
        """(Show today's Dailies)

        Example:
        gw2 daily pve
        gw2 daily pvp
        gw2 daily wvw
        gw2 daily fractals

        """
        if daily_type is not None:
            await GW2Daily.gw2_daily(self, ctx, daily_type)
        else:
            cmd = self.bot.get_command("gw2 daily")
            await bot_utils.send_help_msg(self, ctx, cmd)

    @gw2_group.command()
    @commands.cooldown(1, GW2CoolDowns.ApiKeys.value, BucketType.user)
    async def key(self, ctx, *, cmd_api_key: str = None):
        """(Commands related to GW2 API keys)

        To generate an API key, head to https://account.arena.net, and log in.
        In the "Applications" tab, generate a new key, with all permissions.
        Required API permissions: account

        Example:
        gw2 key add api_key   (Adds a key and associates it with your discord account)
        gw2 key remove        (Removes your GW2 API key from the bot)
        gw2 key info          (Information about your GW2 API keys)
        """

        if cmd_api_key is not None:
            await GW2Key.gw2_key(self, ctx, cmd_api_key)
        else:
            cmd = self.bot.get_command("gw2 key")
            await bot_utils.send_help_msg(self, ctx, cmd)

    @gw2_group.command(name="lastsession")
    @commands.cooldown(1, GW2CoolDowns.LastSession.value, BucketType.user)
    async def last_session(self, ctx):
        await GW2Session.gw2_lastSession(self, ctx)

    @gw2_group.command()
    @commands.cooldown(1, GW2CoolDowns.Wvw.value, BucketType.user)
    async def wvwinfo(self, ctx, *, world: str = None):
        await GW2WvW.gw2_wvwinfo(self, ctx, world)

    @gw2_group.command()
    @commands.cooldown(1, GW2CoolDowns.Wvw.value, BucketType.user)
    async def match(self, ctx, *, world: str = None):
        await GW2WvW.gw2_match(self, ctx, world)

    @gw2_group.command()
    @commands.cooldown(1, GW2CoolDowns.Wvw.value, BucketType.user)
    async def kdr(self, ctx, *, world: str = None):
        await GW2WvW.gw2_kdr(self, ctx, world)

    @gw2_group.command()
    @commands.cooldown(1, GW2CoolDowns.Misc.value, BucketType.user)
    async def wiki(self, ctx, *, search: str = None):
        """ (Search the Guild wars 2 wiki)

        Example:
        gw2 wiki name_to_search
        """

        if search is not None:
            await GW2Misc.gw2_wiki(self, ctx, search)
        else:
            cmd = self.bot.get_command("gw2 wiki")
            await bot_utils.send_help_msg(self, ctx, cmd)

    @gw2_group.command()
    @commands.cooldown(1, GW2CoolDowns.Misc.value, BucketType.user)
    async def info(self, ctx, *, skill: str = None):
        """ (Information about a given name/skill/rune)

        Example:
        gw2 info info_to_search
        """

        if skill is not None:
            await GW2Misc.gw2_info(self, ctx, skill)
        else:
            cmd = self.bot.get_command("gw2 info")
            await bot_utils.send_help_msg(self, ctx, cmd)

    @gw2_group.command()
    @commands.cooldown(1, GW2CoolDowns.Misc.value, BucketType.user)
    async def worlds(self, ctx):
        await GW2Misc.gw2_worlds(self, ctx)


async def setup(bot):
    await bot.add_cog(GuildWars2(bot))
