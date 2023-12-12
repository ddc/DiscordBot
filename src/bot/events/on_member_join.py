# -*- coding: utf-8 -*-
from datetime import datetime
import discord
from discord.ext import commands
from src.database.dal.bot.servers_dal import ServersDal
from src.bot.utils import bot_utils


class OnMemberJoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        @self.bot.event
        async def on_member_join(member):
            server_configs_sql = ServersDal(self.bot.db_session, self.bot.log)
            rs = await server_configs_sql.get_server(member.guild.id)
            if rs["msg_on_join"]:
                now = datetime.utcnow()
                embed = discord.Embed(color=discord.Color.green(), description=str(member))
                embed.set_thumbnail(url=member.avatar.url)
                embed.set_author(name="Joined the Server")
                embed.set_footer(text=f"{now.strftime('%c')}")

                if rs["default_text_channel"]:
                    channel_to_send_msg = bot.get_channel(int(rs["default_text_channel"]))
                else:
                    channel_to_send_msg = await bot_utils.get_server_first_public_text_channel(guild)

                if channel_to_send_msg:
                    try:
                        await channel_to_send_msg.send(embed=embed)
                    except discord.HTTPException:
                        await channel_to_send_msg.send(f"{member.name} Joined the Server\n{now.strftime('%c')}")


async def setup(bot):
    await bot.add_cog(OnMemberJoin(bot))
