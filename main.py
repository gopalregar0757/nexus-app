import discord
from discord import app_commands
from discord.ext import commands
import os
import asyncio

# Get token from environment
token = os.getenv("DISCORD_TOKEN")
if not token:
    print("❌ CRITICAL ERROR: Missing DISCORD_TOKEN")
    exit(1)

# Configure intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Required for user mentions

bot = commands.Bot(
    command_prefix='!',
    intents=intents
)

# Global command sync flag
commands_synced = False

@bot.event
async def on_ready():
    global commands_synced
    print(f"✅ Bot ready! Logged in as {bot.user}")
    
    if not commands_synced:
        try:
            # Sync commands globally
            synced = await bot.tree.sync()
            commands_synced = True
            print(f"✅ Synced {len(synced)} command(s) globally")
            
            # Additional verification
            await asyncio.sleep(2)  # Wait for propagation
            app_info = await bot.application_info()
            print(f"Bot ID: {app_info.id}")
            print(f"Owner: {app_info.owner}")
            
        except Exception as e:
            print(f"❌ Command sync failed: {e}")
            print("Trying fallback sync method...")
            try:
                # Try syncing to current guild only
                for guild in bot.guilds:
                    bot.tree.copy_global_to(guild=guild)
                    await bot.tree.sync(guild=guild)
                    print(f"✅ Synced commands to guild: {guild.name}")
                commands_synced = True
            except Exception as e2:
                print(f"❌ Fallback sync failed: {e2}")

# Command to force sync
@bot.tree.command(name="sync-cmds", description="Force sync commands (Owner only)")
async def sync_cmds(interaction: discord.Interaction):
    if interaction.user.id != (await bot.application_info()).owner.id:
        return await interaction.response.send_message("❌ Owner only command!", ephemeral=True)
    
    try:
        synced = await bot.tree.sync()
        await interaction.response.send_message(
            f"✅ Synced {len(synced)} commands globally!",
            ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(
            f"❌ Sync failed: {e}",
            ephemeral=True
        )

@bot.tree.command(name="send-announce", description="Send an announcement to a channel")
@app_commands.describe(
    channel="Channel to send announcement to",
    message="Announcement message content",
    ping_role="Optional role to ping (use @role)"
)
async def send_announce(interaction: discord.Interaction, 
                        channel: discord.TextChannel, 
                        message: str,
                        ping_role: discord.Role = None):
    # Permission check
    if not interaction.user.guild_permissions.manage_messages:
        return await interaction.response.send_message(
            "❌ You need 'Manage Messages' permission to use this command!",
            ephemeral=True
        )
    
    # Create embed
    embed = discord.Embed(
        title="📢 Announcement",
        description=message,
        color=discord.Color.gold()
    )
    embed.set_footer(text=f"Announced by {interaction.user.display_name}")
    
    try:
        # Prepare ping string
        ping_str = f"{ping_role.mention} " if ping_role else ""
        
        # Send announcement
        await channel.send(f"{ping_str}\n", embed=embed)
        await interaction.response.send_message(
            f"✅ Announcement sent to {channel.mention}!",
            ephemeral=True
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I don't have permission to send messages in that channel!",
            ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(
            f"❌ Failed to send announcement: {e}",
            ephemeral=True
        )

@bot.tree.command(name="send-message", description="Send a direct message to a user")
@app_commands.describe(
    user="User to message",
    message="Message content"
)
async def send_message(interaction: discord.Interaction, 
                       user: discord.Member, 
                       message: str):
    # Permission check
    if not interaction.user.guild_permissions.manage_messages:
        return await interaction.response.send_message(
            "❌ You need 'Manage Messages' permission to use this command!",
            ephemeral=True
        )
    
    try:
        # Create embed for DM
        embed = discord.Embed(
            title=f"Message from {interaction.guild.name}",
            description=message,
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Sent by {interaction.user.display_name}")
        
        # Send DM
        await user.send(embed=embed)
        await interaction.response.send_message(
            f"✅ Message sent to {user.mention}!",
            ephemeral=True
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ User has DMs disabled or blocked me!",
            ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(
            f"❌ Failed to send message: {e}",
            ephemeral=True
        )

@bot.tree.command(name="ping", description="Test bot responsiveness")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong!")

try:
    bot.run(token)
except discord.PrivilegedIntentsRequired:
    print("\n❌ PRIVILEGED INTENTS REQUIRED ❌")
    print("1. Go to https://discord.com/developers/applications")
    print("2. Select your application")
    print("3. Navigate to Bot > Privileged Gateway Intents")
    print("4. ENABLE 'MESSAGE CONTENT INTENT' and 'SERVER MEMBERS INTENT'")
    print("5. Save changes and restart your bot\n")
except discord.LoginFailure:
    print("❌ Invalid token. Check your DISCORD_TOKEN")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
