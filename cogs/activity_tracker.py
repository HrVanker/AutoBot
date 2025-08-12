import discord
from discord.ext import commands
from datetime import datetime
from utils import database
# We no longer need to import log_action here
from utils.role_utils import handle_role_add

class ActivityTrackerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = bot.config.get("auto_promotion", {})
        self.vc_join_times = {}

    async def _check_promotion(self, member: discord.Member):
        # ... (This function's logic remains mostly the same until the end)
        if not self.config.get("enabled", False): return
        source_role_id = int(self.config.get("source_role_id", 0))
        target_role_id = int(self.config.get("target_role_id", 0))
        if not source_role_id or not target_role_id: return
        source_role = member.guild.get_role(source_role_id)
        target_role = member.guild.get_role(target_role_id)
        if not source_role or not target_role: return
        if source_role not in member.roles or target_role in member.roles: return
        msg_threshold = self.config.get("message_threshold", 500)
        vc_min_threshold = self.config.get("vc_threshold_minutes", 600)
        logic = self.config.get("promotion_logic", "AND").upper()
        message_count, vc_time = database.get_user_activity(member.id)
        met_messages = message_count >= msg_threshold
        met_vc_time = vc_time >= vc_min_threshold
        should_promote = (logic == "AND" and met_messages and met_vc_time) or \
                         (logic == "OR" and (met_messages or met_vc_time))
        if not should_promote: return

        # ▼▼▼ CONSOLIDATED LOGGING CALL ▼▼▼
        await handle_role_add(
            bot=self.bot,
            member=member,
            role_to_add=target_role,
            reason="Automatic promotion",
            log_title="Automatic User Promotion",
            log_responsible_party=f"System (Messages: {message_count}, VC Time: {vc_time} mins)"
        )
        # ▲▲▲ CONSOLIDATED LOGGING CALL ▲▲▲
        # The separate log_action call that was here has been REMOVED.

    # ... (on_message and on_voice_state_update are unchanged)
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild or message.content.startswith('/'): return
        database.update_user_activity(message.author.id, messages=1)
        await self._check_promotion(message.author)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        user_id = member.id
        if before.channel is None and after.channel is not None:
            self.vc_join_times[user_id] = datetime.utcnow()
        elif before.channel is not None and after.channel is None:
            if user_id in self.vc_join_times:
                join_time = self.vc_join_times.pop(user_id)
                duration_seconds = (datetime.utcnow() - join_time).total_seconds()
                duration_minutes = round(duration_seconds / 60)
                if duration_minutes > 0:
                    database.update_user_activity(member.id, vc_minutes=duration_minutes)
                    await self._check_promotion(member)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if not self.config.get("enabled", False): return
        source_role_id = int(self.config.get("source_role_id", 0))
        if not source_role_id: return
        role = member.guild.get_role(source_role_id)
        if not role:
            print(f"Error: Auto-assign role with ID {source_role_id} not found.")
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


async def setup(bot: commands.Bot):
    await bot.add_cog(ActivityTrackerCog(bot))