import discord
from discord import app_commands
from discord.ext import commands
import os
import json
from datetime import datetime
from typing import Optional

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
            manage_messages=True,
            attach_files=True
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

def create_embed(title: str = None, description: str = None, color: discord.Color = discord.Color(0x3e0000)) -> discord.Embed:
    """Helper function to create consistent embeds"""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,  # Now uses #3e0000 as default
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
            color=discord.Color(0x3e0000)
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
            color=discord.Color(0x3e0000)
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
            manage_messages=True,
            attach_files=True
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
            color=discord.Color(0x3e0000)
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
            color=discord.Color(0x3e0000)
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# New Announcement Commands
@bot.tree.command(name="announce-simple", description="Send a simple text announcement")
@app_commands.describe(
    channel="Channel to send announcement to",
    message="Announcement message content (formatting preserved)",
    ping_everyone="Ping @everyone with this announcement",
    ping_here="Ping @here with this announcement"
)
async def announce_simple(interaction: discord.Interaction, 
                          channel: discord.TextChannel, 
                          message: str,
                          ping_everyone: bool = False,
                          ping_here: bool = False):
    """Send a simple text announcement"""
    if not has_announcement_permission(interaction):
        embed = create_embed(
            title="❌ Permission Denied",
            description="You need the Announcement role or 'Manage Messages' permission!",
            color=discord.Color(0x3e0000)
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Create professional announcement embed
    formatted_message = (
        "📢 **Official Announcement**\n\n"
        f"```\n{message}\n```"
    )
    embed = create_embed(
        description=formatted_message,
        color=discord.Color.gold()
    )
    
    if interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)
    
    try:
        # Prepare ping string
        ping_str = ""
        if ping_everyone:
            ping_str += "@everyone "
        if ping_here:
            ping_str += "@here "
        
        # Send announcement
        await channel.send(
            content=ping_str if ping_str else None, 
            embed=embed,
            allowed_mentions=discord.AllowedMentions(everyone=True) if (ping_everyone or ping_here) else None
        )
        
        embed = create_embed(
            title="✅ Announcement Sent",
            description=f"Simple announcement sent to {channel.mention}!",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        embed = create_embed(
            title="❌ Announcement Failed",
            description=f"Error: {e}",
            color=discord.Color(0x3e0000)
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="announce-attachment", description="Send announcement with text and attachment")
@app_commands.describe(
    channel="Channel to send announcement to",
    message="Announcement message content (formatting preserved)",
    attachment="File to attach to the announcement",
    ping_everyone="Ping @everyone with this announcement",
    ping_here="Ping @here with this announcement"
)
async def announce_attachment(interaction: discord.Interaction, 
                              channel: discord.TextChannel, 
                              message: str,
                              attachment: discord.Attachment,
                              ping_everyone: bool = False,
                              ping_here: bool = False):
    """Send announcement with text and attachment"""
    if not has_announcement_permission(interaction):
        embed = create_embed(
            title="❌ Permission Denied",
            description="You need the Announcement role or 'Manage Messages' permission!",
            color=discord.Color(0x3e0000)
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Create professional announcement embed
    formatted_message = (
        "📢 **Official Announcement**\n\n"
        f"```\n{message}\n```"
    )
    embed = create_embed(
        description=formatted_message,
        color=discord.Color.gold()
    )
    
    if interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)
    
    try:
        # Prepare ping string
        ping_str = ""
        if ping_everyone:
            ping_str += "@everyone "
        if ping_here:
            ping_str += "@here "
        
        # Process attachment
        file = await attachment.to_file()
        
        # Send announcement with attachment
        await channel.send(
            content=ping_str if ping_str else None, 
            embed=embed,
            file=file,
            allowed_mentions=discord.AllowedMentions(everyone=True) if (ping_everyone or ping_here) else None
        )
        
        embed = create_embed(
            title="✅ Announcement Sent",
            description=f"Announcement with attachment sent to {channel.mention}!",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        embed = create_embed(
            title="❌ Announcement Failed",
            description=f"Error: {e}",
            color=discord.Color(0x3e0000)
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="announce-only-attachment", description="Send announcement with only an attachment")
@app_commands.describe(
    channel="Channel to send announcement to",
    attachment="File to attach to the announcement",
    ping_everyone="Ping @everyone with this announcement",
    ping_here="Ping @here with this announcement"
)
async def announce_only_attachment(interaction: discord.Interaction, 
                                   channel: discord.TextChannel, 
                                   attachment: discord.Attachment,
                                   ping_everyone: bool = False,
                                   ping_here: bool = False):
    """Send announcement with only an attachment"""
    if not has_announcement_permission(interaction):
        embed = create_embed(
            title="❌ Permission Denied",
            description="You need the Announcement role or 'Manage Messages' permission!",
            color=discord.Color(0x3e0000)
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)
    
    try:
        # Prepare ping string
        ping_str = ""
        if ping_everyone:
            ping_str += "@everyone "
        if ping_here:
            ping_str += "@here "
        
        # Process attachment
        file = await attachment.to_file()
        
        # Send announcement with only attachment
        await channel.send(
            content=ping_str if ping_str else None, 
            file=file,
            allowed_mentions=discord.AllowedMentions(everyone=True) if (ping_everyone or ping_here) else None
        )
        
        embed = create_embed(
            title="✅ Announcement Sent",
            description=f"Attachment-only announcement sent to {channel.mention}!",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        embed = create_embed(
            title="❌ Announcement Failed",
            description=f"Error: {e}",
            color=discord.Color(0x3e0000)
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="dm-user", description="Send a DM to a specific user (Mods only)")
@app_commands.describe(
    user="The user to DM",
    message="The message to send",
    attachment="(Optional) File to attach"
)
async def dm_user(
    interaction: discord.Interaction,
    user: discord.User,
    message: str,
    attachment: Optional[discord.Attachment] = None
):
    """Send a direct message to a user"""
    # Check permissions
    if not interaction.user.guild_permissions.manage_messages:
        embed = create_embed(
            title="❌ Permission Denied",
            description="You need 'Manage Messages' permission to use this command.",
            color=discord.Color.red()
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)
    
    try:
        # Create the base message with server link
        base_message = (
            f"**Message from {interaction.guild.name}:**\n{message}\n\n"
            "For any queries or further support, contact @acroneop in our Official Server:\n"
            "https://discord.gg/xPGJCWpMbM"
        )
        
        # Add attachment notice if there's an attachment
        if attachment:
            base_message += "\n\n📎 *Attachment included*"
        
        # Create the embed
        embed = discord.Embed(
            description=base_message,
            color=discord.Color(0x3e0000),
            timestamp=datetime.utcnow()
        )
        
        # If there's an attachment
        files = []
        if attachment:
            file = await attachment.to_file()
            files.append(file)
            embed.set_image(url=f"attachment://{file.filename}")
        
        # Send the DM
        await user.send(embed=embed, files=files)
        
        # Confirm to the moderator
        confirm_message = f"Message sent to {user.mention}"
        if attachment:
            confirm_message += f" with attachment: {attachment.filename}"
            
        embed = create_embed(
            title="✅ DM Sent",
            description=confirm_message,
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except discord.Forbidden:
        embed = create_embed(
            title="❌ Failed to Send DM",
            description="This user has DMs disabled or blocked the bot.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        embed = create_embed(
            title="❌ Error",
            description=f"An error occurred: {str(e)}",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        embed = create_embed(
            title="❌ Error",
            description=f"An error occurred: {str(e)}",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        embed = create_embed(
            title="❌ Error",
            description=f"An error occurred: {str(e)}",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
@bot.tree.context_menu(name="Reply to User")
async def reply_to_user(interaction: discord.Interaction, message: discord.Message):
    """Reply to a user's message with a mention"""
    # Check permissions
    if not interaction.user.guild_permissions.manage_messages:
        embed = create_embed(
            title="❌ Permission Denied",
            description="You need 'Manage Messages' permission to use this command.",
            color=discord.Color.red()
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Create a modal for the reply
    class ReplyModal(discord.ui.Modal, title="Reply to User"):
        reply_content = discord.ui.TextInput(
            label="Your reply",
            style=discord.TextStyle.paragraph,
            placeholder="Type your reply here...",
            required=True
        )
        
        async def on_submit(self, interaction: discord.Interaction):
            # Send the reply mentioning the original author
            await interaction.channel.send(
                f"{message.author.mention}, {interaction.user.mention} replies:\n{self.reply_content}",
                allowed_mentions=discord.AllowedMentions(users=True)
            )
            await interaction.response.send_message(
                "✅ Reply sent!",
                ephemeral=True
            )
    
    await interaction.response.send_modal(ReplyModal())


# Welcome System - UPDATED
@bot.tree.command(name="set-welcome", description="Configure welcome messages (Admin only)")
@app_commands.describe(
    welcome_channel="Channel to send welcome messages",
    dm_message="Message to send in DMs when someone joins",
    dm_attachment_url="(Optional) URL of an image to include in the DM welcome"
)
async def set_welcome(interaction: discord.Interaction, 
                      welcome_channel: discord.TextChannel, 
                      dm_message: str,
                      dm_attachment_url: Optional[str] = None):
    """Set welcome channel and DM message"""
    if not interaction.user.guild_permissions.manage_guild:
        embed = create_embed(
            title="❌ Permission Denied",
            description="You need 'Manage Server' permission to configure welcome messages.",
            color=discord.Color(0x3e0000)
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)
    
    guild_id = str(interaction.guild.id)
    
    # Initialize guild config if needed
    if guild_id not in guild_configs:
        guild_configs[guild_id] = {}
    
    # Save welcome settings
    guild_configs[guild_id]["welcome_channel"] = welcome_channel.id
    guild_configs[guild_id]["welcome_dm"] = dm_message
    if dm_attachment_url:
        guild_configs[guild_id]["dm_attachment_url"] = dm_attachment_url
    save_config()
    
    # Build confirmation message
    conf_msg = (
        f"Welcome messages will be sent to {welcome_channel.mention}\n"
        f"DM message set to: ```\n{dm_message}\n```"
    )
    if dm_attachment_url:
        conf_msg += f"\nDM attachment URL set to: {dm_attachment_url[:50]}..."
    
    embed = create_embed(
        title="✅ Welcome System Configured",
        description=conf_msg,
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.event
async def on_member_join(member: discord.Member):
    """Send welcome messages when a member joins"""
    guild_id = str(member.guild.id)
    
    # Check if welcome is configured
    if guild_id not in guild_configs:
        return
    
    welcome_channel_id = guild_configs[guild_id].get("welcome_channel")
    
    # Send channel welcome
    if welcome_channel_id:
        try:
            channel = member.guild.get_channel(welcome_channel_id)
            if channel:
                # Create red-themed embed with proper formatting
                welcome_text = (
                    "First click on Nexus Esports above\n"
                    "and select 'Show All Channels' so that\n"
                    "all channels become visible to you.\n\n"
                    "💕 Welcome to Nexus Esports 💕"
                )
                
                embed = discord.Embed(
                    description=(
                        f"Bro {member.mention},\n\n"  # Mention outside the code block
                        f"```\n{welcome_text}\n```"   # Instructions inside code block
                    ),
                    color=discord.Color(0x3e0000)
                )
                # Set new GIF
                embed.set_image(url="https://cdn.discordapp.com/attachments/1378018158010695722/1378426905585520901/standard_2.gif")
                
                await channel.send(embed=embed)
        except Exception as e:
            print(f"⚠️ Error sending channel welcome: {e}")
    
    # ... rest of the DM welcome code remains the same ...
    
    # Send DM welcome (configured or fixed)
    try:
        # Get configured DM settings
        welcome_dm = guild_configs[guild_id].get("welcome_dm")
        dm_attachment_url = guild_configs[guild_id].get("dm_attachment_url")
        
        if welcome_dm:
            # Use configured DM
            embed = discord.Embed(
                description=welcome_dm,
                color=discord.Color(0x3e0000),
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text="Nexus Esports Official | DM Moderators or Officials for any Query!")
            
            # Add attachment if provided
            if dm_attachment_url:
                embed.set_image(url=dm_attachment_url)
            
            if member.guild.icon:
                embed.set_thumbnail(url=member.guild.icon.url)
            
            await member.send(embed=embed)
        else:
            # Fallback to fixed DM
            dm_message = (
                "🌟 Welcome to Nexus Esports! 🌟\n\n"
                "Thank you for joining our gaming community! We're excited to have you on board.\n\n"
                "As mentioned in our welcome channel:\n"
                "1. Click \"Nexus Esports\" at the top of the server\n"
                "2. Select \"Show All Channels\" to access everything\n"
                "3. Explore our community spaces!\n\n"
                "Quick Start:\n"
                "• Read #rules for guidelines\n"
                "• Introduce yourself in #introductions\n"
                "• Check #announcements for news\n"
                "• Join tournaments in #events\n\n"
                "Need help? Contact @acroneop or our mod team anytime!\n\n"
                "We're glad you're here! 🎮"
            )
            
            # Create professional DM embed (red theme)
            embed = discord.Embed(
                description=dm_message,
                color=discord.Color(0x3e0000),
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text="Nexus Esports Official | DM Moderators or Officials for any Query!")
            
            if member.guild.icon:
                embed.set_thumbnail(url=member.guild.icon.url)
            
            await member.send(embed=embed)
    except discord.Forbidden:
        # User has DMs disabled
        pass
    except Exception as e:
        print(f"⚠️ Error sending welcome DM: {e}")

# Other commands remain the same
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
