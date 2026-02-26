import discord
from discord.ext import commands
from src.bot.tools import bot_utils, chat_formatting
from src.database.dal.gw2.gw2_key_dal import Gw2KeyDal
from src.gw2.cogs.gw2 import GuildWars2
from src.gw2.constants import gw2_messages
from src.gw2.tools.gw2_client import Gw2Client
from src.gw2.tools.gw2_cooldowns import GW2CoolDowns


def _get_user_id(ctx_or_interaction):
    if isinstance(ctx_or_interaction, discord.Interaction):
        return ctx_or_interaction.user.id
    return ctx_or_interaction.message.author.id


async def _send_success(ctx_or_interaction, msg, color):
    if isinstance(ctx_or_interaction, discord.Interaction):
        embed = discord.Embed(description=msg, color=color)
        await ctx_or_interaction.followup.send(embed=embed, ephemeral=True)
    else:
        await bot_utils.send_msg(ctx_or_interaction, msg, True, color)


async def _send_error(ctx_or_interaction, msg):
    msg = str(msg)
    if isinstance(ctx_or_interaction, discord.Interaction):
        embed = discord.Embed(
            description=chat_formatting.error(msg),
            color=discord.Color.red(),
        )
        await ctx_or_interaction.followup.send(embed=embed, ephemeral=True)
    else:
        await bot_utils.send_error_msg(ctx_or_interaction, msg, True)


async def _validate_api_key(bot, api_key):
    """Validate API key with GW2 servers and return account info dict."""
    gw2_api = Gw2Client(bot)
    is_valid_key = await gw2_api.check_api_key(api_key)
    if not isinstance(is_valid_key, dict):
        raise ValueError(f"{is_valid_key.message}\n`{api_key}`")

    key_name = is_valid_key["name"]
    permissions = ",".join(is_valid_key["permissions"])

    api_req_acc_info = await gw2_api.call_api("account", api_key)
    gw2_acc_name = api_req_acc_info["name"]
    member_server_id = api_req_acc_info["world"]

    uri = f"worlds/{member_server_id}"
    api_req_server = await gw2_api.call_api(uri, api_key)
    gw2_server_name = api_req_server["name"]

    return {
        "key_name": key_name,
        "permissions": permissions,
        "gw2_acc_name": gw2_acc_name,
        "gw2_server_name": gw2_server_name,
    }


async def _process_add_key(ctx_or_interaction, api_key, bot, prefix):
    """Validate and add a new GW2 API key for the user."""
    user_id = _get_user_id(ctx_or_interaction)
    embed_color = bot.settings["gw2"]["EmbedColor"]

    try:
        key_info = await _validate_api_key(bot, api_key)
    except Exception as e:
        bot.log.error(f"API key validation failed for user {user_id}: {e}")
        return await _send_error(ctx_or_interaction, e)

    gw2_key_dal = Gw2KeyDal(bot.db_session, bot.log)

    existing_user_key = await gw2_key_dal.get_api_key_by_user(user_id)
    if existing_user_key:
        error_msg = (
            f"You already have an API key registered.\n"
            f"Current key: `{existing_user_key[0]['name']}` for account `{existing_user_key[0]['gw2_acc_name']}`\n\n"
            f"To update your key: `{prefix}gw2 key update <new_api_key>`\n"
            f"To view your current key: `{prefix}gw2 key info`\n"
            f"To remove your key first: `{prefix}gw2 key remove`"
        )
        return await _send_error(ctx_or_interaction, error_msg)

    rs = await gw2_key_dal.get_api_key(api_key)
    if rs:
        return await _send_error(ctx_or_interaction, gw2_messages.KEY_ALREADY_IN_USE)

    try:
        await gw2_key_dal.insert_api_key(
            {
                "user_id": user_id,
                "key_name": key_info["key_name"],
                "gw2_acc_name": key_info["gw2_acc_name"],
                "server_name": key_info["gw2_server_name"],
                "permissions": key_info["permissions"],
                "api_key": api_key,
            }
        )
        msg = gw2_messages.key_added_successfully(key_info["key_name"], key_info["gw2_server_name"])
        msg += gw2_messages.key_more_info_help(prefix)
        await _send_success(ctx_or_interaction, msg, embed_color)
    except Exception as e:
        bot.log.error(f"Error inserting API key for user {user_id}: {e}")
        await _send_error(ctx_or_interaction, "Failed to add API key. Please try again later.")


