import discord
from discord.ext import commands
from discord import app_commands
from utils.logger import log_action

class ManualRolesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Define a command group for role management
    role_group = app_commands.Group(name="role", description="Manual role management for moderators.")

    def is_moderator(self, interaction: discord.Interaction) -> bool:
        """Check if the user is an admin or has the configured mod role."""
        mod_role_id = int(self.bot.config.get("mod_role_id", 0))
        mod_role = interaction.guild.get_role(mod_role_id)
        
        if interaction.user.guild_permissions.administrator:
            return True
        if mod_role and mod_role in interaction.user.roles:
            return True
        return False

    @role_group.command(name="add", description="Add a role to a user.")
    @app_commands.describe(user="The user to add the role to.", role="The role to add.")
    async def add_role(self, interaction: discord.Interaction, user: discord.Member, role: discord.Role):
        """Adds a specified role to a user."""
        if not self.is_moderator(interaction):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return

        # Prevent mods from adding roles higher than the bot's highest role
        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message(
                f"I can't assign the **{role.name}** role because it is higher than or equal to my highest role.",
                ephemeral=True
            )
            return

        try:
            await user.add_roles(role, reason=f"Role added by {interaction.user.name}")
            await interaction.response.send_message(f"Successfully added the **{role.name}** role to {user.mention}.", ephemeral=True)
            
            # Log the action
            await log_action(
                bot=self.bot,
                title="Manual Role Added",
                target_user=user,
                responsible_party=interaction.user.mention,
                details=f"Added Role: {role.mention}"
            )
        except discord.Forbidden:
            await interaction.response.send_message("I don't have the necessary permissions to add that role.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An unexpected error occurred: {e}", ephemeral=True)

    @role_group.command(name="remove", description="Remove a role from a user.")
    @app_commands.describe(user="The user to remove the role from.", role="The role to remove.")
    async def remove_role(self, interaction: discord.Interaction, user: discord.Member, role: discord.Role):
        """Removes a specified role from a user."""
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
            
            # Log the action
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