import discord
from discord import app_commands
from discord.ext import commands
import os
import asyncio
from datetime import datetime

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

def create_embed(title: str = None, description: str = None, color: discord.Color = discord.Color.blue()) -> discord.Embed:
    """Helper function to create consistent embeds"""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text="Nexus Esports • Professional Communication")
    return embed

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
        embed = create_embed(
            title="❌ Access Denied",
            description="This command is restricted to the bot owner only.",
            color=discord.Color.red()
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)
    
    try:
        synced = await bot.tree.sync()
        embed = create_embed(
            title="✅ Success",
            description=f"Synced {len(synced)} commands globally!",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        embed = create_embed(
            title="❌ Sync Failed",
            description=f"Error: {e}",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="announce", description="Send an announcement to a channel")
@app_commands.describe(
    channel="Channel to send announcement to",
    message="Announcement message content",
    ping_everyone="Ping @everyone with this announcement"
)
async def announce(interaction: discord.Interaction, 
                  channel: discord.TextChannel, 
                  message: str,
                  ping_everyone: bool = False):
    """Send a professional announcement to a specified channel"""
    # Permission check
    if not has_announcement_permission(interaction):
        embed = create_embed(
            title="❌ Permission Denied",
            description="You need the Announcement role or 'Manage Messages' permission!",
            color=discord.Color.red()
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Create professional announcement embed
    embed = create_embed(
        title="📢 Official Announcement",
        description=message,
        color=discord.Color.gold()
    )
    embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
    
    try:
        # Prepare ping string
        ping_str = "@everyone " if ping_everyone else ""
        
        # Send announcement
        await channel.send(
            content=f"{ping_str}\n", 
            embed=embed,
            allowed_mentions=discord.AllowedMentions(everyone=True) if ping_everyone else None
        )
        
        embed = create_embed(
            title="✅ Announcement Sent",
            description=f"Announcement successfully sent to {channel.mention}!",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except discord.Forbidden:
        # Provide detailed permission error
        error_msg = "❌ Bot lacks permissions in that channel!\n"
        if ping_everyone:
            error_msg += "• Need 'Mention Everyone' permission to ping @everyone\n"
        error_msg += "• Required: Send Messages, Embed Links"
        
        embed = create_embed(
            title="❌ Permission Error",
            description=error_msg,
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        embed = create_embed(
            title="❌ Announcement Failed",
            description=f"Error: {e}",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="reply", description="Reply to a message in a channel")
@app_commands.describe(
    message_id="ID of the message to reply to",
    channel="Channel where the message is located",
    content="Your reply content"
)
async def reply(interaction: discord.Interaction,
               message_id: str,
               channel: discord.TextChannel,
               content: str):
    """Reply to a specific message in a channel"""
    if not has_announcement_permission(interaction):
        embed = create_embed(
            title="❌ Permission Denied",
            description="You need the Announcement role or 'Manage Messages' permission!",
            color=discord.Color.red()
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)
    
    try:
        message = await channel.fetch_message(int(message_id))
        
        # Create professional reply embed
        embed = create_embed(
            description=f"*Reply to [this message]({message.jump_url})*\n\n{content}",
            color=discord.Color.blue()
        )
        embed.set_author(
            name=f"Reply from {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        
        await channel.send(embed=embed)
        
        embed = create_embed(
            title="✅ Reply Sent",
            description=f"Your reply was successfully sent to {channel.mention}!",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except discord.NotFound:
        embed = create_embed(
            title="❌ Message Not Found",
            description="Could not find the specified message in that channel.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        embed = create_embed(
            title="❌ Reply Failed",
            description=f"Error: {e}",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="dm", description="Send a direct message to a user")
@app_commands.describe(
    user="User to message",
    message="Message content"
)
async def dm(interaction: discord.Interaction, 
             user: discord.Member, 
             message: str):
    """Send a professional direct message to a user"""
    if not has_announcement_permission(interaction):
        embed = create_embed(
            title="❌ Permission Denied",
            description="You need the Announcement role or 'Manage Messages' permission!",
            color=discord.Color.red()
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)
    
    try:
        # Create professional DM embed
        embed = create_embed(
            title="📩 Message from Nexus Esports",
            description=message,
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        
        # Send DM
        await user.send(embed=embed)
        
        embed = create_embed(
            title="✅ Message Delivered",
            description=f"Message successfully sent to {user.mention}!",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except discord.Forbidden:
        embed = create_embed(
            title="❌ Delivery Failed",
            description="User has DMs disabled or has blocked the bot.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        embed = create_embed(
            title="❌ Error Sending Message",
            description=f"Error: {e}",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="ping", description="Test bot responsiveness")
async def ping(interaction: discord.Interaction):
    """Simple ping command with latency check"""
    latency = round(bot.latency * 1000)
    embed = create_embed(
        title="🏓 Pong!",
        description=f"Bot latency: {latency}ms",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="my-permissions", description="Check your announcement permissions")
async def check_perms(interaction: discord.Interaction):
    """Command for users to check why they can't use announcement commands"""
    has_perm = has_announcement_permission(interaction)
    perm_status = "✅ You HAVE announcement permissions!" if has_perm else "❌ You DON'T HAVE announcement permissions"
    
    # Get user's roles
    roles = ", ".join([role.name for role in interaction.user.roles]) or "No roles"
    
    description = (
        f"{perm_status}\n\n"
        f"*Your roles:* {roles}\n"
        f"*Announcement role ID:* {ANNOUNCEMENT_ROLE_ID or 'Not set'}\n"
        f"*Manage Messages permission:* {interaction.user.guild_permissions.manage_messages}\n\n"
        f"Contact server admins if you should have access."
    )
    
    embed = create_embed(
        title="🔑 Your Permissions",
        description=description,
        color=discord.Color.blue()
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

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
    print(f"❌ Unexpected error: {e}")
