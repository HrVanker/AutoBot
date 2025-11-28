import discord
from discord.ext import commands
from discord import app_commands
# We no longer need to import log_action here
from utils.logger import log_action
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
    @app_commands.describe(user="The user to add the role to.", role="The role to add.", reason="Why you do like that?")
    async def add_role(self, interaction: discord.Interaction, user: discord.Member, role: discord.Role, reason: str = None):
        await interaction.response.defer(ephemeral=True)

        if not self.is_moderator(interaction):
            await interaction.followup.send("You don't have permission to use this command.", ephemeral=True)
            return

        if role >= interaction.guild.me.top_role:
            await interaction.followup.send(
                f"I can't assign the **{role.name}** role because it is higher than or equal to my highest role.",
                ephemeral=True
            )
            return

        try:
            await user.add_roles(role, reason=reason)
        
            # ▼▼▼ CONSOLIDATED LOGGING CALL ▼▼▼
            source_text = f"Moderator ({interaction.user.mention})"
            if reason:
                source_text += f" - Reason: {reason}"

            database.log_role_change(
                user_id=user.id,
                role_id=role.id,
                action="added",
                source=source_text
            )
            details_text = f"**Role:** {role.mention}"
            if reason:
                details_text += f"\n**Reason:** {reason}"
            
            await log_action(
                bot=self.bot,
                title="Manual Role Added",
                target_user=user,
                responsible_party=interaction.user.mention, # Use the moderator who ran the command
                details=details_text
            )
        
            await interaction.followup.send(f"Successfully added the **{role.name}** role to {user.mention}.", ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"An unexpected error occurred: {e}", ephemeral=True)
    
    # The 'remove_role' command does not need to change
    @role_group.command(name="remove", description="Remove a role from a user.")
    @app_commands.describe(user="The user to remove the role from.", role="The role to remove.", reason="Why, though?")
    async def remove_role(self, interaction: discord.Interaction, user: discord.Member, role: discord.Role, reason: str = None):
        await interaction.response.defer(ephemeral=True)

        if not self.is_moderator(interaction):
            await interaction.followup.send("You don't have permission to use this command.", ephemeral=True)
            return
            
        if role >= interaction.guild.me.top_role:
            await interaction.followup.send(
                f"I can't remove the **{role.name}** role because it is higher than or equal to my highest role.",
                ephemeral=True
            )
            return

        try:
            await user.remove_roles(role, reason=reason)
            await interaction.followup.send(f"Successfully removed the **{role.name}** role from {user.mention}.", ephemeral=True)
            
            # Construct the detailed source string for our database
            source_text = f"Moderator ({interaction.user.mention})"
            if reason:
                source_text += f" - Reason: {reason}"
            
            database.log_role_change(
                user_id=user.id,
                role_id=role.id,
                action="removed",
                source=source_text
            )
            details_text = f"**Role:** {role.mention}"
            if reason:
                details_text += f"\n**Reason:** {reason}"

            await log_action(
                bot=self.bot,
                title="Manual Role Removed",
                target_user=user,
                responsible_party=interaction.user.mention, # Use the moderator who ran the command
                details=details_text
            )
        except discord.Forbidden:
            await interaction.followup.send("I don't have the necessary permissions to remove that role.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"An unexpected error occurred: {e}", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(ManualRolesCog(bot))