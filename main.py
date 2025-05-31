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
intents.members = True

bot = commands.Bot(
    command_prefix='!',
    intents=intents
)

# Global command sync flag
commands_synced = False

# Add your announcement role ID here (or set via environment variable)
ANNOUNCEMENT_ROLE_ID = int(os.getenv("ANNOUNCEMENT_ROLE_ID", 0))  # Default to 0 if not set

@bot.event
async def on_ready():
    global commands_synced
    print(f"✅ Bot ready! Logged in as {bot.user}")
    
    if not commands_synced:
        try:
            synced = await bot.tree.sync()
            commands_synced = True
            print(f"✅ Synced {len(synced)} command(s) globally")
        except Exception as e:
            print(f"❌ Command sync failed: {e}")

def has_announcement_permission(interaction: discord.Interaction) -> bool:
    """Check if user has announcement permissions through role or manage_messages"""
    # Check if user has manage_messages permission
    if interaction.user.guild_permissions.manage_messages:
        return True
    
    # Check if user has announcement role
    if ANNOUNCEMENT_ROLE_ID:
        return any(role.id == ANNOUNCEMENT_ROLE_ID for role in interaction.user.roles)
    
    return False

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
    if not has_announcement_permission(interaction):
        return await interaction.response.send_message(
            "❌ You need the Announcement role or 'Manage Messages' permission!",
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
    if not has_announcement_permission(interaction):
        return await interaction.response.send_message(
            "❌ You need the Announcement role or 'Manage Messages' permission!",
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

@bot.tree.command(name="my-permissions", description="Check your announcement permissions")
async def check_perms(interaction: discord.Interaction):
    """Command for users to check why they can't use announcement commands"""
    has_perm = has_announcement_permission(interaction)
    perm_status = "✅ You HAVE announcement permissions!" if has_perm else "❌ You DON'T HAVE announcement permissions"
    
    # Get user's roles
    roles = ", ".join([role.name for role in interaction.user.roles]) or "No roles"
    
    response = (
        f"{perm_status}\n\n"
        f"**Your roles:** {roles}\n"
        f"**Announcement role ID:** {ANNOUNCEMENT_ROLE_ID or 'Not set'}\n"
        f"**Manage Messages permission:** {interaction.user.guild_permissions.manage_messages}\n\n"
        f"Contact server admins if you should have access."
    )
    
    await interaction.response.send_message(response, ephemeral=True)

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
