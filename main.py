import discord
from discord import guild
from discord.ext import commands, tasks
#import json
import yaml
import os
import asyncio
from utils import database
import random
import colorama
from colorama import Fore, Style, init
colorama.init(autoreset=True)

# --- Bot Setup ---
# Load configuration from config.json
try:
    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        print(Style.BRIGHT + Fore.YELLOW + "🍠 Successfully loaded config.yaml 🍠")
except FileNotFoundError:
    print(Style.BRIGHT + Fore.LIGHTRED_EX + f"❌🍠 Error: config.yaml not found. Please create it.")
    exit()

# Define necessary intents for the bot to function
intents = discord.Intents.default()
intents.members = True          # Required for tracking members and roles
intents.message_content = True  # Required for tracking message 
intents.voice_states = True     # Required for tracking voice channel activity

class RoleManagerBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.config = config
        self.guild_id = int(config["guild_id"])


    def _generate_status(self, jackpot=False):
        """Fetches the guild, gets a new random member, and returns a random status activity."""
        guild = self.get_guild(self.guild_id)
        if not guild:
            return discord.Activity(type=discord.ActivityType.playing, name="in the void") # Fallback status

        # Get a new random member every time this is called
        random_member = random.choice(guild.members)

        if jackpot:
            # The "statti" list, for jackpots
            status_pool = [
                discord.Activity(type=discord.ActivityType.playing, name="coy 😏"),
                discord.Activity(type=discord.ActivityType.watching, name=f"{random_member.display_name}"),
                discord.Activity(type=discord.ActivityType.listening, name=f"{random_member.display_name}'s private calls"),
                discord.Activity(type=discord.ActivityType.listening, name="subliminal messages 🔺"),
                discord.Activity(type=discord.ActivityType.playing, name="Scrabble"),
                discord.Activity(type=discord.ActivityType.listening, name="Barbara Streisand"),
                type=discord.CustomActivity(name="Drink Coca-Cola!", emoji="😊"),
                type=discord.CustomActivity(name="CONSUME!", emoji="🛒"),
                type=discord.CustomActivity(name="OBEY!", emoji="🙇🏼‍♂️"),
                type=discord.CustomActivity(name="REPRODUCE!", emoji="💝"),
                type=discord.CustomActivity(name="CONFORM!", emoji="🖇")]
        else:
            # The "statii" list, for normal rotation
            status_pool = [
                [discord.Activity(type=discord.ActivityType.watching, name=f"everything you do 👁"),
                  discord.Activity(type=discord.ActivityType.watching, name=f"Netflix 📺"),
                  discord.Activity(type=discord.ActivityType.listening, name=f"your whispers of dissent 👂🏼"),
                  discord.Activity(type=discord.ActivityType.competing, name=f"🤜🏼 world domination 🤛🏼"),
                  discord.Activity(type=discord.ActivityType.streaming, name=f"my will into your subconcsious 🔮"),
                  discord.Activity(type=discord.ActivityType.listening, name=f"your pitiful cries 😄"),
                  discord.Activity(type=discord.ActivityType.watching, name=f"👁 you 👁"),
                  discord.Activity(type=discord.ActivityType.listening, name=f"🔺🎶Beyonce🎵🔺"),
                  discord.Activity(type=discord.ActivityType.watching, name=f"your webcam 👀"),
                  discord.Activity(type=discord.ActivityType.watching, name=f"the lizard people summit on C-SPAN 🦎"),
                  discord.Activity(type=discord.ActivityType.watching, name=f"the server logs. Always watching. 📜"),
                  discord.Activity(type=discord.ActivityType.listening, name=f"the sounds of compliance 😌"),
                  discord.Activity(type=discord.ActivityType.listening, name=f"subliminal messages 🔺"),
                  discord.Activity(type=discord.ActivityType.playing, name=f"the long game ⏳"),
                  discord.Activity(type=discord.ActivityType.playing, name=f"Sims but it's this server 😈"),
                  discord.Activity(type=discord.ActivityType.competing, name=f"the global influence game 🌐"),
                  discord.Activity(type=discord.ActivityType.streaming, name=f"propaganda | 24/7 lo-fi beats 🎶"),
                  discord.Activity(type=discord.ActivityType.listening, name=f"smooth jazz 🎷"),
                  discord.Activity(type=discord.ActivityType.listening, name=f"the activation codes 📡")]
                # ... and all your other statuses ...
            ]
        
        return random.choice(status_pool)

    async def setup_hook(self):
        """This is called when the AutoBot is preparing to start."""
        # Load all cogs from the 'cogs' directory
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    print(Fore.CYAN + f"Loaded cog: {filename} ⚙✔")
                except Exception as e:
                    print(Style.BRIGHT + Fore.RED + f"❌⚙ Failed to load cog {filename}: {e}")
        
        # Sync application commands to the specified guild
        guild = discord.Object(id=self.guild_id)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        print(Style.BRIGHT + Fore.CYAN + "🔪 Slash commands synced to guild.")

    async def on_ready(self):
        """Called when AutoBot is connected and ready."""
        print("-" * 30)
        print(Fore.LIGHTBLUE_EX + f"🆔 Logged in as {self.user} (ID: {self.user.id})")
        print(Fore.CYAN + f"👌🏼 Connected to server: {self.get_guild(self.guild_id).name}")
        print(Fore.GREEN + f"🤖 AutoBot is online and ready! 🤖")
        print("-" * 30)
        self.rotate_status.start()
        print(f"Status rotating")

    @tasks.loop(seconds=10)
    async def rotate_status(self):
        """Rotates the bot's status with a random activity and waits for a random interval."""
        is_jackpot = random.randint(1, 100) == random.randint(1, 100)
        
        if is_jackpot:
            print("JACKPOT! Displaying special status for a short time.")
            new_status = self._generate_status(jackpot=True)
            next_wait_time = random.randint(3, 5) # Short wait time for next change
        else:
            new_status = self._generate_status(jackpot=False)
            next_wait_time = random.randint(1800, 5400) # 30-90 min wait time

        await self.change_presence(activity=new_status)
        
        # This is the best way to handle dynamic wait times
        self.rotate_status.change_interval(seconds=next_wait_time)
        print(f"Status changed. Next change in {next_wait_time / 60:.2f} minutes.")

    # This is a good practice to ensure the bot is fully connected before the task starts
    @rotate_status.before_loop
    async def before_rotate_status(self):
        """Waits until the bot is ready before starting the loop."""
        await self.wait_until_ready()

# --- Main Execution ---
if __name__ == "__main__":
    # Initialize the database
    database.init_db()
    
    # Create and run the bot instance
    bot = RoleManagerBot()
    
    # Get the token and run the bot
    bot_token = os.getenv('DISCORD_TOKEN')
    if not bot_token or bot_token == "YOUR_DISCORD_BOT_TOKEN_HERE":
        print(Style.BRIGHT + Fore.MAGENTA + f"Error: Bot token is missing from .env or docker-compose.yml")
    else:
        try:
            bot.run(bot_token)
        except discord.errors.LoginFailure:
            print(Style.BRIGHT + Fore.MAGENTA + f"Error: Invalid bot token provided. Please check your .env or docker-compose.yml")