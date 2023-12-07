# -*- coding: utf-8 -*-
from datetime import datetime
import discord
from discord.ext import commands
from src.database.dal.bot.servers_dal import ServersDal
from src.bot.utils import bot_utils
from src.gw2.utils import gw2_utils


class OnMemberUpdate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        @self.bot.event
        async def on_member_update(before, after):
            # do nothing if its a bot OR do nothing if status changed
            if after.bot or (str(before.status) != str(after.status)):
                return

            # check for gw2 game activity
            await gw2_utils.gw2_event_session(bot, before, after)

            msg = "Profile Changes:\n\n"
            color = self.bot.settings["EmbedColor"]
            embed = discord.Embed(color=color)
            embed.set_author(name=after.display_name, icon_url=after.avatar.url)
            embed.set_footer(text=f"{datetime.utcnow().strftime('%c')}")

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

            if str(before.nick) != str(after.nick):
                if before.nick is not None:
                    embed.add_field(name="Previous Nickname", value=str(before.nick))
                embed.add_field(name="New Nickname", value=str(after.nick))
                msg += f"New Nickname: `{after.nick}`\n"

            if len(embed.fields) > 0:
                server_configs_sql = ServersDal(self.bot.db_session, self.bot.log)
                rs_sc = await server_configs_sql.get_server(after.guild.id)
                if len(rs_sc) > 0 and rs_sc[0]["msg_on_member_update"]:
                    channel_to_send_msg = await bot_utils.channel_to_send_msg(self.bot, after.guild)
                    if channel_to_send_msg is not None:
                        try:
                            await channel_to_send_msg.send(embed=embed)
                        except discord.HTTPException:
                            await channel_to_send_msg.send(msg)


async def setup(bot):
    await bot.add_cog(OnMemberUpdate(bot))
