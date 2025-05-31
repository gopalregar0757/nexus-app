import discord
from discord.ext import commands
import os

from keep_alive import keep_alive
keep_alive()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

ANNOUNCER_ROLE = "Announcer"

@bot.event
async def on_ready():
    print(f"✅ Bot is ready! Logged in as {bot.user}")

@bot.event
async def on_member_join(member):
    welcome_channel = discord.utils.get(member.guild.text_channels, name="general")
    if welcome_channel:
        await welcome_channel.send(f"👋 Welcome to the server, {member.mention}!")

@bot.command()
async def say(ctx, *, message):
    await ctx.send(message)

@bot.command()
@commands.has_role(ANNOUNCER_ROLE)
async def announce(ctx, *, message):
    embed = discord.Embed(title="📢 Announcement", description=message, color=0xff9900)
    embed.set_footer(text=f"From {ctx.author.display_name}")
    await ctx.send(embed=embed)

@announce.error
async def announce_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("❌ You need the 'Announcer' role to use this command.")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason"):
    await member.kick(reason=reason)
    await ctx.send(f"👢 {member.mention} has been kicked. Reason: {reason}")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason"):
    await member.ban(reason=reason)
    await ctx.send(f"🔨 {member.mention} has been banned. Reason: {reason}")

@bot.command()
async def poll(ctx, *, question):
    embed = discord.Embed(title="🗳️ Poll", description=question, color=0x3498db)
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("👍")
    await msg.add_reaction("👎")

bot.run(os.getenv("DISCORD_TOKEN"))
