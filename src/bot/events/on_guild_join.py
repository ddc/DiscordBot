# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from src.bot.utils import bot_utils, constants
from src.database.dal.bot.bot_configs_dal import BotConfigsDal


class OnGuildJoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        @self.bot.event
        async def on_guild_join(guild):
            await bot_utils.insert_default_initial_configs(self.bot, guild)
            bot_configs_sql = BotConfigsDal(self.bot.db_session, self.bot.logs)
            configs = await bot_configs_sql.get_bot_configs()
            prefix = configs[0]["prefix"]
            games_included = None

            if constants.GAMES_INCLUDED is not None:
                if len(constants.GAMES_INCLUDED) == 1:
                    games_included = constants.GAMES_INCLUDED[0]
                elif len(constants.GAMES_INCLUDED) > 1:
                    games_included = ""
                    for games in constants.GAMES_INCLUDED:
                        games_included += f"({games}) "
            msg = (f"Thanks for using *{self.bot.user.name}*\n"
                   f"To learn more about this bot: `{prefix}about`\n"
                   f"Games included so far: `{games_included}`\n\n")

            for rol in guild.me.roles:
                if rol.permissions.value == 8:
                    msg += ("Bot is running in \"Admin\" mode\n"
                            "A \"bot-commands\" channel were created for bot commands\n")

            msg += (f"If you are an Admin and wish to list configurations: `{prefix}config list`\n"
                    f"To get a list of commands: `{prefix}help`")
            embed = discord.Embed(color=discord.Color.green(), description=msg)
            embed.set_author(name=guild.me.display_name, icon_url=guild.me.avatar.url)
            channel_to_send_msg = await bot_utils.channel_to_send_msg(self.bot, guild)
            if channel_to_send_msg is not None:
                try:
                    await channel_to_send_msg.send(embed=embed)
                except discord.HTTPException:
                    await channel_to_send_msg.send(msg)
            await bot_utils.create_admin_commands_channel(self.bot, guild)


async def setup(bot):
    await bot.add_cog(OnGuildJoin(bot))
