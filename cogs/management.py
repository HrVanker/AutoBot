import discord
from discord.ext import commands
from discord import app_commands
import json

class ManagementCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Define a command group for management commands
    rules_group = app_commands.Group(name="rules", description="Commands for managing server rules.")

    @rules_group.command(name="sync", description="Update the rules embed from the source message.")
    @app_commands.checks.has_permissions(administrator=True)
    async def sync_rules(self, interaction: discord.Interaction):
        """Fetches embed JSON from a source message and posts/updates it in the rules channel."""
        await interaction.response.defer(ephemeral=True) # Acknowledge command, gives us more time

        # 1. Load configuration
        config = self.bot.config.get("rules_embed", {})
        target_channel_id = int(config.get("target_channel_id", 0))
        source_channel_id = int(config.get("source_channel_id", 0))
        source_message_id = int(config.get("source_message_id", 0))

        if not all([target_channel_id, source_channel_id, source_message_id]):
            await interaction.followup.send("Rules embed configuration is missing from `config.json`.")
            return

        try:
            # 2. Fetch the source message
            source_channel = self.bot.get_channel(source_channel_id)
            if not source_channel:
                await interaction.followup.send(f"Error: Could not find the source channel (ID: {source_channel_id}).")
                return
            
            source_message = await source_channel.fetch_message(source_message_id)

            # 3. Clean and parse the JSON content from the message
            # Removes backticks and 'json' language specifier
            raw_json = source_message.content.strip()
            if raw_json.startswith("```json"):
                raw_json = raw_json[7:-3]
            elif raw_json.startswith("```"):
                raw_json = raw_json[3:-3]
            
            embed_data = json.loads(raw_json)
            rules_embed = discord.Embed.from_dict(embed_data)

        except json.JSONDecodeError:
            await interaction.followup.send("Error: The content of the source message is not valid JSON.")
            return
        except discord.NotFound:
            await interaction.followup.send(f"Error: Could not find the source message (ID: {source_message_id}).")
            return
        except Exception as e:
            await interaction.followup.send(f"An unexpected error occurred while creating the embed: {e}")
            return
            
        # 4. Find the target channel and post or edit the embed
        target_channel = self.bot.get_channel(target_channel_id)
        if not target_channel:
            await interaction.followup.send(f"Error: Could not find the target channel (ID: {target_channel_id}).")
            return
            
        # Search for a message previously sent by the bot to edit it
        bot_message = None
        async for message in target_channel.history(limit=100):
            if message.author == self.bot.user:
                bot_message = message
                break
        
        try:
            if bot_message:
                await bot_message.edit(embed=rules_embed)
                await interaction.followup.send("✅ Rules embed has been successfully updated!")
            else:
                await target_channel.send(embed=rules_embed)
                await interaction.followup.send("✅ Rules embed has been posted for the first time!")
        except discord.Forbidden:
             await interaction.followup.send("Error: I don't have permission to send or edit messages in the target channel.")


# This function is the entry point that discord.py looks for when loading a cog.
async def setup(bot: commands.Bot):
    await bot.add_cog(ManagementCog(bot))