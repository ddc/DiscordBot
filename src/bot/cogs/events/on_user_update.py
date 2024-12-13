# -*- coding: utf-8 -*-
from discord.ext import commands
from src.bot.tools import bot_utils
from src.database.dal.bot.servers_dal import ServersDal
from src.bot.constants import messages


class OnUserUpdate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        @self.bot.event
        async def on_user_update(before, after):
            """
                Called when a User updates their profile.
                This is called before on_member_update event is triggered
                This is called when one or more of the following things change:
                    avatar
                    username
                    discriminator
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

            if str(before.avatar.url) != str(after.avatar.url):
                embed.set_thumbnail(url=after.avatar.url)
                embed.add_field(name=messages.NEW_AVATAR, value="-->")
                msg += f"{messages.NEW_AVATAR}: \n{after.avatar.url}\n"

            if str(before.name) != str(after.name):
                if before.name is not None:
                    embed.add_field(name=messages.PREVIOUS_NAME, value=str(before.name))
                embed.add_field(name=messages.NEW_NAME, value=str(after.name))
                msg += f"{messages.NEW_NAME}: `{after.name}`\n"

            if str(before.discriminator) != str(after.discriminator):
                if before.name is not None:
                    embed.add_field(name=messages.PREVIOUS_DISCRIMINATOR, value=str(before.discriminator))
                embed.add_field(name=messages.NEW_DISCRIMINATOR, value=str(after.discriminator))
                msg += f"{messages.NEW_DISCRIMINATOR}: `{after.discriminator}`\n"

            if len(embed.fields) > 0:
                servers_dal = ServersDal(bot.db_session, bot.log)
                for guild in after.mutual_guilds:
                    rs = await servers_dal.get_server(guild.id)
                    if rs["msg_on_member_update"]:
                        await bot_utils.send_msg_to_system_channel(self.bot.log, guild, embed, msg)


async def setup(bot):
    await bot.add_cog(OnUserUpdate(bot))
