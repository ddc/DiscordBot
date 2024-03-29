# -*- coding: utf-8 -*-
from discord.ext import commands
from src.database.dal.bot.servers_dal import ServersDal
from src.bot.tools import bot_utils
from src.bot.constants import messages


class OnGuildUpdate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        @self.bot.event
        async def on_guild_update(before, after):
            msg = f"{messages.NEW_SERVER_SETTINGS}\n"
            embed = bot_utils.get_embed(self)
            embed.set_footer(icon_url=self.bot.user.avatar.url, text=f"{bot_utils.get_current_date_time_str_long()} UTC")

            if str(before.icon.url) != str(after.icon.url):
                embed.set_thumbnail(url=after.icon.url)
                embed.add_field(name=messages.NEW_SERVER_ICON, value="")
                msg += f"{messages.NEW_SERVER_ICON}: \n{after.icon.url}\n"

            if str(before.name) != str(after.name):
                if before.name is not None:
                    embed.add_field(name=messages.PREVIOUS_NAME, value=str(before.name))
                embed.add_field(name=messages.NEW_SERVER_NAME, value=str(after.name))
                msg += f"{messages.NEW_SERVER_NAME}: `{after.name}`\n"

            if str(before.owner_id) != str(after.owner_id):
                embed.set_thumbnail(url=after.icon.url)
                if before.owner_id is not None:
                    embed.add_field(name=messages.PREVIOUS_SERVER_OWNER, value=str(before.owner))
                embed.add_field(name=messages.NEW_SERVER_OWNER, value=str(after.owner))
                msg += f"{messages.NEW_SERVER_OWNER}: `{after.owner}`\n"

            if len(embed.fields) > 0:
                servers_sql = ServersDal(self.bot.db_session, self.bot.log)
                rs = await servers_sql.get_server(after.id)
                if rs["msg_on_server_update"]:
                    await bot_utils.send_msg_to_system_channel(self.bot.log, after, embed, msg)


async def setup(bot):
    await bot.add_cog(OnGuildUpdate(bot))
