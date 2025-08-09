import discord
from datetime import datetime

async def log_action(bot, title: str, target_user: discord.Member, responsible_party: str, details: str):
    """
    Sends a formatted embed log to the designated log channel.
    
    Args:
        bot: The bot instance to access config and channels.
        title: The title of the embed (e.g., "Manual Role Added").
        target_user: The user who was affected.
        responsible_party: Who performed the action ("System" or a moderator's name).
        details: Specifics of the action (e.g., "Role added: Member").
    """
    log_channel_id = bot.config["log_channel_id"]
    log_channel = bot.get_channel(int(log_channel_id))
    
    if not log_channel:
        print(f"Error: Log channel with ID {log_channel_id} not found.")
        return

    embed = discord.Embed(
        title=title,
        color=discord.Color.blue(),
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="Target User", value=f"{target_user.mention} (`{target_user.id}`)", inline=False)
    embed.add_field(name="Responsible Party", value=responsible_party, inline=False)
    embed.add_field(name="Details", value=details, inline=False)
    embed.set_thumbnail(url=target_user.display_avatar.url)

    try:
        await log_channel.send(embed=embed)
    except discord.Forbidden:
        print(f"Error: Bot does not have permission to send messages in channel ID {log_channel_id}.")
    except Exception as e:
        print(f"An unexpected error occurred in log_action: {e}")