async def _process_update_key(ctx_or_interaction, api_key, bot, prefix):
    """Validate and update an existing GW2 API key for the user."""
    user_id = _get_user_id(ctx_or_interaction)
    embed_color = bot.settings["gw2"]["EmbedColor"]

    gw2_key_dal = Gw2KeyDal(bot.db_session, bot.log)
    existing_user_key = await gw2_key_dal.get_api_key_by_user(user_id)
    if not existing_user_key:
        error_msg = (
            f"You don't have an API key registered yet.\n\n"
            f"To add your first key: `{prefix}gw2 key add <api_key>`\n"
            f"For more help: `{prefix}help gw2 key`"
        )
        return await _send_error(ctx_or_interaction, error_msg)

    try:
        key_info = await _validate_api_key(bot, api_key)
    except Exception as e:
        bot.log.error(f"API key validation failed for user {user_id}: {e}")
        return await _send_error(ctx_or_interaction, e)

    rs = await gw2_key_dal.get_api_key(api_key)
    if rs and rs[0]["user_id"] != user_id:
        return await _send_error(ctx_or_interaction, gw2_messages.KEY_ALREADY_IN_USE)

    try:
        await gw2_key_dal.update_api_key(
            {
                "user_id": user_id,
                "key_name": key_info["key_name"],
                "gw2_acc_name": key_info["gw2_acc_name"],
                "server_name": key_info["gw2_server_name"],
                "permissions": key_info["permissions"],
                "api_key": api_key,
            }
        )
        old_key_name = existing_user_key[0]["name"]
        msg = gw2_messages.key_replaced_successfully(old_key_name, key_info["key_name"], key_info["gw2_server_name"])
        msg += gw2_messages.key_more_info_help(prefix)
        await _send_success(ctx_or_interaction, msg, embed_color)
    except Exception as e:
        bot.log.error(f"Error updating API key for user {user_id}: {e}")
        await _send_error(ctx_or_interaction, "Failed to update API key. Please try again later.")


class ApiKeyModal(discord.ui.Modal, title="Enter GW2 API Key"):
    """Modal dialog for secure API key input."""

    api_key_input = discord.ui.TextInput(
        label="API Key",
        placeholder="Paste your GW2 API key here",
        style=discord.TextStyle.short,
        required=True,
        min_length=10,
    )

    def __init__(self, bot, mode: str, prefix: str):
        super().__init__()
        self.bot = bot
        self.mode = mode
        self.prefix = prefix

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        api_key = self.api_key_input.value.strip()
        if self.mode == "add":
            await _process_add_key(interaction, api_key, self.bot, self.prefix)
        else:
            await _process_update_key(interaction, api_key, self.bot, self.prefix)


