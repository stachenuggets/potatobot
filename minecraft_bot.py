"""
Minecraft Server Manager Discord Bot
Handles: start, stop, save, status, and restart commands
"""

import discord
from discord.ext import commands
import os
import subprocess
import asyncio
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

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Color constants for embeds
COLOR_SUCCESS = discord.Color.green()
COLOR_ERROR = discord.Color.red()
COLOR_INFO = discord.Color.blue()
COLOR_WARNING = discord.Color.orange()

# Track server state
server_state = {
    'running': False,
    'process': None,
}


async def rcon_command(command: str) -> str:
    """Execute a command via RCON and return the response"""
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            response = mcr.command(command)
        return response
    except Exception as e:
        raise Exception(f"RCON Error: {str(e)}")


async def start_server() -> bool:
    """Start the Minecraft server"""
    if server_state['running']:
        return False  # Already running
    
    try:
        # Change to server directory
        os.chdir(SERVER_DIR)
        
        # Start the server process
        server_state['process'] = subprocess.Popen(
            SERVER_START_CMD,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        server_state['running'] = True
        
        # Wait a bit for the server to start
        await asyncio.sleep(3)
        return True
    except Exception as e:
        raise Exception(f"Failed to start server: {str(e)}")


async def stop_server() -> bool:
    """Stop the Minecraft server gracefully via RCON"""
    if not server_state['running']:
        return False  # Not running
    
    try:
        # Send stop command via RCON
        await rcon_command("stop")
        server_state['running'] = False
        
        # Give it time to shut down
        await asyncio.sleep(2)
        return True
    except Exception as e:
        raise Exception(f"Failed to stop server: {str(e)}")


async def save_server() -> bool:
    """Save the server data"""
    if not server_state['running']:
        raise Exception("Server is not running!")
    
    try:
        await rcon_command("save-all")
        await asyncio.sleep(1)
        return True
    except Exception as e:
        raise Exception(f"Failed to save server: {str(e)}")


async def get_server_status() -> dict:
    """Get current server status"""
    try:
        # Try to ping via RCON to check if running
        await rcon_command("list")
        return {
            'running': True,
            'message': '✅ Server is online'
        }
    except:
        return {
            'running': False,
            'message': '❌ Server is offline'
        }


@bot.event
async def on_ready():
    """Bot ready event"""
    print(f'{bot.user} has connected to Discord!')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="your server"))


@bot.command(name='start', help='Start the Minecraft server')
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
            embed.add_field(name='Status', value='Booting', inline=False)
            embed.add_field(name='ETA', value='~30 seconds', inline=False)
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title='❌ Start Failed',
                description=str(e),
                color=COLOR_ERROR
            )
            await ctx.send(embed=embed)


@bot.command(name='stop', help='Stop the Minecraft server gracefully')
async def stop_cmd(ctx):
    """Stop the server"""
    async with ctx.typing():
        try:
            await stop_server()
            embed = discord.Embed(
                title='⏹️ Server Stopping',
                description='The Minecraft server has been stopped gracefully.',
                color=COLOR_WARNING
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title='❌ Stop Failed',
                description=str(e),
                color=COLOR_ERROR
            )
            await ctx.send(embed=embed)


@bot.command(name='save', help='Save the server world')
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
            embed = discord.Embed(
                title='❌ Save Failed',
                description=str(e),
                color=COLOR_ERROR
            )
            await ctx.send(embed=embed)


@bot.command(name='restart', help='Restart the Minecraft server')
async def restart_cmd(ctx):
    """Restart the server"""
    embed = discord.Embed(
        title='🔄 Restarting Server',
        description='Saving world and restarting...',
        color=COLOR_INFO
    )
    await ctx.send(embed=embed)
    
    async with ctx.typing():
        try:
            # Save first
            if server_state['running']:
                await rcon_command("say Server restarting in 10 seconds...")
                await rcon_command("save-all")
                await asyncio.sleep(2)
                await stop_server()
                await asyncio.sleep(3)
            
            # Start again
            await start_server()
            
            embed = discord.Embed(
                title='✅ Server Restarted',
                description='The server is back online.',
                color=COLOR_SUCCESS
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title='❌ Restart Failed',
                description=str(e),
                color=COLOR_ERROR
            )
            await ctx.send(embed=embed)


@bot.command(name='status', help='Check the server status')
async def status_cmd(ctx):
    """Check server status"""
    async with ctx.typing():
        status = await get_server_status()
        
        if status['running']:
            embed = discord.Embed(
                title='✅ Server Status',
                description=status['message'],
                color=COLOR_SUCCESS
            )
        else:
            embed = discord.Embed(
                title='❌ Server Status',
                description=status['message'],
                color=COLOR_ERROR
            )
        
        await ctx.send(embed=embed)


@bot.command(name='say', help='Send a message to the server chat')
async def say_cmd(ctx, *, message):
    """Send a message to server chat"""
    if not message:
        embed = discord.Embed(
            title='❌ Error',
            description='Please provide a message.',
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
        return
    
    async with ctx.typing():
        try:
            await rcon_command(f'say {message}')
            embed = discord.Embed(
                title='💬 Message Sent',
                description=f'Sent to server: {message}',
                color=COLOR_SUCCESS
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title='❌ Failed',
                description=str(e),
                color=COLOR_ERROR
            )
            await ctx.send(embed=embed)


if __name__ == '__main__':
    bot.run(DISCORD_TOKEN)
