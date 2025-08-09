import sys
import os

print("--- Python Environment Diagnostic ---")
print(f"Python Executable: {sys.executable}")
print(f"Python Version: {sys.version}")
print("-" * 20)

try:
    import discord
    print("✅ 'discord.py' library was successfully imported.")
    print(f"discord.py Version: {discord.__version__}")
    print(f"Location: {discord.__file__}")

    # Check for the .Bot attribute
    if hasattr(discord, 'Bot'):
        print("✅ discord.Bot attribute was FOUND.")
    else:
        print("❌ discord.Bot attribute was NOT FOUND.")

except ImportError:
    print("❌ Critical Error: The 'discord' library could not be imported at all.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

print("-" * 20)
print("Python's Search Paths (sys.path):")
for path in sys.path:
    print(f"- {path}")
print("--- End of Diagnostic ---")