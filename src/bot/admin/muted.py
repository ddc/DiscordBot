# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from src.database.dal.bot.muted_dal import MutedDal
from src.database.dal.bot.servers_dal import ServersDal
from src.bot.utils import bot_utils, chat_formatting
from src.bot.utils.cooldowns import CoolDowns
from src.bot.admin.admin import Admin


class Muted(Admin):
    """(Admin mute commands)"""
    def __init__(self, bot):
        super().__init__(bot)


@Muted.admin.group()
async def mute(self, ctx):
    """(Add, remove, list mute users)

    Muted members cannot type anything.
    They will be noticed with a direct message from bot.

    mute

    Example:
    mute add member#1234 reason
    mute remove member#1234
    mute list
    """

    if ctx.invoked_subcommand:
        return ctx.invoked_subcommand
    else:
        if ctx.command is not None:
            cmd = ctx.command
        else:
            cmd = self.bot.get_command("mute")
        await bot_utils.send_help_msg(self, ctx, cmd)

    # # check if bot has perms (manage messages)
    # if ctx.message.guild.me.guild_permissions.manage_messages:
    #     ctx.invoked_subcommand
    # else:
    #     msg = "Bot does not have permission to delete messages.\n" \
    #           "Missing permission: \"Manage Messages\"`"
    #     embed = discord.Embed(title="", color=discord.Color.red(), description=msg)
    #     try:
    #         await ctx.channel.send(embed=embed)
    #     except discord.HTTPException:
    #         await ctx.channel.send(f"{msg}")
    #     return

@mute.command(name="add")
@commands.cooldown(1, CoolDowns.Mute.value, BucketType.user)
async def mute_add(self, ctx, member: discord.Member, *, reason=None):
    """(Mute an user)

    Example:
    mute add member#1234 reason
    """

    if member.id == self.bot.owner.id:
        await bot_utils.send_error_msg(self, ctx, "The Bot Owner cannot be muted.")
        return
    if member.id == self.bot.user.id:
        await bot_utils.send_error_msg(self, ctx, "The Bot itself cannot be muted.")
        return
    if member.id == ctx.message.author.id:
        await bot_utils.send_error_msg(self, ctx, "You cannot mute yourself.")
        return
    if bot_utils.is_server_owner(ctx, member):
        await bot_utils.send_error_msg(self, ctx, "You cannot mute the Server's Owner.")
        return

    server_configs_dal = ServersDal(self.bot.db_session, self.bot.log)
    rs = await server_configs_dal.get_server_by_id(ctx.guild.id)
    if bot_utils.is_member_admin(member) and rs[0]["mute_admins"] == 'N':
        await bot_utils.send_error_msg(self, ctx, "You cannot mute a Server's Admin.")
        return

    if reason is not None and len(reason) > 29:
        await bot_utils.send_error_msg(self, ctx, "Reason has too many characters.")
        return

    muted_dal = MutedDal(self.bot.db_session, self.bot.log)
    rs = await muted_dal.get_server_mute_user(member)
    if len(rs) == 0:
        await muted_dal.insert_mute_user(member, ctx.message.author, reason)
        msg = f"Successfully muted {member}"
        color = self.bot.settings["EmbedColor"]
        if reason is not None:
            msg += f"\nReason: {reason}"
        await bot_utils.send_msg(self, ctx, color, chat_formatting.inline(msg))
    else:
        msg = f"{member} is already muted."
        if rs[0]["reason"] is not None:
            msg += f"\nReason: {reason}"
        await bot_utils.send_error_msg(self, ctx, msg)

@mute.command(name="remove")
@commands.cooldown(1, CoolDowns.Mute.value, BucketType.user)
async def mute_remove_user(self, ctx, *, member: discord.Member):
    """(Remove muted user)

    Example:
    mute remove member#1234
    """

    if member is not None:
        muted_dal = MutedDal(self.bot.db_session, self.bot.log)
        rs = await muted_dal.get_server_mute_user(member)
        if len(rs) > 0:
            msg = f"Successfully unmuted {member}."
            color = self.bot.settings["EmbedColor"]
            await muted_dal.delete_mute_user(member)
            await bot_utils.send_msg(self, ctx, color, chat_formatting.inline(msg))
            await ctx.send(f"{member.mention}")
        else:
            msg = f"{member} is not muted."
            await bot_utils.send_error_msg(self, ctx, msg)
    else:
        msg = f"Member {member} not found"
        await bot_utils.send_error_msg(self, ctx, msg)

@mute.command(name="removeall")
@commands.cooldown(1, CoolDowns.Mute.value, BucketType.user)
async def mute_remove_all_users(self, ctx):
    """(Remove all muted users)

    Example:
    mute removeall
    """

    muted_dal = MutedDal(self.bot.db_session, self.bot.log)
    rs = await muted_dal.get_all_server_mute_users(ctx.guild.id)
    if len(rs) > 0:
        color = self.bot.settings["EmbedColor"]
        await muted_dal.delete_all_mute_users(ctx.guild.id)
        await bot_utils.send_msg(self, ctx, color, "Successfully unmuted all members.")
    else:
        await bot_utils.send_error_msg(self, ctx, "There are no muted members in this server.")

@mute.command(name="list")
@commands.cooldown(1, CoolDowns.Mute.value, BucketType.user)
async def mute_list(self, ctx):
    """(List all muted users)

    Example:
    mute list
    """

    bl_members = []
    bl_reason = []
    bl_author = []
    position = 1

    muted_dal = MutedDal(self.bot.db_session, self.bot.log)
    rs = await muted_dal.get_all_server_mute_users(ctx.guild.id)
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

        embed = discord.Embed(description="*`Members that cannot type anything`*", color=discord.Color.red())
        embed.set_footer(text=f"For more info: {ctx.prefix}help mute")
        embed.set_author(name="Muted members in this server:\n\n", icon_url=f"{ctx.guild.icon.url}")
        embed.add_field(name="Member", value=chat_formatting.inline(members), inline=True)
        embed.add_field(name="Added by", value=chat_formatting.inline(author), inline=True)
        embed.add_field(name="Reason", value=chat_formatting.inline(reason), inline=True)

        await bot_utils.send_embed(self, ctx, embed, False)
    else:
        await bot_utils.send_error_msg(self, ctx, "There are no muted members in this server.")


async def setup(bot):
    bot.remove_command("admin")
    await bot.add_cog(Muted(bot))
