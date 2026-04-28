"""
Advanced Minecraft Server Manager Discord Bot
Features: start, stop, save, status, backup, player monitoring, role-based access
"""

import discord
from discord.ext import commands, tasks
import os
import subprocess
import asyncio
import shutil
from datetime import datetime
from pathlib import Path
from mcrcon import MCRcon
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
RCON_HOST = os.getenv('RCON_HOST', 'localhost')
RCON_PORT = int(os.getenv('RCON_PORT', 25575))
RCON_PASSWORD = os.getenv('RCON_PASSWORD')
SERVER_DIR = os.getenv('SERVER_DIR', '/path/to/minecraft/server')
SERVER_START_CMD = os.getenv('SERVER_START_CMD', 'java -Xmx30G -Xms30G -jar server.jar nogui')
BACKUP_DIR = os.getenv('BACKUP_DIR', './backups')
ADMIN_ROLE = os.getenv('ADMIN_ROLE', 'Admin')  # Discord role required for dangerous commands
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID', 0))  # Optional: channel for bot logs

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Colors for embeds
COLOR_SUCCESS = discord.Color.green()
COLOR_ERROR = discord.Color.red()
COLOR_INFO = discord.Color.blue()
COLOR_WARNING = discord.Color.orange()

# Server state
server_state = {
    'running': False,
    'process': None,
    'last_backup': None,
    'start_time': None,
}

# Create backup directory
Path(BACKUP_DIR).mkdir(parents=True, exist_ok=True)


def has_admin_role():
    """Check if user has admin role"""
    async def predicate(ctx):
        if ctx.author.guild_permissions.administrator:
            return True
        if ADMIN_ROLE:
            return discord.utils.get(ctx.author.roles, name=ADMIN_ROLE) is not None
        return False
    return commands.check(predicate)


async def rcon_command(command: str) -> str:
    """Execute a command via RCON"""
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            response = mcr.command(command)
        return response
    except Exception as e:
        raise Exception(f"RCON Error: {str(e)}")


async def log_action(message: str):
    """Log action to designated channel"""
    if LOG_CHANNEL_ID and LOG_CHANNEL_ID != 0:
        try:
            channel = bot.get_channel(LOG_CHANNEL_ID)
            if channel:
                embed = discord.Embed(
                    title='🔔 Server Action',
                    description=message,
                    color=COLOR_INFO,
                    timestamp=datetime.now()
                )
                await channel.send(embed=embed)
        except Exception as e:
            print(f"Failed to log action: {e}")


