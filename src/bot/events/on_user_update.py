# -*- coding: utf-8 -*-
from datetime import datetime
import discord
from discord.ext import commands
from src.database.dal.bot.servers_dal import ServersDal
from src.bot.utils import bot_utils


class OnUserUpdate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        @self.bot.event
        async def on_user_update(before, after):
            if (str(before.name) != str(after.name)
                    or str(before.avatar.url) != str(after.avatar.url)
                    or str(before.discriminator) != str(after.discriminator)):

                msg = "Profile Changes:\n\n"
                now = datetime.now()
                color = self.bot.settings["EmbedColor"]
                embed = discord.Embed(color=color)
                embed.set_author(name=after.display_name, icon_url=after.avatar.url)
                embed.set_footer(text=f"{now.strftime('%c')}")

                if str(before.avatar.url) != str(after.avatar.url):
                    embed.set_thumbnail(url=after.avatar.url)
                    embed.add_field(name="New Avatar", value="-->", inline=True)
                    msg += f"New Avatar: \n{after.avatar.url}\n"

                if str(before.name) != str(after.name):
                    if before.name is not None:
                        embed.add_field(name="Previous Name", value=str(before.name))
                    embed.add_field(name="New Name", value=str(after.name))
                    msg += f"New Name: `{after.name}`\n"

                if str(before.discriminator) != str(after.discriminator):
                    if before.name is not None:
                        embed.add_field(name="Previous Discriminator", value=str(before.discriminator))
                    embed.add_field(name="New Discriminator", value=str(after.discriminator))
                    msg += f"New Discriminator: `{after.discriminator}`\n"

                server_configs_sql = ServersDal(self.bot.db_session, self.bot.log)
                for guild in after._state.guilds:
                    if after in guild.members:
                        rs_sc = await server_configs_sql.get_server_by_id(guild.id)
                        if len(rs_sc) > 0 and rs_sc[0]["msg_on_member_update"] == "Y":
                            if len(embed.fields) > 0:
                                channel_to_send_msg = await bot_utils.channel_to_send_msg(bot, guild)
                                if channel_to_send_msg is not None:
                                    try:
                                        await channel_to_send_msg.send(embed=embed)
                                    except discord.HTTPException:
                                        await channel_to_send_msg.send(msg)


async def setup(bot):
    await bot.add_cog(OnUserUpdate(bot))