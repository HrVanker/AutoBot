import discord
from discord.ext import commands
from datetime import datetime
# Make sure to import your new functions
from utils import database 
from utils.role_utils import handle_role_add
import colorama
from colorama import Fore, Style, init
colorama.init(autoreset=True)

class ActivityTrackerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = bot.config.get("auto_promotion", {})
        # self.vc_join_times is no longer needed

    # The _check_promotion function can remain the same, but the underlying
    # database.get_user_activity function will need to be updated to calculate
    # totals from the new event tables instead of reading from the old 'users' table.

    async def _check_promotion(self, member: discord.Member):
        # ... (This function's logic remains the same for now)
        pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild or message.content.startswith('/'): 
            return
        
        # ▼▼▼ MODIFIED BEHAVIOR ▼▼▼
        # Log the specific message event instead of incrementing a counter
        database.log_message(message.author.id, message.channel.id)
        await self._check_promotion(message.author)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        
        # ▼▼▼ MODIFIED BEHAVIOR ▼▼▼
        # Log a "join" event when a user connects to a voice channel
        if before.channel is None and after.channel is not None:
            database.log_vc_event(member.id, after.channel.id, "join")

        # Log a "leave" event when a user disconnects from a voice channel
        elif before.channel is not None and after.channel is None:
            database.log_vc_event(member.id, before.channel.id, "leave")
            # You can still check for promotion after they leave a channel
            await self._check_promotion(member)

    # ... (on_member_join is unchanged) ...

async def setup(bot: commands.Bot):
    await bot.add_cog(ActivityTrackerCog(bot))