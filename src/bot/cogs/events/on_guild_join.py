# -*- coding: utf-8 -*-
import sys
import discord
from discord.ext import commands
from src.bot.tools import bot_utils
from src.bot.constants import variables, messages


class OnGuildJoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        @self.bot.event
        async def on_guild_join(guild):
            await bot_utils.insert_server(self.bot, guild)
            prefix = self.bot.command_prefix
            games_included = "".join(variables.GAMES_INCLUDED)
            msg = messages.GUILD_JOIN_BOT_MESSAGE.format(
                self.bot.user.name,
                prefix,
                games_included,
                prefix,
                prefix
            )

            bot_webpage_url = variables.BOT_WEBPAGE_URL
            bot_avatar = self.bot.user.avatar.url
            author = self.bot.get_user(self.bot.owner_id)
            python_version = "Python {}.{}.{}".format(*sys.version_info[:3])

            embed = discord.Embed(color=discord.Color.green(), description=msg)
            embed.set_author(name=f"{self.bot.user.name} v{variables.VERSION}", icon_url=bot_avatar, url=bot_webpage_url)
            embed.set_thumbnail(url=bot_avatar)
            embed.set_footer(icon_url=author.avatar.url, text=f"Developed by {str(author)} | {python_version}")

            await bot_utils.send_msg_to_system_channel(self.bot.log, guild, embed, msg)


async def setup(bot):
    await bot.add_cog(OnGuildJoin(bot))
