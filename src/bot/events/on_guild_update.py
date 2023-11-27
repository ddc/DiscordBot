# -*- coding: utf-8 -*-
from datetime import datetime
import discord
from discord.ext import commands
from src.database.dal.bot.servers_dal import ServersDal
from src.bot.utils import bot_utils


class OnGuildUpdate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        @self.bot.event
        async def on_guild_update(before, after):
            author = None
            async for entry in after.audit_logs(limit=1, action=discord.AuditLogAction.guild_update):
                author = entry.user

            servers_sql = ServersDal(self.bot.db_session, self.bot.log)
            await servers_sql.update_server(before, after)

            server_configs_sql = ServersDal(self.bot.db_session, self.bot.log)
            rs = await server_configs_sql.get_server_by_id(after.id)
            if len(rs) > 0 and rs[0]["msg_on_server_update"] == "Y":
                msg = "New Server Settings\n"
                now = datetime.now()
                color = self.bot.settings["EmbedColor"]
                embed = discord.Embed(color=color)
                embed.set_author(name=msg, icon_url=author.avatar.url)
                embed.set_footer(text=f"{now.strftime('%c')}")

                if str(before.name) != str(after.name):
                    if before.name is not None:
                        embed.add_field(name="Previous Name", value=str(before.name))
                    embed.add_field(name="New Name", value=str(after.name))
                    msg += f"New Server Name: `{after.name}`\n"

                if str(before.icon.url) != str(after.icon.url):
                    embed.set_thumbnail(url=after.icon.url)
                    embed.add_field(name="New Server Icon", value="-->", inline=True)
                    msg += f"New Server Icon: \n{after.icon.url}\n"

                if str(before.owner_id) != str(after.owner_id):
                    embed.set_thumbnail(url=after.icon.url)
                    if before.owner_id is not None:
                        embed.add_field(name="Previous Server Owner", value=str(before.owner))
                    embed.add_field(name="New Server Owner", value=str(after.owner), inline=True)
                    msg += f"New Server Owner: `{after.owner}`\n"

                if len(embed.fields) > 0:
                    channel_to_send_msg = await bot_utils.channel_to_send_msg(bot, after)
                    if channel_to_send_msg is not None:
                        try:
                            await channel_to_send_msg.send(embed=embed)
                        except discord.HTTPException:
                            await channel_to_send_msg.send(msg)


async def setup(bot):
    await bot.add_cog(OnGuildUpdate(bot))
