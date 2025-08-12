import discord
from .logger import log_action

async def handle_role_add(bot, member: discord.Member, role_to_add: discord.Role, reason: str):
    """
    A centralized handler for adding roles.
    It adds the specified role and automatically removes any conflicting roles
    as defined in the config's 'toggled_roles'.
    """
    if role_to_add in member.roles:
        return # The user already has the role, do nothing.

    try:
        # 1. Add the new role
        await member.add_roles(role_to_add, reason=reason)

        # 2. Check for conflicting roles to remove
        toggles = bot.config.get("toggled_roles", {})
        role_to_add_id = str(role_to_add.id)
        conflicting_role_id_str = None

        # Check for conflicts in both directions (key->value and value->key)
        if role_to_add_id in toggles:
            conflicting_role_id_str = toggles[role_to_add_id]
        else:
            for key, value in toggles.items():
                if value == role_to_add_id:
                    conflicting_role_id_str = key
                    break
        
        # 3. If a conflicting role exists and the user has it, remove it
        if conflicting_role_id_str:
            conflicting_role_id = int(conflicting_role_id_str)
            conflicting_role = member.guild.get_role(conflicting_role_id)

            if conflicting_role and conflicting_role in member.roles:
                await member.remove_roles(conflicting_role, reason=f"Toggled by adding {role_to_add.name}")
                # Log the secondary removal
                await log_action(
                    bot=bot,
                    title="Automatic Role Removed (Toggle)",
                    target_user=member,
                    responsible_party="System (Automatic)",
                    details=f"Removed {conflicting_role.mention} because {role_to_add.mention} was added."
                )

    except discord.Forbidden:
        print(f"Error: Bot lacks permissions to manage roles for {member.name}.")
    except Exception as e:
        print(f"An unexpected error occurred in handle_role_add: {e}")