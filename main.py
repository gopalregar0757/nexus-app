import discord
from discord import app_commands
from discord.ext import commands
import os
import asyncio
from datetime import datetime
import json

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

# Configuration storage
CONFIG_FILE = "bot_config.json"
guild_configs = {}

def load_config():
    global guild_configs
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                guild_configs = json.load(f)
    except Exception as e:
        print(f"⚠️ Error loading config: {e}")
        guild_configs = {}

def save_config():
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(guild_configs, f, indent=2)
    except Exception as e:
        print(f"⚠️ Error saving config: {e}")

# Load config on startup
load_config()

@bot.event
async def on_ready():
    global commands_synced
    print(f"✅ Bot ready! Logged in as {bot.user}")
    
    # Print invite link with proper scopes
    invite_url = discord.utils.oauth_url(
        bot.user.id,
        permissions=discord.Permissions(
            send_messages=True,
            embed_links=True,
            view_channel=True,
            read_message_history=True,
            mention_everyone=True,
            manage_messages=True
        ),
        scopes=("bot", "applications.commands")
    )
    print(f"\n🔗 Add bot to other servers using this link (MUST include 'applications.commands' scope):\n{invite_url}\n")
    
    if not commands_synced:
        try:
            synced = await bot.tree.sync()
            commands_synced = True
            print(f"✅ Synced {len(synced)} command(s) globally")
        except Exception as e:
            print(f"❌ Command sync failed: {e}")

# Auto-reply to DMs
@bot.event
async def on_message(message):
    # Check if it's a DM and not from the bot itself
    if isinstance(message.channel, discord.DMChannel) and message.author != bot.user:
        # Create professional response embed
        embed = discord.Embed(
            title="📬 Nexus Esports Support",
            description=(
                "Thank you for your message!\n\n"
                "For official support, please contact:\n"
                "• **@acroneop** in our Official Server\n"
                "• Join: https://discord.gg/xPGJCWpMbM\n\n"
                "We'll assist you as soon as possible!"
            ),
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text="Nexus Esports Official | Dm Moderators or Officials for any Query!")
        
        # Try to send the response
        try:
            await message.channel.send(embed=embed)
        except discord.Forbidden:
            # Can't send message back (user blocked bot or closed DMs)
            pass
    
    # Process commands (important for command functionality)
    await bot.process_commands(message)

def create_embed(title: str = None, description: str = None, color: discord.Color = discord.Color.blue()) -> discord.Embed:
    """Helper function to create consistent embeds"""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text="Nexus Esports Official | Dm Moderators or Officials for any Query!")
    return embed

def has_announcement_permission(interaction: discord.Interaction) -> bool:
    """Check if user has announcement permissions through role or manage_messages"""
    if not interaction.guild:
        return False
    
    guild_id = str(interaction.guild.id)
    
    # Check if user has manage_messages permission
    if interaction.user.guild_permissions.manage_messages:
        return True
    
    # Check if user is server owner
    if interaction.user.id == interaction.guild.owner_id:
        return True
    
    # Check if user has announcement role
    if guild_id in guild_configs:
        role_id = guild_configs[guild_id].get("announcement_role")
        if role_id:
            return any(role.id == role_id for role in interaction.user.roles)
    
    return False

