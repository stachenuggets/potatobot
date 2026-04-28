# Minecraft Server Discord Bot - Setup Guide

## Prerequisites
- Python 3.8+
- A Discord server where you can add a bot
- A self-hosted Minecraft server with RCON enabled
- The bot will run on the same machine as your server (or network-accessible)

---

## Step 1: Enable RCON on Your Minecraft Server

Edit your Minecraft server's `server.properties` file:

```properties
enable-rcon=true
rcon.password=your_secure_password_here
rcon.port=25575
```

Restart your Minecraft server after making these changes.

---

## Step 2: Create a Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name (e.g., "Minecraft Manager")
3. Go to the "Bot" tab and click "Add Bot"
4. Under the bot's username, click "Reset Token" and copy it (keep this SECRET)
5. Go to OAuth2 → URL Generator
6. Select scopes: `bot`
7. Select permissions:
   - `Send Messages`
   - `Embed Links`
   - `Read Message History`
8. Copy the generated URL and visit it to add the bot to your Discord server

---

## Step 3: Install Dependencies

```bash
pip install discord.py python-dotenv mcrcon
```

Or using a requirements file:

```bash
pip install -r requirements.txt
```

**requirements.txt:**
```
discord.py==2.4.0
python-dotenv==1.0.1
mcrcon==0.6.1
```

---

## Step 4: Configure Environment Variables

1. Create a `.env` file in the same directory as `minecraft_bot.py`
2. Fill in your configuration:

```env
DISCORD_TOKEN=your_bot_token_here
RCON_HOST=localhost
RCON_PORT=25575
RCON_PASSWORD=your_rcon_password_here
SERVER_DIR=/path/to/minecraft/server
SERVER_START_CMD=java -Xmx30G -Xms30G -jar server.jar nogui
```

**Important Notes:**
- `SERVER_DIR` should be the full path to your Minecraft server directory
- `SERVER_START_CMD` needs to match your server's startup command exactly
- Adjust `-Xmx30G -Xms30G` to match your available RAM
- For Spigot/Paper/Purpur servers, use their respective jar files

---

## Step 5: Run the Bot

```bash
python minecraft_bot.py
```

You should see:
```
YourBotName#1234 has connected to Discord!
```

---

## Step 6: Test Commands

In any Discord channel where your bot has message permissions:

| Command | Description |
|---------|-------------|
| `!start` | Start the Minecraft server |
| `!stop` | Stop the server gracefully |
| `!restart` | Restart the server |
| `!save` | Save the world to disk |
| `!status` | Check if the server is online |
| `!say <message>` | Send a message to server chat |

---

## Step 7: Run Bot on Startup (Linux/macOS)

### Using systemd (Linux)

Create `/etc/systemd/system/minecraft-bot.service`:

```ini
[Unit]
Description=Minecraft Discord Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/bot
ExecStart=/usr/bin/python3 /path/to/bot/minecraft_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable minecraft-bot
sudo systemctl start minecraft-bot
```

### Using launchd (macOS)

Create `~/Library/LaunchAgents/com.minecraft.bot.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.minecraft.bot</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/path/to/minecraft_bot.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/bot</string>
    <key>StandardErrorPath</key>
    <string>/tmp/minecraft-bot.err</string>
    <key>StandardOutPath</key>
    <string>/tmp/minecraft-bot.out</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

Load it:
```bash
launchctl load ~/Library/LaunchAgents/com.minecraft.bot.plist
```

### Using PM2 (Any OS)

```bash
npm install -g pm2
pm2 start minecraft_bot.py --name "minecraft-bot" --interpreter python3
pm2 save
pm2 startup
```

---

## Troubleshooting

### "RCON Error: Connection refused"
- Verify RCON is enabled in `server.properties`
- Check `rcon.port` matches your config
- Ensure the server is running
- If remote: check firewall rules

### "Failed to start server"
- Verify `SERVER_DIR` path exists
- Check `SERVER_START_CMD` is correct for your server type
- Ensure the bot has permission to execute the command
- Test starting manually first

### Bot doesn't respond
- Check your Discord token is correct
- Verify bot has message permissions in the channel
- Check bot is online in your Discord server
- Review console for error messages

### "Token is invalid"
- Regenerate token in Discord Developer Portal
- Update `.env` file
- Restart the bot

---

## Security Tips

1. **Never commit `.env` to version control** - add to `.gitignore`
2. **Use a strong RCON password** - treat like a password
3. **Restrict bot permissions** - only give it message permissions
4. **Limit channel access** - use role-based permissions
5. **Firewall RCON port** - only allow localhost or internal network
6. **Keep dependencies updated** - run `pip install --upgrade discord.py mcrcon`

---

## Customization Ideas

- Add channel restrictions (bot only works in specific channels)
- Add user role requirements (only admins can stop server)
- Add cooldowns to prevent spam
- Send notifications when server starts/stops
- Add player count polling
- Create a web dashboard alongside the bot

---

## Support

If you encounter issues:
1. Check console output for error messages
2. Verify all config values in `.env`
3. Test RCON manually: `mcrcon -H localhost -P 25575 -p your_password "list"`
4. Check Discord bot permissions and token validity
