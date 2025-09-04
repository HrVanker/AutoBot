import discord
from discord.ext import commands
import asyncio
from utils import database # Make sure your database functions are accessible

class RolePersistenceCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """
        Listens for changes in a member's roles and updates the database.
        """
        # Ignore if the roles haven't changed
        if before.roles == after.roles:
            return

        # --- Update the current set of roles for the user ---
        # Get a list of all current role IDs as strings
        current_role_ids = [str(role.id) for role in after.roles if role.name != "@everyone"]
        database.update_user_roles(after.id, current_role_ids)

        # --- Determine what changed and log it to history ---
        before_roles = set(before.roles)
        after_roles = set(after.roles)

        added_roles = after_roles - before_roles
        removed_roles = before_roles - after_roles
        
        # We need a small delay to ensure the audit log is populated
        await asyncio.sleep(2)
        
        # Determine the source of the change from the audit log
        source = "Unknown"
        try:
            async for entry in after.guild.audit_logs(limit=5, action=discord.AuditLogAction.member_role_update):
                # Find the specific log entry for this member
                if entry.target.id == after.id:
                    if entry.user.id == self.bot.user.id:
                        source = f"System ({entry.reason or 'Automatic'})"
                    else:
                        source = f"Moderator ({entry.user.mention})"
                    break # Stop after finding the relevant entry
        except discord.Forbidden:
            source = "Source Unknown (Missing Audit Log Permissions)"

        # Log added roles
        for role in added_roles:
            database.log_role_change(user_id=after.id, role_id=role.id, action="added", source=source)

        # Log removed roles
        for role in removed_roles:
            database.log_role_change(user_id=after.id, role_id=role.id, action="removed", source=source)


    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """
        Checks if a returning member has saved roles and re-applies them.
        """
        saved_roles = database.get_user_roles(member.id)
        if not saved_roles:
            return # No roles to restore

        roles_to_add = []
        for role_id_str in saved_roles:
            role = member.guild.get_role(int(role_id_str))
            # Add the role if it exists, is not managed by an integration (e.g. boosts),
            # and the bot has permission to assign it.
            if role and not role.is_bot_managed() and role < member.guild.me.top_role:
                roles_to_add.append(role)
        
        if roles_to_add:
            try:
                await member.add_roles(*roles_to_add, reason="Automatic role restoration for returning member.")
                print(f"Restored {len(roles_to_add)} roles for returning member {member.name}.")
            except discord.Forbidden:
                print(f"Failed to restore roles for {member.name} due to missing permissions.")
            except discord.HTTPException as e:
                print(f"An error occurred while restoring roles for {member.name}: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(RolePersistenceCog(bot))