@bot.tree.command(name="set-announce-role", description="Set announcement role for this server (Admin only)")
@app_commands.describe(role="Role to use for announcement permissions")
async def set_announce_role(interaction: discord.Interaction, role: discord.Role):
    """Set the announcement role for the current server"""
    if not interaction.user.guild_permissions.manage_guild:
        embed = create_embed(
            title="❌ Permission Denied",
            description="You need 'Manage Server' permission to set announcement roles.",
            color=discord.Color.red()
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)
    
    guild_id = str(interaction.guild.id)
    
    # Initialize guild config if needed
    if guild_id not in guild_configs:
        guild_configs[guild_id] = {}
    
    # Save the role ID
    guild_configs[guild_id]["announcement_role"] = role.id
    save_config()
    
    embed = create_embed(
        title="✅ Announcement Role Set",
        description=f"{role.mention} is now the announcement role for this server.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="sync-commands", description="Sync bot commands (Server Owner only)")
async def sync_commands(interaction: discord.Interaction):
    """Sync commands for the current server"""
    # Check if user is server owner or bot owner
    app_info = await bot.application_info()
    is_bot_owner = interaction.user.id == app_info.owner.id
    is_server_owner = interaction.guild and interaction.user.id == interaction.guild.owner_id
    
    if not (is_bot_owner or is_server_owner):
        embed = create_embed(
            title="❌ Permission Denied",
            description="Only server owners or bot owners can sync commands.",
            color=discord.Color.red()
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Generate invite URL with proper scopes for troubleshooting
    invite_url = discord.utils.oauth_url(
        bot.user.id,
        permissions=discord.Permissions(
            send_messages=True,
            embed_links=True,
            view_channel=True,
            read_message_history=True,
            mention_everyone=True,
            manage_messages=True
        ),
        scopes=("bot", "applications.commands")
    )
    
    try:
        # Sync for the current guild
        if interaction.guild:
            await bot.tree.sync(guild=interaction.guild)
            message = f"✅ Commands synced for {interaction.guild.name}!"
        else:
            await bot.tree.sync()
            message = "✅ Global commands synced!"
        
        embed = create_embed(
            title="✅ Sync Successful",
            description=message,
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except discord.Forbidden as e:
        # Provide detailed troubleshooting for permission issues
        description = (
            f"❌ **Sync Failed: Bot lacks permissions**\n"
            f"Error: `{e}`\n\n"
            "**Troubleshooting Steps:**\n"
            "1. Re-invite the bot using this link with proper permissions:\n"
            f"{invite_url}\n"
            "2. Ensure the bot has **Manage Server** permission\n"
            "3. Server owner must run this command\n"
            "4. Check bot has `applications.commands` scope\n"
            "5. Wait 1 hour after bot invite for permissions to propagate"
        )
        embed = create_embed(
            title="❌ Sync Failed - Permissions Issue",
            description=description,
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        # Provide detailed troubleshooting for other issues
        description = (
            f"❌ **Sync Failed**\n"
            f"Error: `{e}`\n\n"
            "**Troubleshooting Steps:**\n"
            "1. Ensure the bot has `applications.commands` scope in invite\n"
            "2. Re-invite the bot using this link:\n"
            f"{invite_url}\n"
            "3. Server owner must run this command\n"
            "4. Try again in 5 minutes (Discord API might be slow)\n"
            "5. Contact support if issue persists"
        )
        embed = create_embed(
            title="❌ Sync Failed",
            description=description,
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="announce", description="Send an announcement to a channel")
@app_commands.describe(
    channel="Channel to send announcement to",
    message="Announcement message content",
    ping_everyone="Ping @everyone with this announcement",
    ping_here="Ping @here with this announcement"  # NEW OPTION ADDED
)
async def announce(interaction: discord.Interaction, 
                  channel: discord.TextChannel, 
                  message: str,
                  ping_everyone: bool = False,
                  ping_here: bool = False):  # NEW PARAMETER ADDED
    """Send a professional announcement to a specified channel"""
    # Permission check (unchanged)
    if not has_announcement_permission(interaction):
        embed = create_embed(
            title="❌ Permission Denied",
            description="You need the Announcement role or 'Manage Messages' permission!",
            color=discord.Color.red()
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Create professional announcement embed (unchanged)
    embed = create_embed(
        title=" ",
        description=message,
        color=discord.Color.gold()
    )
    
    if interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)
    
    try:
        # Prepare ping string - MODIFIED TO INCLUDE @HERE
        ping_str = ""
        if ping_everyone:
            ping_str += "@everyone "
        if ping_here:
            ping_str += "@here "
        
        # Send announcement - MODIFIED ALLOWED MENTIONS
        await channel.send(
            content=f"{ping_str}\n" if ping_str else None, 
            embed=embed,
            allowed_mentions=discord.AllowedMentions(everyone=True) if (ping_everyone or ping_here) else None
        )
        
        embed = create_embed(
            title="✅ Announcement Sent",
            description=f"Announcement successfully sent to {channel.mention}!",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except discord.Forbidden:
        # Provide detailed permission error - UPDATED MESSAGE
        error_msg = "❌ Bot lacks permissions in that channel!\n"
        if ping_everyone or ping_here:
            error_msg += "• Need 'Mention Everyone' permission to ping @everyone/@here\n"
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
            description=f"**Reply to [this message]({message.jump_url})**\n\n{content}",
            color=discord.Color.blue()
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
            title="📩 Message from Nexus Esports \nFor any Query or Further support tag @acroneop on Our Official Server: https://discord.gg/xPGJCWpMbM ",
            description=message,
            color=discord.Color.blue()
        )
        if interaction.guild and interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
        
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
    
    # Get current guild's announcement role
    guild_id = str(interaction.guild.id)
    announce_role_id = guild_configs.get(guild_id, {}).get("announcement_role") if interaction.guild else None
    
    description = (
        f"{perm_status}\n\n"
        f"**Your roles:** {roles}\n"
        f"**Announcement role ID:** {announce_role_id or 'Not set'}\n"
        f"**Manage Messages permission:** {interaction.user.guild_permissions.manage_messages}\n"
        f"**Server Owner:** {interaction.user.id == interaction.guild.owner_id}\n\n"
        f"Contact server admins if you should have access."
    )
    
    embed = create_embed(
        title="🔑 Your Permissions",
        description=description,
        color=discord.Color.blue()
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.event
async def on_guild_join(guild):
    """Handle joining new servers"""
    print(f"✅ Joined new server: {guild.name} (ID: {guild.id})")
    # Initialize default config for new server
    guild_id = str(guild.id)
    if guild_id not in guild_configs:
        guild_configs[guild_id] = {}
        save_config()
    
    # Sync commands for this new server
    try:
        await bot.tree.sync(guild=guild)
        print(f"✅ Synced commands for {guild.name}")
    except Exception as e:
        print(f"❌ Failed to sync commands for {guild.name}: {e}")

@bot.event
async def on_guild_remove(guild):
    """Handle leaving servers"""
    print(f"❌ Left server: {guild.name} (ID: {guild.id})")
    # Clean up config
    guild_id = str(guild.id)
    if guild_id in guild_configs:
        del guild_configs[guild_id]
        save_config()

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
