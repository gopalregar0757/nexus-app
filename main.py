import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True  # REQUIRED for commands

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot is ready! Logged in as {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

bot.run(os.getenv("DISCORD_TOKEN"))