class ApiKeyView(discord.ui.View):
    """View with a button that opens the API key modal."""

    def __init__(self, bot, mode: str, prefix: str):
        super().__init__(timeout=300)
        self.bot = bot
        self.mode = mode
        self.prefix = prefix
        self.message = None

    @discord.ui.button(label="Enter API Key", emoji="\U0001f511", style=discord.ButtonStyle.primary)
    async def enter_key(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ApiKeyModal(self.bot, self.mode, self.prefix)
        await interaction.response.send_modal(modal)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            if self.message:
                await self.message.edit(view=self)
        except discord.NotFound, discord.HTTPException:
            pass


class GW2Key(GuildWars2):
    """Guild Wars 2 commands for API key management."""

    def __init__(self, bot):
        super().__init__(bot)


@GW2Key.gw2.group()
async def key(ctx):
    """Manage your Guild Wars 2 API keys.

    To generate an API key, head to https://account.arena.net and log in.
    In the "Applications" tab, generate a new key with all permissions.
    Only one API key per user is supported.

    Available subcommands:
        gw2 key add [api_key] - Add your first GW2 API key
        gw2 key update [api_key] - Update your existing API key
        gw2 key remove - Remove your GW2 API key
        gw2 key info - Show your API key information
    """

    await bot_utils.invoke_subcommand(ctx, "gw2 key")


@key.command(name="add")
@commands.cooldown(1, GW2CoolDowns.ApiKeys.seconds, commands.BucketType.user)
async def add(ctx, api_key: str = None):
    """Add your first Guild Wars 2 API key.

    This command only works if you don't have an existing key.
    If no key is provided, a secure input dialog will be sent to your DM.
    Required API permissions: account

    Usage:
        gw2 key add
        gw2 key add XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
    """

    if api_key is None:
        view = ApiKeyView(ctx.bot, "add", ctx.prefix)
        embed = discord.Embed(
            description=(
                "Click the button below to securely enter your GW2 API key.\n\n"
                "To generate an API key, head to https://account.arena.net\n"
                "In the **Applications** tab, generate a new key with **account** permissions."
            ),
            color=ctx.bot.settings["gw2"]["EmbedColor"],
        )
        message = await ctx.author.send(embed=embed, view=view)
        view.message = message
        if not bot_utils.is_private_message(ctx):
            notification = discord.Embed(
                description="\U0001f4ec Secure API key input sent to your DM",
                color=discord.Color.green(),
            )
            await ctx.send(embed=notification)
        return

    await bot_utils.delete_message(ctx, warning=True)
    await _process_add_key(ctx, api_key, ctx.bot, ctx.prefix)


@key.command(name="update", aliases=["replace"])
@commands.cooldown(1, GW2CoolDowns.ApiKeys.seconds, commands.BucketType.user)
async def update(ctx, api_key: str = None):
    """Update your existing Guild Wars 2 API key.

    This command only works if you already have a key registered.
    If no key is provided, a secure input dialog will be sent to your DM.
    Required API permissions: account

    Usage:
        gw2 key update
        gw2 key update XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
    """

    if api_key is None:
        view = ApiKeyView(ctx.bot, "update", ctx.prefix)
        embed = discord.Embed(
            description=(
                "Click the button below to securely enter your new GW2 API key.\n\n"
                "This will replace your existing API key."
            ),
            color=ctx.bot.settings["gw2"]["EmbedColor"],
        )
        message = await ctx.author.send(embed=embed, view=view)
        view.message = message
        if not bot_utils.is_private_message(ctx):
            notification = discord.Embed(
                description="\U0001f4ec Secure API key input sent to your DM",
                color=discord.Color.green(),
            )
            await ctx.send(embed=notification)
        return

    await bot_utils.delete_message(ctx, warning=True)
    await _process_update_key(ctx, api_key, ctx.bot, ctx.prefix)


@key.command(name="remove")
@commands.cooldown(1, GW2CoolDowns.ApiKeys.seconds, commands.BucketType.user)
async def remove(ctx):
    """Remove your Guild Wars 2 API key from the bot.

    Usage:
        gw2 key remove
    """

    user_id = ctx.message.author.id
    gw2_key_dal = Gw2KeyDal(ctx.bot.db_session, ctx.bot.log)

    rs = await gw2_key_dal.get_api_key_by_user(user_id)
    if not rs:
        msg = gw2_messages.NO_API_KEY
        msg += gw2_messages.key_add_info_help(ctx.prefix)
        msg += gw2_messages.key_more_info_help(ctx.prefix)
        return await bot_utils.send_error_msg(ctx, msg)
    else:
        color = ctx.bot.settings["gw2"]["EmbedColor"]
        await gw2_key_dal.delete_user_api_key(user_id)
        await bot_utils.send_msg(ctx, gw2_messages.KEY_REMOVED_SUCCESSFULLY, True, color)
        return None


@key.command(name="info", aliases=["list"])
@commands.cooldown(1, GW2CoolDowns.ApiKeys.seconds, commands.BucketType.user)
async def info(ctx):
    """Display information about your Guild Wars 2 API key.

    Usage:
        gw2 key info
    """

    user_id = ctx.message.author.id
    author_icon_url = ctx.message.author.display_avatar.url
    color = ctx.bot.settings["gw2"]["EmbedColor"]
    gw2_key_dal = Gw2KeyDal(ctx.bot.db_session, ctx.bot.log)
    gw2_api = Gw2Client(ctx.bot)

    # Get user's API key
    rs = await gw2_key_dal.get_api_key_by_user(user_id)

    if not rs:
        error_msg = (
            "❌ **You don't have an API key registered.**\n\n"
            "**Options:**\n"
            f"• To add your first key: `{ctx.prefix}gw2 key add <api_key>`\n"
            f"• For more help: `{ctx.prefix}help gw2 key`\n\n"
            "💡 **Tip:** You need to add a key before viewing its information."
        )
        await bot_utils.send_error_msg(ctx, error_msg, True)
        return

    try:
        api_key = rs[0]["key"]
        is_valid_key = await gw2_api.check_api_key(api_key)
        if not isinstance(is_valid_key, dict):
            is_valid_key = "NO"
            name = f"***{gw2_messages.INVALID_API_KEY}***"
        else:
            is_valid_key = "YES"
            name = f"{ctx.message.author}"
    except Exception as e:
        await bot_utils.send_error_msg(ctx, e, True)
        ctx.bot.log.error(ctx, e)
        return

    embed = discord.Embed(
        title="Your GW2 Account",
        description=chat_formatting.inline(rs[0]["gw2_acc_name"]),
        color=color,
    )
    embed.set_author(name=name, icon_url=author_icon_url)
    embed.add_field(name="Server", value=chat_formatting.inline(rs[0]["server"]))
    embed.add_field(name="Key Name", value=chat_formatting.inline(rs[0]["name"]))
    embed.add_field(name="Valid", value=chat_formatting.inline(is_valid_key))
    embed.add_field(
        name="Permissions",
        value=chat_formatting.inline(rs[0]["permissions"].replace(",", "|")),
        inline=False,
    )
    embed.add_field(name="Key", value=chat_formatting.inline(rs[0]["key"]), inline=False)
    embed.set_footer(icon_url=ctx.bot.user.display_avatar.url, text=f"{bot_utils.get_current_date_time_str_long()} UTC")
    await bot_utils.send_embed(ctx, embed, dm=True)


async def setup(bot):
    bot.remove_command("gw2")
    await bot.add_cog(GW2Key(bot))
