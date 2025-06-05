# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from openai import OpenAI
from src.bot.constants.settings import BotSettings
from src.bot.tools import bot_utils
from src.bot.tools.cooldowns import CoolDowns


class OpenAi(commands.Cog):
    """(OpenAI commands)"""

    def __init__(self, bot):
        self.bot = bot


    @commands.command()
    @commands.cooldown(1, CoolDowns.OpenAI.value, BucketType.user)
    async def ai(self, ctx, *, msg_text: str):
        """(Asks openAI)"""

        await ctx.message.channel.typing()
        try:
            client = OpenAI()
            model = BotSettings().openai_model
            response = client.responses.create(
                model=model,
                input=msg_text
            )
            color = discord.Color.red()
            embed = discord.Embed(color=color, description=response.output_text)
        except Exception as e:
            color = discord.Color.red()
            embed = discord.Embed(color=color, description=e)

        embed.set_author(name=ctx.message.author.display_name, icon_url=ctx.message.author.avatar.url)
        embed.set_footer(
            icon_url=ctx.bot.user.avatar.url,
            text=f"{bot_utils.get_current_date_time_str_long()} UTC"
        )
        await bot_utils.send_embed(ctx, embed, False)


async def setup(bot):
    await bot.add_cog(OpenAi(bot))
