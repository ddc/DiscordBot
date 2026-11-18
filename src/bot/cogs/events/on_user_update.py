from discord.ext import commands
from src.bot.constants import messages
from src.bot.tools import bot_utils
from src.database.dal.bot.servers_dal import ServersDal


class OnUserUpdate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
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

        msg = f"{messages.MemberUpdate.PROFILE_CHANGES}:\n\n"
        embed = bot_utils.get_embed(self)
        embed.set_author(name=after.display_name, icon_url=after.display_avatar.url)
        embed.set_footer(
            icon_url=self.bot.user.display_avatar.url,
            text=f"{bot_utils.get_current_date_time_str_long()} UTC",
        )

        msg += self._add_avatar_change(embed, before, after)
        msg += self._add_name_change(embed, before, after)
        msg += self._add_discriminator_change(embed, before, after)

        if len(embed.fields) > 0:
            servers_dal = ServersDal(self.bot.db_session, self.bot.log)
            for guild in after.mutual_guilds:
                rs = await servers_dal.get_server(guild.id)
                if rs["msg_on_member_update"]:
                    await bot_utils.send_msg_to_system_channel(self.bot.log, guild, embed, msg)

    @staticmethod
    def _add_avatar_change(embed, before, after) -> str:
        if before.avatar == after.avatar:
            return ""
        if after.avatar:
            embed.set_thumbnail(url=after.avatar.url)
        embed.add_field(name=messages.UserUpdate.NEW_AVATAR, value="-->")
        return f"{messages.UserUpdate.NEW_AVATAR}: \n{after.display_avatar.url}\n"

    @staticmethod
    def _add_name_change(embed, before, after) -> str:
        if str(before.name) == str(after.name):
            return ""
        if before.name is not None:
            embed.add_field(name=messages.GuildUpdate.PREVIOUS_NAME, value=str(before.name))
        embed.add_field(name=messages.UserUpdate.NEW_NAME, value=str(after.name))
        return f"{messages.UserUpdate.NEW_NAME}: `{after.name}`\n"

    @staticmethod
    def _add_discriminator_change(embed, before, after) -> str:
        if str(before.discriminator) == str(after.discriminator):
            return ""
        if before.name is not None:
            embed.add_field(name=messages.UserUpdate.PREVIOUS_DISCRIMINATOR, value=str(before.discriminator))
        embed.add_field(name=messages.UserUpdate.NEW_DISCRIMINATOR, value=str(after.discriminator))
        return f"{messages.UserUpdate.NEW_DISCRIMINATOR}: `{after.discriminator}`\n"


async def setup(bot):
    await bot.add_cog(OnUserUpdate(bot))
