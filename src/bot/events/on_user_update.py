# -*- coding: utf-8 -*-
from discord.ext import commands
from src.bot.utils import bot_utils
from src.database.dal.bot.servers_dal import ServersDal


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
            """
            if after.bot:
                return

            msg = "Profile Changes:\n\n"
            embed = bot_utils.get_embed(self)
            embed.set_author(name=after.display_name, icon_url=after.avatar.url)
            embed.set_footer(icon_url=self.bot.user.avatar.url, text=f"{bot_utils.get_current_date_time_str()} UTC")

            if str(before.avatar.url) != str(after.avatar.url):
                embed.set_thumbnail(url=after.avatar.url)
                embed.add_field(name="New Avatar", value="-->")
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

            if len(embed.fields) > 0:
                servers_dal = ServersDal(bot.db_session, bot.log)
                for guild in after.mutual_guilds:
                    rs = await servers_dal.get_server(guild.id)
                    if rs["msg_on_member_update"]:
                        await bot_utils.send_msg_to_system_channel(self.bot.log, guild, embed, msg)


async def setup(bot):
    await bot.add_cog(OnUserUpdate(bot))
