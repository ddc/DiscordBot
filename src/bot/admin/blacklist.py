# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from src.database.dal.bot.blacklist_dal import BlacklistDal
from src.database.dal.bot.servers_dal import ServersDal
from src.bot.utils import bot_utils, chat_formatting
from src.bot.utils.cooldowns import CoolDowns
from src.bot.admin.admin import Admin


class Blacklist(Admin):
    """(Admin blacklist commands)"""
    def __init__(self, bot):
        super().__init__(bot)


@Blacklist.admin.group(aliases=["bl"])
async def blacklist(self, ctx):
    """(Add, remove, list users from the blacklist)

    Blacklisted users cannot use any bot commands.

    admin blacklist or admin bl

    Example:
    admin blacklist add member#1234
    admin blacklist remove member#1234
    asmin blacklist removeall
    admin blacklist list
    """

    if ctx.invoked_subcommand:
        return ctx.invoked_subcommand
    else:
        if ctx.command is not None:
            cmd = ctx.command
        else:
            cmd = self.bot.get_command("admin blacklist")
        await bot_utils.send_help_msg(self, ctx, cmd)


@blacklist.command(name="add")
@commands.cooldown(1, CoolDowns.Blacklist.value, BucketType.user)
async def blacklist_add(self, ctx, member: discord.Member, *, reason=None):
    """(Add user to blacklist)

    Example:
    blacklist add member#1234 reason
    """

    if member.id == self.bot.owner.id:
        await bot_utils.send_error_msg(self, ctx, "The Bot Owner cannot be blacklisted.")
        return
    if member.id == self.bot.user.id:
        await bot_utils.send_error_msg(self, ctx, "The Bot itself cannot be blacklisted.")
        return
    if member.id == ctx.message.author.id:
        await bot_utils.send_error_msg(self, ctx, "You cannot blacklist yourself.")
        return
    if bot_utils.is_server_owner(ctx, member):
        await bot_utils.send_error_msg(self, ctx, "You cannot blacklist the Server's Owner.")
        return

    server_configs_dal = ServersDal(self.bot.db_session, self.bot.log)
    rs = await server_configs_dal.get_server_by_id(ctx.guild.id)
    if bot_utils.is_member_admin(member) and rs[0]["blacklist_admins"] == 'N':
        await bot_utils.send_error_msg(self, ctx, "You cannot blacklist a Server's Admin.")
        return

    if reason is not None and len(reason) > 29:
        await bot_utils.send_error_msg(self, ctx, "Reason has too many characters.")
        return

    blacklist_dal = BlacklistDal(self.bot.db_session, self.bot.log)
    rs = await blacklist_dal.get_server_blacklisted_user(member)
    if len(rs) == 0:
        await blacklist_dal.insert_blacklisted_user(member, ctx.message.author, reason)
        msg = f"Successfully added {member} to the blacklist.\n" \
              "Cannot execute any Bot commands anymore."
        if reason is not None:
            msg += f"\nReason: {reason}"
        color = self.bot.settings["EmbedColor"]
        await bot_utils.send_msg(self, ctx, color, chat_formatting.inline(msg))
    else:
        msg = f"{member} is already blacklisted."
        if rs[0]["reason"] is not None:
            msg += f"\nReason: {reason}"
        await bot_utils.send_error_msg(self, ctx, msg)


@blacklist.command(name="remove")
@commands.cooldown(1, CoolDowns.Blacklist.value, BucketType.user)
async def blacklist_remove_user(self, ctx, *, member: discord.Member):
    """(Remove blacklisted user)

    Example:
    blacklist remove member#1234
    """

    if member is not None:
        blacklist_dal = BlacklistDal(self.bot.db_session, self.bot.log)
        rs = await blacklist_dal.get_server_blacklisted_user(member)
        if len(rs) > 0:
            await blacklist_dal.delete_blacklisted_user(member)
            msg = f"Successfully removed {member} from the blacklist."
            color = self.bot.settings["EmbedColor"]
            await bot_utils.send_msg(self, ctx, color, chat_formatting.inline(msg))
            await ctx.send(f"{member.mention}")
        else:
            msg = f"{member} is not blacklisted."
            await bot_utils.send_error_msg(self, ctx, msg)
    else:
        msg = f"Member {member} not found"
        await bot_utils.send_error_msg(self, ctx, msg)


@blacklist.command(name="removeall")
@commands.cooldown(1, CoolDowns.Blacklist.value, BucketType.user)
async def blacklist_remove_all_users(self, ctx):
    """(Remove all blacklisted users)

    Example:
    blacklist removeall
    """

    blacklist_dal = BlacklistDal(self.bot.db_session, self.bot.log)
    rs = await blacklist_dal.get_all_server_blacklisted_users(ctx.guild.id)
    if len(rs) > 0:
        color = self.bot.settings["EmbedColor"]
        await blacklist_dal.delete_all_server_blacklisted_users(ctx.guild.id)
        await bot_utils.send_msg(self, ctx, color, "Successfully removed all members from the blacklist.")
    else:
        await bot_utils.send_error_msg(self, ctx, "There are no blacklisted members in this server.")


@blacklist.command(name="list")
@commands.cooldown(1, CoolDowns.Blacklist.value, BucketType.user)
async def blacklist_list(self, ctx):
    """(List all blacklisted users)

    Example:
    blacklist list
    """

    bl_members = []
    bl_reason = []
    bl_author = []
    position = 1

    blacklist_dal = BlacklistDal(self.bot.db_session, self.bot.log)
    rs = await blacklist_dal.get_all_server_blacklisted_users(ctx.guild.id)
    if len(rs) > 0:
        for key, value in rs.items():
            member_name = f"{ctx.guild.get_member(value['user_id'])}"
            author_name = bot_utils.get_member_name_by_id(self, ctx, value["discord_author_id"])
            bl_author.append(author_name)
            bl_members.append(f"{position}) {member_name}")
            if value["reason"] is None:
                bl_reason.append("---")
            else:
                bl_reason.append(value["reason"])
            position += 1

        members = '\n'.join(bl_members)
        reason = '\n'.join(bl_reason)
        author = '\n'.join(bl_author)

        embed = discord.Embed(description="*`Members that cannot execute any bot commands`*",
                              color=discord.Color.red())
        embed.set_footer(text=f"For more info: {ctx.prefix}help blacklist")
        embed.set_author(name="Blalcklisted members in this server:\n\n", icon_url=f"{ctx.guild.icon.url}")
        embed.add_field(name="Member", value=chat_formatting.inline(members), inline=True)
        embed.add_field(name="Added by", value=chat_formatting.inline(author), inline=True)
        embed.add_field(name="Reason", value=chat_formatting.inline(reason), inline=True)

        await bot_utils.send_embed(self, ctx, embed, False)
    else:
        await bot_utils.send_error_msg(self, ctx, "There are no blacklisted members in this server.")


async def setup(bot):
    bot.remove_command('admin')
    await bot.add_cog(Blacklist(bot))
