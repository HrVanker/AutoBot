import colorama
from colorama import Fore, Style
import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
import sqlite3
import asyncio
from datetime import datetime
from utils.database import DB_FILE # This ensures we target the correct shared file
colorama.init(autoreset=True)

class BackupManagerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = self.bot.config.get("database_backup", {})
        
        # Start the scheduled backup task if it's enabled in the config
        if self.config.get("enabled", False):
            interval = self.config.get("interval_hours", 12)
            self.backup_task.change_interval(hours=interval)
            self.backup_task.start()

    def cog_unload(self):
        """Clean up the task when the cog is unloaded."""
        self.backup_task.cancel()

    def _perform_backup_sync(self):
        """
        Synchronous function to perform the backup using SQLite's online backup API.
        This is safe to use even if other bots are writing to the DB file.
        """
        backup_folder = self.config.get("backup_folder", "./backups")
        copies_to_keep = self.config.get("copies_to_keep", 2)

        # Ensure the backup directory exists
        os.makedirs(backup_folder, exist_ok=True)

        # Create the new backup file name
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_file_name = f"{DB_FILE.stem}_{timestamp}{DB_FILE.suffix}"
        backup_path = os.path.join(backup_folder, backup_file_name)

        src_conn = None
        dst_conn = None
        
        try:
            # 1. Connect to the live database (read-only usually sufficient, but standard open is fine)
            src_conn = sqlite3.connect(DB_FILE)
            
            # 2. Connect to the backup file (this creates it)
            dst_conn = sqlite3.connect(backup_path)
            
            # 3. Use the SQLite Backup API
            # This handles locking and copying correctly, even with WAL files
            with dst_conn:
                src_conn.backup(dst_conn)
            
            print(Fore.CYAN + f"Database backup successful: {backup_path}")

            # --- Rotation Logic ---
            backups = sorted(
                [os.path.join(backup_folder, f) for f in os.listdir(backup_folder)],
                key=os.path.getctime
            )
            
            # Delete oldest backups if we exceed the limit
            while len(backups) > copies_to_keep:
                file_to_delete = backups.pop(0)
                os.remove(file_to_delete)
                print(Fore.CYAN + f"Removed old backup: {file_to_delete}")
            
            return True, f"Backup created: `{backup_file_name}`"

        except Exception as e:
            print(Style.BRIGHT + Fore.YELLOW + f"Database backup failed: {e}")
            return False, str(e)
        
        finally:
            # Always close connections
            if src_conn: src_conn.close()
            if dst_conn: dst_conn.close()

    @tasks.loop(hours=12)
    async def backup_task(self):
        """The scheduled task that runs automatically."""
        print(Style.DIM + Fore.YELLOW + f"Running scheduled database backup...")
        # Run the blocking I/O operation in a separate thread
        await asyncio.to_thread(self._perform_backup_sync)

    @app_commands.command(name="backup-db", description="Manually triggers a database backup.")
    @app_commands.checks.has_permissions(administrator=True)
    async def backup_db(self, interaction: discord.Interaction):
        """A command for admins to manually create a backup."""
        await interaction.response.defer(ephemeral=True)
        
        # Run the blocking I/O operation in a separate thread
        success, message = await asyncio.to_thread(self._perform_backup_sync)
        
        if success:
            await interaction.followup.send(f"✅ Backup successful! {message}", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ Backup failed! Reason: {message}", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(BackupManagerCog(bot))