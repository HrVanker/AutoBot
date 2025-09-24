from colorama import Fore, Style
import colorama
import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
import shutil
from datetime import datetime
from utils.database import DB_FILE # Import your DB_FILE variable
colorama.init(autoreset=True)

class BackupManagerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = self.bot.config.get("database_backup", {})
        
        # Start the scheduled backup task if it's enabled in the config
        # if self.config.get("enabled", False):
        #     interval = self.config.get("interval_hours", 12)
        #     self.backup_task.change_interval(hours=interval)
        #     self.backup_task.start()

    def cog_unload(self):
        """Clean up the task when the cog is unloaded."""
        self.backup_task.cancel()

    def perform_backup(self):
        """The core logic for creating and rotating backups."""
        backup_folder = self.config.get("backup_folder", "./backups")
        copies_to_keep = self.config.get("copies_to_keep", 2)

        # Ensure the backup directory exists
        os.makedirs(backup_folder, exist_ok=True)

        # Create the new backup file
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_file_name = f"{DB_FILE.stem}_{timestamp}{DB_FILE.suffix}"
        backup_path = os.path.join(backup_folder, backup_file_name)

        try:
            shutil.copyfile(DB_FILE, backup_path)
            print(Fore.CYAN + f"Database backup successful: {backup_path}")

            # --- Rotation Logic ---
            # Get all backup files, sorted by creation time (oldest first)
            backups = sorted(
                [os.path.join(backup_folder, f) for f in os.listdir(backup_folder)],
                key=os.path.getctime
            )
            
            # If we have more backups than we want to keep, delete the oldest ones
            while len(backups) > copies_to_keep:
                file_to_delete = backups.pop(0)
                os.remove(file_to_delete)
                print(Fore.CYAN + f"Removed old backup: {file_to_delete}")
            
            return True, f"Backup created: `{backup_file_name}`"
        except Exception as e:
            print(Style.BRIGHT + Fore.YELLOW + f"Database backup failed: {e}")
            return False, str(e)

    # @tasks.loop(hours=12)
    # async def backup_task(self):
    #     """The scheduled task that runs automatically."""
    #     print(Style.DIM + Fore.YELLOW + f"Running scheduled database backup...")
    #     self.perform_backup()

    # @app_commands.command(name="backup-db", description="Manually triggers a database backup.")
    # @app_commands.checks.has_permissions(administrator=True)
    # async def backup_db(self, interaction: discord.Interaction):
    #     """A command for admins to manually create a backup."""
    #     await interaction.response.defer(ephemeral=True)
    #     success, message = self.perform_backup()
    #     if success:
    #         await interaction.followup.send(f"✅ Backup successful! {message}")
    #     else:
    #         await interaction.followup.send(f"❌ Backup failed! Reason: {message}")


async def setup(bot: commands.Bot):
    # Make sure you import the DB_FILE variable into this cog
    from utils import database
    # This ensures the cog can find the database file to back it up
    await bot.add_cog(BackupManagerCog(bot))