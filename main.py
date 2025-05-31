import discord
from discord import app_commands
from discord.ext import commands
import os
import asyncio

# Debugging: Print environment information
print("="*50)
print("Starting Bot...")
print(f"Python version: {os.sys.version}")
print(f"Discord.py version: {discord.__version__}")
print("="*50)

# Get token from environment
token = os.getenv("DISCORD_TOKEN")
if token:
    print(f"✅ Token found (length: {len(token)} characters)")
else:
    print("❌ CRITICAL ERROR: Missing DISCORD_TOKEN")
    exit(1)

# Configure intents with explicit debugging
intents = discord.Intents.default()
print(f"Default intents value: {intents.value}")

# Enable required intents
intents.message_content = True
intents.members = True
print(f"Modified intents value: {intents.value}")
print(f"Members intent: {intents.members}")
print(f"Message content intent: {intents.message_content}")

bot = commands.Bot(
    command_prefix='!',
    intents=intents
)

# Global command sync flag
commands_synced = False

@bot.event
async def on_ready():
    global commands_synced
    print("\n" + "="*50)
    print(f"✅ Bot ready! Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"Guilds connected: {len(bot.guilds)}")
    
    # Print guild details
    for guild in bot.guilds:
        print(f"- {guild.name} (ID: {guild.id})")
        print(f"  Bot permissions: {guild.me.guild_permissions.value}")
    
    if not commands_synced:
        try:
            # Sync commands globally
            print("\nAttempting global command sync...")
            synced = await bot.tree.sync()
            commands_synced = True
            print(f"✅ Synced {len(synced)} command(s) globally")
            
            # Print synced command names
            print("Commands synced:")
            for cmd in synced:
                print(f"- {cmd.name}")
            
            # Additional verification
            await asyncio.sleep(2)
            app_info = await bot.application_info()
            print(f"\nBot owner: {app_info.owner} (ID: {app_info.owner.id})")
            
        except Exception as e:
            print(f"❌ Global sync failed: {e}")
            print("Trying guild-specific sync...")
            try:
                # Try syncing to current guilds
                for guild in bot.guilds:
                    try:
                        bot.tree.copy_global_to(guild=guild)
                        await bot.tree.sync(guild=guild)
                        print(f"✅ Synced commands to guild: {guild.name} (ID: {guild.id})")
                        commands_synced = True
                    except Exception as guild_e:
                        print(f"❌ Failed to sync to {guild.name}: {guild_e}")
            except Exception as e2:
                print(f"❌ Fallback sync failed: {e2}")
    print("="*50 + "\n")

@bot.tree.command(name="sync-cmds", description="Force sync commands (Owner only)")
async def sync_cmds(interaction: discord.Interaction):
    """Force sync commands with debug info"""
    app_info = await bot.application_info()
    if interaction.user.id != app_info.owner.id:
        return await interaction.response.send_message("❌ Owner only command!", ephemeral=True)
    
    try:
        # Debug info
        debug_info = f"Owner: {app_info.owner} (ID: {app_info.owner.id})\n"
        debug_info += f"Bot: {bot.user} (ID: {bot.user.id})\n"
        debug_info += f"Global commands: {len(await bot.tree.fetch_commands())}\n"
        
        # Perform sync
        synced = await bot.tree.sync()
        debug_info += f"✅ Synced {len(synced)} commands globally!"
        
        await interaction.response.send_message(debug_info, ephemeral=True)
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
    try:
        # Permission check
        if not interaction.user.guild_permissions.manage_messages:
            return await interaction.response.send_message(
                "❌ You need 'Manage Messages' permission!",
                ephemeral=True
            )
        
        # Create embed
        embed = discord.Embed(
            title="📢 Announcement",
            description=message,
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Announced by {interaction.user.display_name}")
        
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
            "❌ Bot lacks permissions in that channel!\n"
            f"Required: `Send Messages`, `Embed Links`\n"
            f"Current permissions: {channel.permissions_for(channel.guild.me).value}",
            ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(
            f"❌ Error: {e}",
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
    try:
        # Permission check
        if not interaction.user.guild_permissions.manage_messages:
            return await interaction.response.send_message(
                "❌ You need 'Manage Messages' permission!",
                ephemeral=True
            )
        
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
            "❌ User has DMs disabled or blocked the bot!",
            ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(
            f"❌ Error: {e}",
            ephemeral=True
        )

@bot.tree.command(name="ping", description="Test bot responsiveness")
async def ping(interaction: discord.Interaction):
    """Basic ping command with latency info"""
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(
        f"🏓 Pong! Latency: {latency}ms\n"
        f"Bot ID: {bot.user.id}\n"
        f"Shards: {bot.shard_count}",
        ephemeral=True
    )

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors"""
    if isinstance(error, commands.CommandNotFound):
        return
    print(f"❌ Command error: {error}")

# Start the bot with enhanced error handling
try:
    print("Starting bot...")
    bot.run(token)
except discord.PrivilegedIntentsRequired as e:
    print("\n" + "="*50)
    print("❌ PRIVILEGED INTENTS REQUIRED ❌")
    print(f"Error details: {e}")
    print("1. Go to https://discord.com/developers/applications")
    print("2. Select your application")
    print("3. Navigate to Bot > Privileged Gateway Intents")
    print("4. ENABLE 'MESSAGE CONTENT INTENT' and 'SERVER MEMBERS INTENT'")
    print("5. Save changes and restart your bot")
    print("="*50 + "\n")
    # Reraise to get full traceback
    raise
except discord.LoginFailure:
    print("\n❌ LOGIN FAILED: Invalid token")
    print("Verify your DISCORD_TOKEN environment variable")
    print(f"Token length: {len(token) if token else 0} characters")
    print("Get a new token at: https://discord.com/developers/applications")
    raise
except Exception as e:
    print(f"\n❌ UNEXPECTED ERROR: {e}")
    print("Please check the traceback above")
    raise
