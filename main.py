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
        scopes=("bot", "applications.commands")  # Ensure applications.commands scope is included
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
    
    try:
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

# ... rest of the code remains unchanged (announce, reply, dm, ping, my-permissions, etc.) ...
