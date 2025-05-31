import discord
from discord.ext import commands
import os

# Get token from environment with error handling
token = os.getenv("DISCORD_TOKEN")
if not token:
    print("❌ CRITICAL ERROR: DISCORD_TOKEN environment variable is missing!")
    print("Please set it in Railway's environment variables")
    exit(1)

print("✅ Token found in environment")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot is ready! Logged in as {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

try:
    bot.run(token)
except discord.LoginFailure:
    print("❌ Failed to log in. The token is invalid.")
    print("Please verify your token in the Discord Developer Portal")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
