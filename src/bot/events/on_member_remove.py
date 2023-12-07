# -*- coding: utf-8 -*-
from datetime import datetime
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
            if len(rs) > 0 and rs[0]["msg_on_leave"]:
                now = datetime.now()
                embed = discord.Embed(color=discord.Color.red(), description=str(member))
                embed.set_thumbnail(url=member.avatar.url)
                embed.set_author(name="Left the Server")
                embed.set_footer(text=f"{now.strftime('%c')}")
                channel_to_send_msg = await bot_utils.channel_to_send_msg(self.bot, member.guild)
                if channel_to_send_msg is not None:
                    try:
                        await channel_to_send_msg.send(embed=embed)
                    except discord.HTTPException:
                        await channel_to_send_msg.send(
                            f"{member.name} Left the Server\n{now.strftime('%c')}"
                        )


async def setup(bot):
    await bot.add_cog(OnMemberRemove(bot))
