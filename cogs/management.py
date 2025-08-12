import discord
from discord.ext import commands
from discord import app_commands
import json

class ManagementCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    rules_group = app_commands.Group(name="rules", description="Commands for managing server rules.")

    @rules_group.command(name="sync", description="Update the rules embed from the source message and clean up old ones.")
    @app_commands.checks.has_permissions(administrator=True)
    async def sync_rules(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        config = self.bot.config.get("rules_embed", {})
        target_channel_id = int(config.get("target_channel_id", 0))
        source_channel_id = int(config.get("source_channel_id", 0))
        source_message_id = int(config.get("source_message_id", 0))

        if not all([target_channel_id, source_channel_id, source_message_id]):
            await interaction.followup.send("Rules embed configuration is missing from `config.json`.")
            return

        try:
            source_channel = self.bot.get_channel(source_channel_id)
            if not source_channel:
                await interaction.followup.send(f"Error: Could not find the source channel (ID: {source_channel_id}).")
                return
            
            source_message = await source_channel.fetch_message(source_message_id)

            raw_json = source_message.content.strip()
            if raw_json.startswith("```json"):
                raw_json = raw_json[7:-3]
            elif raw_json.startswith("```"):
                raw_json = raw_json[3:-3]
            
            embed_data = json.loads(raw_json)

            # --- ✨ NEW: Multi-Embed Logic ✨ ---
            list_of_embeds = []
            # Check if the root of the JSON is a list (for multiple embeds) or a dict (for a single one)
            if isinstance(embed_data, list):
                if len(embed_data) > 10:
                    await interaction.followup.send("Error: Discord only supports up to 10 embeds per message.")
                    return
                # Create an embed from each dictionary in the list
                list_of_embeds = [discord.Embed.from_dict(d) for d in embed_data]
            elif isinstance(embed_data, dict):
                # If it's just a single object, put it in a list to handle it the same way
                list_of_embeds.append(discord.Embed.from_dict(embed_data))
            else:
                await interaction.followup.send("Error: The root of the JSON must be an object `{...}` or an array `[...]`.")
                return

        except json.JSONDecodeError:
            await interaction.followup.send("Error: The content of the source message is not valid JSON.")
            return
        except discord.NotFound:
            await interaction.followup.send(f"Error: Could not find the source message (ID: {source_message_id}).")
            return
        except Exception as e:
            await interaction.followup.send(f"An unexpected error occurred while creating the embed(s): {e}")
            return
            
        target_channel = self.bot.get_channel(target_channel_id)
        if not target_channel:
            await interaction.followup.send(f"Error: Could not find the target channel (ID: {target_channel_id}).")
            return
            
        final_message = None
        
        try:
            bot_message_to_edit = None
            async for message in target_channel.history(limit=100):
                if message.author == self.bot.user:
                    bot_message_to_edit = message
                    break
            
            if bot_message_to_edit:
                # Use embeds= (plural) to send a list of embeds
                await bot_message_to_edit.edit(embeds=list_of_embeds)
                final_message = bot_message_to_edit
                await interaction.followup.send("✅ Rules embeds have been successfully updated!")
            else:
                # Use embeds= (plural) to send a list of embeds
                new_message = await target_channel.send(embeds=list_of_embeds)
                final_message = new_message
                await interaction.followup.send("✅ Rules embeds have been posted for the first time!")
        except discord.Forbidden:
             await interaction.followup.send("Error: I don't have permission to send or edit messages in the target channel.")
             return
        
        if final_message:
            async for message in target_channel.history(limit=100):
                if message.author == self.bot.user and message.id != final_message.id:
                    try:
                        await message.delete()
                    except (discord.Forbidden, discord.NotFound):
                        pass

async def setup(bot: commands.Bot):
    await bot.add_cog(ManagementCog(bot))