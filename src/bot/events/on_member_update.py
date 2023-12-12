# -*- coding: utf-8 -*-
from datetime import datetime
import discord
from discord.ext import commands
from src.database.dal.bot.servers_dal import ServersDal
from src.bot.utils import bot_utils


class OnMemberUpdate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        @self.bot.event
        async def on_member_update(before, after):
            """
                Called when a Member updates their profile.
                This is called when one or more of the following things change:
                    nickname
                    roles
                    pending
                    flags
            """
            if after.bot:
                return

            msg = "Profile Changes:\n\n"
            embed = bot_utils.get_embed(self)
            embed.set_author(name=after.display_name, icon_url=after.avatar.url)
            embed.set_footer(text=f"{datetime.utcnow().strftime('%c')}")

            if before.nick != after.nick:
                if before.nick is not None:
                    embed.add_field(name="Previous Nickname", value=str(before.nick))
                embed.add_field(name="New Nickname", value=str(after.nick))
                msg += f"New Nickname: `{after.nick}`\n"

            if before.roles != after.roles:
                if before.roles is not None:
                    embed.add_field(name="Previous Roles", value=", ".join([role.name for role in before.roles]))
                embed.add_field(name="New Roles", value=", ".join([role.name for role in after.roles]))
                msg += f"New Roles: `{', '.join([role.name for role in after.roles])}`\n"

            if len(embed.fields) > 0:
                server_configs_sql = ServersDal(self.bot.db_session, self.bot.log)
                rs = await server_configs_sql.get_server(after.guild.id)
                if rs["msg_on_member_update"]:
                    if rs["default_text_channel"]:
                        channel_to_send_msg = bot.get_channel(int(rs["default_text_channel"]))
                    else:
                        channel_to_send_msg = await bot_utils.get_server_first_public_text_channel(after)

                    if channel_to_send_msg:
                        try:
                            await channel_to_send_msg.send(embed=embed)
                        except discord.HTTPException as e:
                            self.bot.logger.error(e)
                            await channel_to_send_msg.send(msg)


async def setup(bot):
    await bot.add_cog(OnMemberUpdate(bot))
