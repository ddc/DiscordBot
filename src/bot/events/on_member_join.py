# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from src.database.dal.bot.servers_dal import ServersDal
from src.bot.tools import bot_utils
from src.bot.constants import messages


class OnMemberJoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        @self.bot.event
        async def on_member_join(member):
            server_configs_sql = ServersDal(self.bot.db_session, self.bot.log)
            rs = await server_configs_sql.get_server(member.guild.id)
            if rs["msg_on_join"]:
                now = bot_utils.get_current_date_time_str_long()
                embed = discord.Embed(color=discord.Color.green(), description=str(member))
                embed.set_thumbnail(url=member.avatar.url)
                embed.set_author(name=messages.JOINED_THE_SERVER)
                embed.set_footer(icon_url=self.bot.user.avatar.url, text=f"{now} UTC")
                msg = f"{member.name} {messages.JOINED_THE_SERVER}\n{now}"
                await bot_utils.send_msg_to_system_channel(self.bot.log, member.guild, embed, msg)


async def setup(bot):
    await bot.add_cog(OnMemberJoin(bot))