async def start_server() -> bool:
    """Start the Minecraft server"""
    if server_state['running']:
        return False
    
    try:
        os.chdir(SERVER_DIR)
        server_state['process'] = subprocess.Popen(
            SERVER_START_CMD,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        server_state['running'] = True
        server_state['start_time'] = datetime.now()
        await log_action("Server started")
        await asyncio.sleep(3)
        return True
    except Exception as e:
        raise Exception(f"Failed to start server: {str(e)}")


async def stop_server() -> bool:
    """Stop the server gracefully"""
    if not server_state['running']:
        return False
    
    try:
        await rcon_command("stop")
        server_state['running'] = False
        await log_action("Server stopped")
        await asyncio.sleep(2)
        return True
    except Exception as e:
        raise Exception(f"Failed to stop server: {str(e)}")


async def save_server() -> bool:
    """Save the server"""
    if not server_state['running']:
        raise Exception("Server is not running!")
    
    try:
        await rcon_command("save-all flush")
        await log_action("Server saved")
        await asyncio.sleep(1)
        return True
    except Exception as e:
        raise Exception(f"Failed to save: {str(e)}")


async def backup_server() -> str:
    """Create a backup of the server"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}"
        backup_path = os.path.join(BACKUP_DIR, backup_name)
        
        # Save first if running
        if server_state['running']:
            await rcon_command("save-all flush")
            await asyncio.sleep(1)
        
        # Copy world directory
        world_dir = os.path.join(SERVER_DIR, 'world')
        if os.path.exists(world_dir):
            shutil.copytree(world_dir, os.path.join(backup_path, 'world'))
        
        # Copy server.properties
        props_file = os.path.join(SERVER_DIR, 'server.properties')
        if os.path.exists(props_file):
            shutil.copy(props_file, backup_path)
        
        server_state['last_backup'] = backup_name
        await log_action(f"Backup created: {backup_name}")
        return backup_name
    except Exception as e:
        raise Exception(f"Backup failed: {str(e)}")


async def get_player_list() -> str:
    """Get current player list"""
    try:
        if not server_state['running']:
            return "Server is not running"
        response = await rcon_command("list")
        return response
    except:
        return "Unable to fetch player list"


async def get_server_status() -> dict:
    """Get server status"""
    try:
        await rcon_command("list")
        uptime = "Unknown"
        if server_state['start_time']:
            delta = datetime.now() - server_state['start_time']
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            uptime = f"{hours}h {minutes}m"
        
        return {
            'running': True,
            'uptime': uptime,
            'message': '✅ Server is online'
        }
    except:
        return {
            'running': False,
            'uptime': 'N/A',
            'message': '❌ Server is offline'
        }


@bot.event
async def on_ready():
    """Bot ready"""
    print(f'{bot.user} has connected to Discord!')
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="your Minecraft server"
        )
    )
    check_server_status.start()


@tasks.loop(minutes=5)
async def check_server_status():
    """Periodic server status check"""
    status = await get_server_status()
    if not status['running'] and server_state['running']:
        server_state['running'] = False
        await log_action("⚠️ Server detected offline (was running)")


@bot.command(name='start', help='Start the server')
@has_admin_role()
async def start_cmd(ctx):
    """Start the server"""
    async with ctx.typing():
        try:
            await start_server()
            embed = discord.Embed(
                title='🚀 Server Starting',
                description='The Minecraft server is starting up...',
                color=COLOR_SUCCESS
            )
            embed.add_field(name='ETA', value='~30 seconds', inline=False)
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(title='❌ Start Failed', description=str(e), color=COLOR_ERROR)
            await ctx.send(embed=embed)


@bot.command(name='stop', help='Stop the server gracefully')
@has_admin_role()
async def stop_cmd(ctx):
    """Stop the server"""
    async with ctx.typing():
        try:
            await stop_server()
            embed = discord.Embed(
                title='⏹️ Server Stopped',
                description='The Minecraft server has been stopped gracefully.',
                color=COLOR_WARNING
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(title='❌ Stop Failed', description=str(e), color=COLOR_ERROR)
            await ctx.send(embed=embed)


@bot.command(name='save', help='Save the server')
async def save_cmd(ctx):
    """Save the server"""
    async with ctx.typing():
        try:
            await save_server()
            embed = discord.Embed(
                title='💾 Server Saved',
                description='All data has been saved to disk.',
                color=COLOR_SUCCESS
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(title='❌ Save Failed', description=str(e), color=COLOR_ERROR)
            await ctx.send(embed=embed)


@bot.command(name='restart', help='Restart the server')
@has_admin_role()
async def restart_cmd(ctx):
    """Restart the server"""
    embed = discord.Embed(
        title='🔄 Restarting Server',
        description='Saving and restarting...',
        color=COLOR_INFO
    )
    await ctx.send(embed=embed)
    
    async with ctx.typing():
        try:
            if server_state['running']:
                await rcon_command("say Server restarting in 10 seconds!")
                await rcon_command("save-all flush")
                await asyncio.sleep(2)
                await stop_server()
                await asyncio.sleep(3)
            
            await start_server()
            embed = discord.Embed(
                title='✅ Server Restarted',
                description='The server is back online.',
                color=COLOR_SUCCESS
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(title='❌ Restart Failed', description=str(e), color=COLOR_ERROR)
            await ctx.send(embed=embed)


@bot.command(name='backup', help='Create a world backup')
@has_admin_role()
async def backup_cmd(ctx):
    """Create a backup"""
    async with ctx.typing():
        try:
            backup_name = await backup_server()
            embed = discord.Embed(
                title='✅ Backup Created',
                description=f'Backup: `{backup_name}`',
                color=COLOR_SUCCESS
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(title='❌ Backup Failed', description=str(e), color=COLOR_ERROR)
            await ctx.send(embed=embed)


@bot.command(name='status', help='Check server status')
async def status_cmd(ctx):
    """Check server status"""
    async with ctx.typing():
        status = await get_server_status()
        players = await get_player_list()
        
        color = COLOR_SUCCESS if status['running'] else COLOR_ERROR
        embed = discord.Embed(title='📊 Server Status', color=color)
        embed.add_field(name='Status', value=status['message'], inline=False)
        embed.add_field(name='Uptime', value=status['uptime'], inline=False)
        embed.add_field(name='Players', value=f'```{players}```', inline=False)
        if server_state['last_backup']:
            embed.add_field(name='Last Backup', value=server_state['last_backup'], inline=False)
        
        await ctx.send(embed=embed)


@bot.command(name='say', help='Send a message to server chat')
async def say_cmd(ctx, *, message):
    """Send a message"""
    if not message:
        embed = discord.Embed(title='❌ Error', description='Please provide a message.', color=COLOR_ERROR)
        await ctx.send(embed=embed)
        return
    
    async with ctx.typing():
        try:
            await rcon_command(f'say {message}')
            embed = discord.Embed(
                title='💬 Message Sent',
                description=f'`{message}`',
                color=COLOR_SUCCESS
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(title='❌ Failed', description=str(e), color=COLOR_ERROR)
            await ctx.send(embed=embed)


@bot.command(name='help', help='Show all commands')
async def help_cmd(ctx):
    """Show help"""
    embed = discord.Embed(title='📖 Minecraft Server Commands', color=COLOR_INFO)
    embed.add_field(name='!status', value='Check server status and player count', inline=False)
    embed.add_field(name='!start', value='Start the server (Admin only)', inline=False)
    embed.add_field(name='!stop', value='Stop the server gracefully (Admin only)', inline=False)
    embed.add_field(name='!restart', value='Restart the server (Admin only)', inline=False)
    embed.add_field(name='!save', value='Save the world to disk', inline=False)
    embed.add_field(name='!backup', value='Create a backup (Admin only)', inline=False)
    embed.add_field(name='!say <message>', value='Send a message to server chat', inline=False)
    
    await ctx.send(embed=embed)


if __name__ == '__main__':
    bot.run(DISCORD_TOKEN)
