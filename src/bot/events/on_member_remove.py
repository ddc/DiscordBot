# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from src.database.dal.bot.servers_dal import ServersDal
from src.bot.utils import bot_utils


class OnMemberRemove(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        @self.bot.event
        async def on_member_remove(member):
            if bot.user.id == member.id:
                return

            server_configs_sql = ServersDal(self.bot.db_session, self.bot.log)
            rs = await server_configs_sql.get_server(member.guild.id)
            if rs["msg_on_leave"]:
                now = bot_utils.get_current_date_time_str()
                embed = discord.Embed(color=discord.Color.red(), description=str(member))
                embed.set_thumbnail(url=member.avatar.url)
                embed.set_author(name="Left the Server")
                embed.set_footer(icon_url=self.bot.user.avatar.url, text=f"{now} UTC")
                msg = f"{member.name} Left the Server\n{now}"
                await bot_utils.send_msg_to_system_channel(self.bot.log, member.guild, embed, msg)


async def setup(bot):
    await bot.add_cog(OnMemberRemove(bot))
