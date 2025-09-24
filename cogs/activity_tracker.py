import discord
from discord.ext import commands
from datetime import datetime
from utils import database
# We no longer need to import log_action here
from utils.role_utils import handle_role_add
import colorama
from colorama import Fore, Style, init
colorama.init(autoreset=True)

class ActivityTrackerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = bot.config.get("auto_promotion", {})
        self.vc_join_times = {}

    async def _check_promotion(self, member: discord.Member):
    # Check if the whole auto-promotion system is enabled
        if not self.config.get("enabled", False):
            return

        # Get the list of promotion rules
        promotion_rules = self.config.get("promotions", [])
    
        # Get the user's current activity stats once
        message_count, vc_time = database.get_user_activity(member.id)

        # Loop through each rule in the config
        for rule in promotion_rules:
            source_role_id = int(rule.get("source_role_id", 0))
            target_role_id = int(rule.get("target_role_id", 0))

            # Skip if IDs are missing
            if not source_role_id or not target_role_id:
                continue

            source_role = member.guild.get_role(source_role_id)
            target_role = member.guild.get_role(target_role_id)

            # Skip if roles don't exist in the server
            if not source_role or not target_role:
                continue

            # Check if the user is eligible for this specific promotion:
            # 1. They must have the source role.
            # 2. They must NOT already have the target role.
            if source_role not in member.roles or target_role in member.roles:
                continue

            # Get the thresholds for this rule
            msg_threshold = rule.get("message_threshold", 500)
            vc_min_threshold = rule.get("vc_threshold_minutes", 600)
            logic = rule.get("promotion_logic", "AND").upper()

            # Check if the user meets the thresholds
            met_messages = message_count >= msg_threshold
            met_vc_time = vc_time >= vc_min_threshold
        
            should_promote = (logic == "AND" and met_messages and met_vc_time) or \
                             (logic == "OR" and (met_messages or met_vc_time))

            if should_promote:
                # If they meet the criteria, promote them
                await handle_role_add(
                    bot=self.bot,
                    member=member,
                    role_to_add=target_role,
                    reason=f"Automatic promotion: {rule.get('name', 'N/A')}",
                    log_title="Automatic User Promotion",
                    log_responsible_party=f"System (Messages: {message_count}, VC Time: {vc_time} mins)"
                )
                # Stop checking after a successful promotion to avoid multiple promotions at once
                break 

    # ... (on_message and on_voice_state_update are unchanged)
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild or message.content.startswith('/'): 
            return
        
        database.log_message(message.author.id, message.channel.id)
        await self._check_promotion(message.author)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        # Log a "join" event
        if before.channel is None and after.channel is not None:
            database.log_vc_event(member.id, after.channel.id, "join")

        # Log a "leave" event
        elif before.channel is not None and after.channel is None:
            database.log_vc_event(member.id, before.channel.id, "leave")
            await self._check_promotion(member)

        # ▼▼▼ EXPANDED LOGIC FOR VOICE STATES ▼▼▼
        elif before.channel is not None and after.channel is not None:
            channel = after.channel # or before.channel, they are the same here
            if before.self_mute != after.self_mute:
                event = "mute" if after.self_mute else "unmute"
                database.log_voice_state_event(member.id, channel.id, event)
            elif before.self_deaf != after.self_deaf:
                event = "deafen" if after.self_deaf else "undeafen"
                database.log_voice_state_event(member.id, channel.id, event)
            elif before.self_stream != after.self_stream:
                event = "stream_start" if after.self_stream else "stream_stop"
                database.log_voice_state_event(member.id, channel.id, event)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if not self.config.get("enabled", False): return
        source_role_id = int(self.config.get("source_role_id", 0))
        if not source_role_id: return
        role = member.guild.get_role(source_role_id)
        if not role:
            print(Style.BRIGHT + Fore.RED + f"Error: Auto-assign role with ID {source_role_id} not found.")
            return
        
        # ▼▼▼ CONSOLIDATED LOGGING CALL ▼▼▼
        await handle_role_add(
            bot=self.bot,
            member=member,
            role_to_add=role,
            reason="New member autorole",
            log_title="New Member Role Assigned",
            log_responsible_party="System (Automatic)"
        )
        # ▲▲▲ CONSOLIDATED LOGGING CALL ▲▲▲
        # The separate log_action call that was here has been REMOVED.

    # ▼▼▼ NEW LISTENER FOR MESSAGE EDITS ▼▼▼
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot or not before.guild or before.content == after.content:
            return
        database.log_message_event(
            before.id, before.author.id, before.channel.id, "edit", content=before.content
        )

    # ▼▼▼ NEW LISTENER FOR MESSAGE DELETES ▼▼▼
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        database.log_message_event(
            message.id, message.author.id, message.channel.id, "delete"
        )
    
    # ▼▼▼ NEW LISTENERS FOR REACTIONS ▼▼▼
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.Member):
        if user.bot or not reaction.message.guild:
            return
        database.log_reaction(
            user.id, reaction.message.channel.id, reaction.message.id, reaction.emoji, "add"
        )

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction: discord.Reaction, user: discord.Member):
        if user.bot or not reaction.message.guild:
            return
        database.log_reaction(
            user.id, reaction.message.channel.id, reaction.message.id, reaction.emoji, "remove"
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(ActivityTrackerCog(bot))