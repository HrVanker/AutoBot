import discord
from discord.ext import commands
from discord import app_commands
# We no longer need to import log_action here
from utils.role_utils import handle_role_add 
from utils import database

class ManualRolesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    role_group = app_commands.Group(name="role", description="Manual role management for moderators.")

    def is_moderator(self, interaction: discord.Interaction) -> bool:
        mod_role_id = int(self.bot.config.get("mod_role_id", 0))
        mod_role = interaction.guild.get_role(mod_role_id)
        if interaction.user.guild_permissions.administrator:
            return True
        if mod_role and mod_role in interaction.user.roles:
            return True
        return False

    @app_commands.command(name="rebuild-roles-db", description="Scans all members and populates the role database.")
    @app_commands.checks.has_permissions(administrator=True)
    async def rebuild_roles(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
    
        guild = interaction.guild
        member_count = 0
    
        # Loop through every member in the server
        for member in guild.members:
            if member.bot:
                continue
            
            # Get their current roles
            current_role_ids = [str(role.id) for role in member.roles if role.name != "@everyone"]
        
            # Save them to the database
            if current_role_ids:
                database.update_user_roles(member.id, current_role_ids)
                member_count += 1
                
        await interaction.followup.send(f"✅ Successfully scanned and saved roles for {member_count} members.")

    @role_group.command(name="add", description="Add a role to a user.")
    @app_commands.describe(user="The user to add the role to.", role="The role to add.")
    async def add_role(self, interaction: discord.Interaction, user: discord.Member, role: discord.Role):
        if not self.is_moderator(interaction):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return

        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message(
                f"I can't assign the **{role.name}** role because it is higher than or equal to my highest role.",
                ephemeral=True
            )
            return
        
        # ▼▼▼ CONSOLIDATED LOGGING CALL ▼▼▼
        reason_text = f"Role change initiated by {interaction.user.name}"
        await handle_role_add(
            bot=self.bot, 
            member=user, 
            role_to_add=role, 
            reason=reason_text,
            log_title="Manual Role Change", # New title
            log_responsible_party=interaction.user.mention # Pass who did it
        )
        # ▲▲▲ CONSOLIDATED LOGGING CALL ▲▲▲

        await interaction.response.send_message(f"Successfully processed the **{role.name}** role for {user.mention}.", ephemeral=True)
        # The separate log_action call that was here has been REMOVED.
    
    # The 'remove_role' command does not need to change
    @role_group.command(name="remove", description="Remove a role from a user.")
    @app_commands.describe(user="The user to remove the role from.", role="The role to remove.")
    async def remove_role(self, interaction: discord.Interaction, user: discord.Member, role: discord.Role):
        # (This function remains unchanged, as it only removes roles, no toggling)
        from utils.logger import log_action # We need it here now
        if not self.is_moderator(interaction):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
            
        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message(
                f"I can't remove the **{role.name}** role because it is higher than or equal to my highest role.",
                ephemeral=True
            )
            return

        try:
            await user.remove_roles(role, reason=f"Role removed by {interaction.user.name}")
            await interaction.response.send_message(f"Successfully removed the **{role.name}** role from {user.mention}.", ephemeral=True)
            
            await log_action(
                bot=self.bot,
                title="Manual Role Removed",
                target_user=user,
                responsible_party=interaction.user.mention,
                details=f"Removed Role: {role.mention}"
            )
        except discord.Forbidden:
            await interaction.response.send_message("I don't have the necessary permissions to remove that role.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An unexpected error occurred: {e}", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(ManualRolesCog(bot))