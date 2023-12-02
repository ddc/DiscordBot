# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from src.bot.utils import bot_utils, chat_formatting
from src.bot.utils.checks import Checks
from src.bot.utils.cooldowns import CoolDowns


class Admin(commands.Cog):
    """(Admin commands)"""
    def __init__(self, bot):
        self.bot = bot

    @commands.group(aliases=["mod"])
    @Checks.check_is_admin()
    async def admin(self, ctx):
        """(Admin Commands)

        admin botgame <game>
        admin kick member#1234 reason
        admin ban member#1234 reason
        admin unban member#1234
        admin banlist

        """

        if ctx.invoked_subcommand:
            return ctx.invoked_subcommand
        else:
            if ctx.command is not None:
                cmd = ctx.command
            else:
                cmd = self.bot.get_command("admin")
            await bot_utils.send_help_msg(self, ctx, cmd)

    @admin.command(name="botgame")
    @commands.cooldown(1, CoolDowns.Admin.value, BucketType.user)
    async def botgame(self, ctx, *, game: str):
        """(Change game that bot is playing)

        Example:
        admin botgame <game>
        """

        # bot_utils.delete_channel_message(self, ctx)
        await ctx.message.channel.typing()
        prefix = self.bot.command_prefix[0]
        bot_game_desc = f"{game} | {prefix}help"
        color = self.bot.settings["EmbedOwnerColor"]
        msg = f"```I'm now playing: {game}```"
        await self.bot.change_presence(activity=discord.Game(name=bot_game_desc))

        embed = discord.Embed(color=color)
        embed.set_author(name=self.bot.user.display_name, icon_url=self.bot.user.avatar.url)
        embed.description = f"```I'm now playing: {game}```"
        await bot_utils.send_embed(self, ctx, embed, False, msg)

        if self.bot.settings["BGChangeGame"].lower() == "yes":
            bg_task_warning = (f"Background task that update bot activity is ON\n"
                               f"Activity will change after "
                               f"{self.bot.settings['BGActivityTimer']} secs.")
            embed.description = bg_task_warning
            await bot_utils.send_embed(self, ctx, embed, True, msg)

    @admin.command(name="kick")
    @commands.cooldown(1, CoolDowns.Admin.value, BucketType.user)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        """(Kick member from the server)

        Example:
        admin kick member#1234
        admin kick member#1234 reason
        """

        match member.id:
            case self.bot.owner.id:
                return await bot_utils.send_error_msg(self, ctx, "Bot Owner cannot be kicked.")
            case self.bot.user.id:
                return await bot_utils.send_error_msg(self, ctx, "Bot itself cannot be kicked.")
            case ctx.message.author.id:
                return await bot_utils.send_error_msg(self, ctx, "You cannot kick yourself.")

        if bot_utils.is_server_owner(ctx, member):
            return await bot_utils.send_error_msg(self, ctx, "You cannot kick the Server's Owner.")
        if bot_utils.is_member_admin(member):
            return await bot_utils.send_error_msg(self, ctx, "You cannot kick a Server's Admin.")

        try:
            await ctx.guild.kick(member, reason=reason)
        except discord.Forbidden:
            return await bot_utils.send_error_msg(self, ctx, "You do not have the proper permissions to kick.")
        except discord.HTTPException:
            return await bot_utils.send_error_msg(self, ctx, "Kicking failed.")

        # await bot_utils.delete_channel_message(self, ctx)
        kick_author = str(ctx.author)
        try:  # private msg
            private_msg = "You have been KICKED"
            embed_private = discord.Embed(color=discord.Color.red(), description=private_msg)
            embed_private.add_field(name="Server", value=chat_formatting.inline(ctx.guild), inline=True)
            embed_private.add_field(name="Admin", value=chat_formatting.inline(kick_author), inline=True)
            if reason is not None:
                embed_private.add_field(name="Reason", value=chat_formatting.inline(reason), inline=True)
            await member.send(embed=embed_private)
        except discord.HTTPException:
            pass

        kick_author = bot_utils.get_member_name_by_id(self, ctx, ctx.author.id)
        # channel msg
        if member.nick is not None:
            mem_name = bot_utils.get_member_name_by_id(self, ctx, member.id)
            kicked_member = f"{member}\n({mem_name})"
        else:
            kicked_member = str(member)
        channel_msg = "Has been KICKED from the server"
        embed_channel = discord.Embed(color=discord.Color.red(), description=channel_msg)
        embed_channel.add_field(name="Member", value=chat_formatting.inline(kicked_member), inline=True)
        embed_channel.add_field(name="Admin", value=chat_formatting.inline(kick_author), inline=True)
        if reason is not None:
            embed_channel.add_field(name="Reason", value=chat_formatting.inline(reason), inline=True)

        msg_channel = f"{channel_msg}: {kicked_member}"
        await bot_utils.send_embed(self, ctx, embed_channel, False, msg_channel)

    @admin.command(name="ban")
    @commands.cooldown(1, CoolDowns.Admin.value, BucketType.user)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        """(Ban member from the server)

        Example:
        admin ban member#1234
        admin ban member#1234 reason
        """

        if member.id == self.bot.owner.id:
            await bot_utils.send_error_msg(self, ctx, "The Bot Owner cannot be banned.")
            return
        if member.id == self.bot.user.id:
            await bot_utils.send_error_msg(self, ctx, "The Bot itself cannot be banned.")
            return
        if member.id == ctx.message.author.id:
            await bot_utils.send_error_msg(self, ctx, "You cannot ban yourself.")
            return
        if bot_utils.is_server_owner(ctx, member):
            await bot_utils.send_error_msg(self, ctx, "You cannot ban the Server's Owner.")
            return
        if bot_utils.is_member_admin(member):
            await bot_utils.send_error_msg(self, ctx, "You cannot ban a Server's Admin.")
            return

        try:
            await ctx.guild.ban(member, reason=reason, delete_message_days=7)
        except discord.Forbidden:
            await bot_utils.send_error_msg(self, ctx, "You do not have the proper permissions to ban.")
            return
        except discord.HTTPException:
            await bot_utils.send_error_msg(self, ctx, "Banning failed")
            return

        # await bot_utils.delete_channel_message(self, ctx)
        ban_author = str(ctx.author)
        try:  # private msg
            private_msg = "You have been BANNED"
            embed_private = discord.Embed(color=discord.Color.red(), description=private_msg)
            embed_private.add_field(name="Server", value=chat_formatting.inline(ctx.guild), inline=True)
            embed_private.add_field(name="Admin", value=chat_formatting.inline(ban_author), inline=True)
            if reason is not None:
                embed_private.add_field(name="Reason", value=chat_formatting.inline(reason), inline=True)
            await member.send(embed=embed_private)
        except discord.HTTPException:
            pass

        ban_author = bot_utils.get_member_name_by_id(self, ctx, ctx.author.id)
        # channel msg
        if member.nick is not None:
            mem_name = bot_utils.get_member_name_by_id(self, ctx, member.id)
            banned_member = f"{member}\n({mem_name})"
        else:
            banned_member = str(member)
        channel_msg = "Has been BANNED from the server"
        embed_channel = discord.Embed(color=discord.Color.red(), description=channel_msg)
        embed_channel.add_field(name="Member", value=chat_formatting.inline(banned_member), inline=True)
        embed_channel.add_field(name="Admin", value=chat_formatting.inline(ban_author), inline=True)
        if reason is not None:
            embed_channel.add_field(name="Reason", value=chat_formatting.inline(reason), inline=True)

        msg_channel = f"{channel_msg}: {banned_member}"
        await bot_utils.send_embed(self, ctx, embed_channel, False, msg_channel)

    @admin.command(name="unban")
    @commands.cooldown(1, CoolDowns.Admin.value, BucketType.user)
    async def unban(self, ctx, *, user: discord.User):
        """(Unban user from the server)

        Example:
        admin unban member#1234
        """

        banned_list = await ctx.guild.bans()
        if len(banned_list) > 0:
            for banned_user in banned_list:
                if banned_user.user == user:
                    color = self.bot.settings["EmbedColor"]
                    await ctx.guild.unban(banned_user.user)
                    await bot_utils.send_msg(self, ctx, color, f"User `{user}` is no longer banned.")
                else:
                    await bot_utils.send_error_msg(self, ctx, f"User: `{user}` not found.\n"
                                                          "Please use full user name with numbers: user#1234\n"
                                                          f"Display all banned users: `{ctx.prefix}banlist`")
        else:
            await bot_utils.send_error_msg(self, ctx, "There are no banned users in this server.")

    @admin.command(name="banlist")
    @commands.cooldown(1, CoolDowns.Admin.value, BucketType.user)
    async def banlist(self, ctx):
        """(List all members that have been banned from the server)

        Example:
        admin banlist
        """

        position = 1
        bl_members = []
        bl_reason = []
        banned_list = await ctx.guild.bans()
        if len(banned_list) > 0:
            for banned_user in banned_list:
                bl_members.append(str(position) + ") " + str(banned_user.user))
                bl_reason.append(str(banned_user.reason))
                position += 1

            members = '\n'.join(bl_members)
            reason = '\n'.join(bl_reason)

            color = self.bot.settings["EmbedColor"]
            embed = discord.Embed(color=color)
            embed.set_author(name="All banned members:\n\n")
            embed.add_field(name="Member", value=chat_formatting.inline(members), inline=True)
            embed.add_field(name="Reason", value=chat_formatting.inline(f"({reason})"), inline=True)

            await bot_utils.send_embed(self, ctx, embed, False)
        else:
            await bot_utils.send_info_msg(self, ctx, "No banned users in this server.")


async def setup(bot):
    bot.remove_command("admin")
    await bot.add_cog(Admin(bot))
