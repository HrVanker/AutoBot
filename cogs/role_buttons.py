import discord
from discord.ext import commands
from discord import app_commands

# This is our persistent view. It will be attached to the role message.
class RoleButtonView(discord.ui.View):
    def __init__(self, role_configs):
        # We need a timeout of None for the view to be persistent.
        super().__init__(timeout=None)
        
        # Create a button for each role in the config
        for config in role_configs:
            role_id = int(config["role_id"])
            label = config["label"]
            style = config.get("style", "green")
            
            # Map style string to discord.ButtonStyle enum
            style_map = {
                "primary": discord.ButtonStyle.primary,
                "secondary": discord.ButtonStyle.secondary,
                "green": discord.ButtonStyle.green,
                "danger": discord.ButtonStyle.danger,
            }
            
            button = discord.ui.Button(
                label=label,
                custom_id=f"role_button_{role_id}", # A unique ID for each button
                style=style_map.get(style.lower(), discord.ButtonStyle.green)
            )
            
            # Set the button's callback to our generic handler
            button.callback = self.handle_button_click
            self.add_item(button)

    async def handle_button_click(self, interaction: discord.Interaction):
        """This function is called when any button in the view is clicked."""
        # Get the role ID from the button's custom_id
        role_id = int(interaction.data["custom_id"].split("_")[-1])
        role = interaction.guild.get_role(role_id)
        
        if not role:
            await interaction.response.send_message("Error: This role no longer exists.", ephemeral=True)
            return

        # Check if the user already has the role
        has_role = role in interaction.user.roles
        
        try:
            if has_role:
                # If they have it, remove it
                await interaction.user.remove_roles(role, reason="Self-assigned role removal")
                await interaction.response.send_message(f"✅ The **{role.name}** role has been removed.", ephemeral=True)
            else:
                # If they don't, add it
                await interaction.user.add_roles(role, reason="Self-assigned role")
                await interaction.response.send_message(f"✅ You've been given the **{role.name}** role!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to modify your roles.", ephemeral=True)


class RoleButtonCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # On startup, we re-register the persistent view
        role_configs = bot.config.get("self_assign_roles", {}).get("roles", [])
        if role_configs:
            self.bot.add_view(RoleButtonView(role_configs))

    @app_commands.command(name="post-roles", description="Posts the self-assignable role message.")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def post_roles(self, interaction: discord.Interaction):
        """A moderator command to post the role selection panel."""
        config = self.bot.config.get("self_assign_roles", {})
        target_channel_id = int(config.get("channel_id", 0))
        
        if not target_channel_id:
            await interaction.response.send_message("The `self_assign_roles` configuration is missing in `config.json`.", ephemeral=True)
            return

        target_channel = self.bot.get_channel(target_channel_id)
        if not target_channel:
            await interaction.response.send_message(f"Error: Channel with ID `{target_channel_id}` not found.", ephemeral=True)
            return
            
        role_configs = config.get("roles", [])
        if not role_configs:
            await interaction.response.send_message("No roles are configured in the `self_assign_roles` section.", ephemeral=True)
            return

        # Create the embed and the view
        embed = discord.Embed(
            title=config.get("message_title", "Role Selection"),
            description=config.get("message_description", "Click the buttons to get your roles."),
            color=discord.Color.blue()
        )
        view = RoleButtonView(role_configs)
        
        try:
            await target_channel.send(embed=embed, view=view)
            await interaction.response.send_message(f"✅ Role message has been posted in {target_channel.mention}.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to send messages in that channel.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(RoleButtonCog(bot))