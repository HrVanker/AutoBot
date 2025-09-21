import discord
from discord.ext import commands
#import json
import yaml
import asyncio

class ManagementCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        This listener watches for a 'rules.yaml' file upload in the source channel
        and automatically updates the rules embed.
        """
        # Ignore messages from bots (including ourself)
        if message.author.bot:
            return

        # Load configuration and check if the message is in the correct channel
        config = self.bot.config.get("rules_embed", {})
        source_channel_id = int(config.get("source_channel_id", 0))
        target_channel_id = int(config.get("target_channel_id", 0))

        if not message.channel.id == source_channel_id:
            return

        # Check if the message has an attachment named 'rules.yaml'
        rules_attachment = None
        for attachment in message.attachments:
            if attachment.filename == "rules.yaml":
                rules_attachment = attachment
                break
        
        # If no matching attachment is found, do nothing
        if not rules_attachment:
            return
        
        # Add a reaction to show the bot is processing the file
        await message.add_reaction("⚙️")

        try:
            # Read the file content and parse the YAML
            yaml_bytes = await rules_attachment.read()
            yaml_string = yaml_bytes.decode('utf-8')
            embed_data = yaml.safe_load(yaml_string) 
            #yaml.safe_loads(yaml_string)
            
            embed_dicts = embed_data if isinstance(embed_data, list) else [embed_data]

            # Convert hex color codes to integers
            for embed_dict in embed_dicts:
                if 'color' in embed_dict and isinstance(embed_dict['color'], str):
                    try:
                        embed_dict['color'] = int(embed_dict['color'].lstrip('#'), 16)
                    except ValueError:
                        embed_dict.pop('color', None)
            
            if len(embed_dicts) > 10:
                status = await message.channel.send("❌ Error: A message cannot have more than 10 embeds.")
                await asyncio.sleep(10)
                await status.delete()
                return
            
            list_of_embeds = [discord.Embed.from_dict(d) for d in embed_dicts]

        except Exception as e:
            # Report any error during file reading or parsing
            status = await message.channel.send(f"❌ Error processing `rules.yaml`: {e}")
            await asyncio.sleep(10)
            await status.delete()
            await message.remove_reaction("⚙️", self.bot.user)
            await message.add_reaction("❌")
            return

        # --- Find target channel and post/edit the embed ---
        target_channel = self.bot.get_channel(target_channel_id)
        if not target_channel:
            status = await message.channel.send(f"❌ Error: Target channel (ID: {target_channel_id}) not found.")
            await asyncio.sleep(10)
            await status.delete()
            return
            
        final_message = None
        try:
            bot_message_to_edit = None
            async for old_message in target_channel.history(limit=100):
                if old_message.author == self.bot.user:
                    bot_message_to_edit = old_message
                    break
            
            if bot_message_to_edit:
                await bot_message_to_edit.edit(content=None, embeds=list_of_embeds)
                final_message = bot_message_to_edit
            else:
                new_message = await target_channel.send(embeds=list_of_embeds)
                final_message = new_message
        except discord.Forbidden:
             status = await message.channel.send("❌ Error: I don't have permission to send or edit messages in the target channel.")
             await asyncio.sleep(10)
             await status.delete()
             await message.remove_reaction("⚙️", self.bot.user)
             await message.add_reaction("❌")
             return

        # --- Cleanup Logic ---
        if final_message:
            async for old_message in target_channel.history(limit=100):
                if old_message.author == self.bot.user and old_message.id != final_message.id:
                    try:
                        await old_message.delete()
                    except (discord.Forbidden, discord.NotFound):
                        pass

        # All done, update the reaction to a checkmark
        await message.remove_reaction("⚙️", self.bot.user)
        await message.add_reaction("✅")

async def setup(bot: commands.Bot):
    await bot.add_cog(ManagementCog(bot))