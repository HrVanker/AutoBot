import discord
from .logger import log_action

async def handle_role_add(bot, member: discord.Member, role_to_add: discord.Role, reason: str, log_title: str, log_responsible_party: str):
    """
    A centralized handler for adding roles.
    It adds the specified role, removes conflicting roles, and sends a single,
    consolidated log message.
    """
    if role_to_add in member.roles:
        return # The user already has the role, do nothing.

    removed_role = None # Variable to store the role that gets removed

    try:
        # 1. Add the new role
        await member.add_roles(role_to_add, reason=reason)

        # 2. Check for conflicting roles to remove
        toggles = bot.config.get("toggled_roles", {})
        role_to_add_id = str(role_to_add.id)
        conflicting_role_id_str = None

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
            conflicting_role_obj = member.guild.get_role(conflicting_role_id)

            if conflicting_role_obj and conflicting_role_obj in member.roles:
                await member.remove_roles(conflicting_role_obj, reason=f"Toggled by adding {role_to_add.name}")
                removed_role = conflicting_role_obj # Save the removed role for logging

        # 4. Construct and send the single log message
        details = f"✅ Added Role: {role_to_add.mention}"
        if removed_role:
            details += f"\n❌ Removed Toggled Role: {removed_role.mention}"

        await log_action(
            bot=bot,
            title=log_title,
            target_user=member,
            responsible_party=log_responsible_party,
            details=details
        )

    except discord.Forbidden:
        print(f"Error: Bot lacks permissions to manage roles for {member.name}.")
    except Exception as e:
        print(f"An unexpected error occurred in handle_role_add: {e}")