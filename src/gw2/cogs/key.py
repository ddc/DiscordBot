import discord
from discord.ext import commands
from src.bot.tools import bot_utils, chat_formatting
from src.database.dal.gw2.gw2_key_dal import Gw2KeyDal
from src.gw2.cogs.gw2 import GuildWars2
from src.gw2.constants import gw2_messages
from src.gw2.tools.gw2_client import Gw2Client
from src.gw2.tools.gw2_cooldowns import GW2CoolDowns


class GW2Key(GuildWars2):
    """(Commands related to GW2 API keys)"""

    def __init__(self, bot):
        super().__init__(bot)


@GW2Key.gw2.group()
async def key(ctx):
    """(Commands related to GW2 API keys)
    To generate an API key, head to https://account.arena.net, and log in.
    In the "Applications" tab, generate a new key with all permissions.
    Required API permissions: account
    
    Note: Only one API key per user is supported.
    
        gw2 key add <api_key>       (Adds your first GW2 API key)
        gw2 key update <api_key>    (Updates/replaces your existing API key)
        gw2 key remove              (Removes your GW2 API key from the bot)
        gw2 key info                (Shows information about your GW2 API key)
    """

    await bot_utils.invoke_subcommand(ctx, "gw2 key")


@key.command(name="add")
@commands.cooldown(1, GW2CoolDowns.ApiKeys.seconds, commands.BucketType.user)
async def add(ctx, api_key: str):
    """(Adds your first GW2 API key)
    This command only works if you don't have an existing key.
    Required API permissions: account
        gw2 key add <api_key>
    """

    await bot_utils.delete_message(ctx, warning=True)
    user_id = ctx.message.author.id
    embed_color = ctx.bot.settings["gw2"]["EmbedColor"]

    # checking API Key with gw2 servers
    gw2_api = Gw2Client(ctx.bot)
    is_valid_key = await gw2_api.check_api_key(api_key)
    if not isinstance(is_valid_key, dict):
        return await bot_utils.send_error_msg(ctx, f"{is_valid_key.args[1]}\n`{api_key}`", True)

    key_name = is_valid_key["name"]
    permissions = ",".join(is_valid_key["permissions"])

    try:
        # getting gw2 acc name
        api_req_acc_info = await gw2_api.call_api("account", api_key)
        gw2_acc_name = api_req_acc_info["name"]
        member_server_id = api_req_acc_info["world"]
    except Exception as e:
        await bot_utils.send_error_msg(ctx, e, True)
        return ctx.bot.log.error(ctx, e)

    try:
        # getting gw2 server name
        uri = f"worlds/{member_server_id}"
        api_req_server = await gw2_api.call_api(uri, api_key)
        gw2_server_name = api_req_server["name"]
    except Exception as e:
        await bot_utils.send_error_msg(ctx, e, True)
        ctx.bot.log.error(ctx, e)
        return None

    api_key_args = {
        "user_id": user_id,
        "key_name": key_name,
        "gw2_acc_name": gw2_acc_name,
        "server_name": gw2_server_name,
        "permissions": permissions,
        "api_key": api_key,
    }

    # searching if API key in local database
    gw2_key_dal = Gw2KeyDal(ctx.bot.db_session, ctx.bot.log)
    
    # Check if user already has any API key - ADD command should only work for first-time users
    existing_user_key = await gw2_key_dal.get_api_key_by_user(user_id)
    if existing_user_key:
        error_msg = (
            "❌ **You already have an API key registered.**\n\n"
            f"Current key: `{existing_user_key[0]['name']}` for account `{existing_user_key[0]['gw2_acc_name']}`\n\n"
            "**Options:**\n"
            f"• To update your key: `{ctx.prefix}gw2 key update <new_api_key>`\n"
            f"• To view your current key: `{ctx.prefix}gw2 key info`\n"
            f"• To remove your key first: `{ctx.prefix}gw2 key remove`\n\n"
            "💡 **Tip:** Use `update` command to replace your existing key."
        )
        await bot_utils.send_error_msg(ctx, error_msg, True)
        return None
    
    # Check if this exact API key is already used by someone else
    rs = await gw2_key_dal.get_api_key(api_key)
    if rs:
        await bot_utils.send_error_msg(ctx, gw2_messages.KEY_ALREADY_IN_USE, True)
        return None
    
    # If we get here, user has no existing key and the API key is not in use
    try:
        await gw2_key_dal.insert_api_key(api_key_args)
        msg = gw2_messages.KEY_ADDED_SUCCESSFULLY.format(key_name, gw2_server_name)
        msg += gw2_messages.KEY_MORE_INFO_HELP.format(ctx.prefix)
        await bot_utils.send_msg(ctx, msg, True, embed_color)
        return None
    except Exception as e:
        ctx.bot.log.error(f"Error inserting API key for user {user_id}: {e}")
        error_msg = (
            "❌ **Failed to add API key.**\n\n"
            "This could be due to a database constraint or connection issue. "
            "Please try again later or contact an administrator if the problem persists."
        )
        await bot_utils.send_error_msg(ctx, error_msg, True)
        return None


