# -*- coding: utf-8 -*-
from discord.ext import commands
from src.database.dal.bot.servers_dal import ServersDal
from src.bot.tools import bot_utils
from src.bot.constants import messages


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
                :param before: discord.Member
                :param after: discord.Member
                :return: None
            """
            if after.bot:
                return

            msg = f"{messages.PROFILE_CHANGES}:\n\n"
            embed = bot_utils.get_embed(self)
            embed.set_author(name=after.display_name, icon_url=after.avatar.url)
            embed.set_footer(icon_url=self.bot.user.avatar.url, text=f"{bot_utils.get_current_date_time_str_long()} UTC")

            if before.nick != after.nick:
                if before.nick is not None:
                    embed.add_field(name=messages.PREVIOUS_NICKNAME, value=str(before.nick))
                embed.add_field(name=messages.NEW_NICKNAME, value=str(after.nick))
                msg += f"{messages.NEW_NICKNAME}: `{after.nick}`\n"

            if before.roles != after.roles:
                if before.roles is not None:
                    embed.add_field(name=messages.PREVIOUS_ROLES, value=", ".join([role.name for role in before.roles]))
                embed.add_field(name=messages.NEW_ROLES, value=", ".join([role.name for role in after.roles]))
                msg += f"{messages.NEW_ROLES}: `{', '.join([role.name for role in after.roles])}`\n"

            if len(embed.fields) > 0:
                server_configs_sql = ServersDal(self.bot.db_session, self.bot.log)
                rs = await server_configs_sql.get_server(after.guild.id)
                if rs["msg_on_member_update"]:
                    await bot_utils.send_msg_to_system_channel(self.bot.log, after, embed, msg)


async def setup(bot):
    await bot.add_cog(OnMemberUpdate(bot))
