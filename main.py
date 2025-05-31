import discord
from discord.ext import commands
import os

# Get token from environment
token = os.getenv("DISCORD_TOKEN")
if not token:
    print("❌ CRITICAL ERROR: Missing DISCORD_TOKEN")
    exit(1)

# Configure intents properly
intents = discord.Intents.default()
intents.message_content = True  # Required for command processing

bot = commands.Bot(
    command_prefix='!',
    intents=intents
)

@bot.event
async def on_ready():
    print(f"✅ Bot ready! Logged in as {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

try:
    bot.run(token)
except discord.PrivilegedIntentsRequired:
    print("\n❌ PRIVILEGED INTENTS REQUIRED ❌")
    print("1. Go to https://discord.com/developers/applications")
    print("2. Select your application")
    print("3. Navigate to Bot > Privileged Gateway Intents")
    print("4. ENABLE 'MESSAGE CONTENT INTENT'")
    print("5. Save changes and restart your bot\n")
except discord.LoginFailure:
    print("❌ Invalid token. Check your DISCORD_TOKEN")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