@key.command(name="update", aliases=["replace"])
@commands.cooldown(1, GW2CoolDowns.ApiKeys.seconds, commands.BucketType.user)
async def update(ctx, api_key: str):
    """(Updates your existing GW2 API key)
    This command only works if you already have a key registered.
    Required API permissions: account
        gw2 key update <new_api_key>
    """

    await bot_utils.delete_message(ctx, warning=True)
    user_id = ctx.message.author.id
    embed_color = ctx.bot.settings["gw2"]["EmbedColor"]

    # Check if user has an existing key - UPDATE command requires existing key
    gw2_key_dal = Gw2KeyDal(ctx.bot.db_session, ctx.bot.log)
    existing_user_key = await gw2_key_dal.get_api_key_by_user(user_id)
    if not existing_user_key:
        error_msg = (
            "❌ **You don't have an API key registered yet.**\n\n"
            "**Options:**\n"
            f"• To add your first key: `{ctx.prefix}gw2 key add <api_key>`\n"
            f"• For more help: `{ctx.prefix}help gw2 key`\n\n"
            "💡 **Tip:** Use `add` command for your first key."
        )
        await bot_utils.send_error_msg(ctx, error_msg, True)
        return None

    # checking API Key with gw2 servers
    gw2_api = Gw2Client(ctx.bot)
    is_valid_key = await gw2_api.check_api_key(api_key)
    if not isinstance(is_valid_key, dict):
        return await bot_utils.send_error_msg(ctx, f"{is_valid_key.args[1]}\n`{api_key}`", True)

    key_name = is_valid_key["name"]
    permissions = ",".join(is_valid_key["permissions"])

    try:
        # getting gw2 acc name
        api_req_acc_info = await gw2_api.call_api("account", api_key)
        gw2_acc_name = api_req_acc_info["name"]
        member_server_id = api_req_acc_info["world"]
    except Exception as e:
        await bot_utils.send_error_msg(ctx, e, True)
        return ctx.bot.log.error(ctx, e)

    try:
        # getting gw2 server name
        uri = f"worlds/{member_server_id}"
        api_req_server = await gw2_api.call_api(uri, api_key)
        gw2_server_name = api_req_server["name"]
    except Exception as e:
        await bot_utils.send_error_msg(ctx, e, True)
        ctx.bot.log.error(ctx, e)
        return None

    api_key_args = {
        "user_id": user_id,
        "key_name": key_name,
        "gw2_acc_name": gw2_acc_name,
        "server_name": gw2_server_name,
        "permissions": permissions,
        "api_key": api_key,
    }

    # Check if this exact API key is already used by someone else
    rs = await gw2_key_dal.get_api_key(api_key)
    if rs and rs[0]["user_id"] != user_id:
        await bot_utils.send_error_msg(ctx, gw2_messages.KEY_ALREADY_IN_USE, True)
        return None

    # Update the existing key
    try:
        await gw2_key_dal.update_api_key(api_key_args)
        old_key_name = existing_user_key[0]['name']
        msg = gw2_messages.KEY_REPLACED_SUCCESSFULLY.format(old_key_name, key_name, gw2_server_name)
        msg += gw2_messages.KEY_MORE_INFO_HELP.format(ctx.prefix)
        await bot_utils.send_msg(ctx, msg, True, embed_color)
        return None
    except Exception as e:
        ctx.bot.log.error(f"Error updating API key for user {user_id}: {e}")
        error_msg = (
            "❌ **Failed to update API key.**\n\n"
            "This could be due to a database constraint or connection issue. "
            "Please try again later or contact an administrator if the problem persists."
        )
        await bot_utils.send_error_msg(ctx, error_msg, True)
        return None


@key.command(name="remove")
@commands.cooldown(1, GW2CoolDowns.ApiKeys.seconds, commands.BucketType.user)
async def remove(ctx):
    """(Removes your GW2 API key from the bot)
    gw2 key remove
    """

    user_id = ctx.message.author.id
    gw2_key_dal = Gw2KeyDal(ctx.bot.db_session, ctx.bot.log)

    rs = await gw2_key_dal.get_api_key_by_user(user_id)
    if not rs:
        msg = gw2_messages.NO_API_KEY.format(ctx.prefix)
        msg += gw2_messages.KEY_ADD_INFO_HELP.format(ctx.prefix)
        msg += gw2_messages.KEY_MORE_INFO_HELP.format(ctx.prefix)
        return await bot_utils.send_error_msg(ctx, msg)
    else:
        color = ctx.bot.settings["gw2"]["EmbedColor"]
        await gw2_key_dal.delete_user_api_key(user_id)
        await bot_utils.send_msg(ctx, gw2_messages.KEY_REMOVED_SUCCESSFULLY, True, color)
        return None


@key.command(name="info", aliases=["list"])
@commands.cooldown(1, GW2CoolDowns.ApiKeys.seconds, commands.BucketType.user)
async def info(ctx):
    """(Shows information about your GW2 API key)
    gw2 key info
    """

    user_id = ctx.message.author.id
    author_icon_url = ctx.message.author.avatar.url
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
    embed.set_footer(icon_url=ctx.bot.user.avatar.url, text=f"{bot_utils.get_current_date_time_str_long()} UTC")
    await bot_utils.send_embed(ctx, embed, dm=True)


async def setup(bot):
    bot.remove_command("gw2")
    await bot.add_cog(GW2Key(bot))
