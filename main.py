import discord
from discord.ext import commands
import json
import os
import asyncio
from utils import database

# --- Bot Setup ---
# Load configuration from config.json
try:
    with open("config.json", "r") as f:
        config = json.load(f)
except FileNotFoundError:
    print("Error: config.json not found. Please create it.")
    exit()

# Define necessary intents for the bot to function
intents = discord.Intents.default()
intents.members = True          # Required for tracking members and roles
intents.message_content = True  # Required for tracking message counts
intents.voice_states = True     # Required for tracking voice channel activity

class RoleManagerBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.config = config
        self.guild_id = int(config["guild_id"])

    async def setup_hook(self):
        """This is called when the bot is preparing to start."""
        # Load all cogs from the 'cogs' directory
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    print(f"✅ Loaded cog: {filename}")
                except Exception as e:
                    print(f"❌ Failed to load cog {filename}: {e}")
        
        # Sync application commands to the specified guild
        guild = discord.Object(id=self.guild_id)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        print(" Slash commands synced to guild.")

    async def on_ready(self):
        """Called when the bot is connected and ready."""
        print("-" * 30)
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print(f"Connected to guild: {self.get_guild(self.guild_id).name}")
        print("RoleManager Bot is online and ready!")
        print("-" * 30)

# --- Main Execution ---
if __name__ == "__main__":
    # Initialize the database
    database.init_db()
    
    # Create and run the bot instance
    bot = RoleManagerBot()
    
    # Get the token and run the bot
    bot_token = config.get("bot_token")
    if not bot_token or bot_token == "YOUR_DISCORD_BOT_TOKEN_HERE":
        print("Error: Bot token is missing from config.json.")
    else:
        try:
            bot.run(bot_token)
        except discord.errors.LoginFailure:
            print("Error: Invalid bot token provided. Please check your config.json.")