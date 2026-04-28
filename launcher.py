import subprocess
import time
import sys
import os
import json
import urllib.request
import zipfile
import shutil

REPO = "stachenuggets/potatobot"
CHECK_INTERVAL = 60
VERSION_FILE = ".current_release"
FILES_TO_UPDATE = ["minecraft_bot.py", "requirements.txt"]


def get_latest_release():
    url = f"https://api.github.com/repos/{REPO}/releases/latest"
    req = urllib.request.Request(url, headers={"User-Agent": "potatobot-launcher"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            return data.get("tag_name")
    except Exception as e:
        print(f"Failed to check for updates: {e}")
        return None


def get_current_version():
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE) as f:
            return f.read().strip()
    return None


def save_version(tag):
    with open(VERSION_FILE, "w") as f:
        f.write(tag)


def download_file(tag, filename):
    url = f"https://raw.githubusercontent.com/{REPO}/refs/tags/{tag}/{filename}"
    req = urllib.request.Request(url, headers={"User-Agent": "potatobot-launcher"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            content = r.read()
        with open(filename, "wb") as f:
            f.write(content)
        print(f"Updated {filename}")
    except Exception as e:
        print(f"Failed to download {filename}: {e}")


def pull_release(tag):
    print(f"Pulling release {tag}...")
    for f in FILES_TO_UPDATE:
        download_file(tag, f)
    save_version(tag)
    print(f"Now on release {tag}")


def install_requirements():
    python = sys.executable
    result = subprocess.run(
        [python, "-m", "pip", "install", "-r", "requirements.txt", "-q"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"pip error: {result.stderr.strip()}")


def start_bot():
    return subprocess.Popen([sys.executable, "minecraft_bot.py"])


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    latest = get_latest_release()
    current = get_current_version()

    if latest and latest != current:
        pull_release(latest)
        install_requirements()
    else:
        print(f"Running release {current or 'unknown'}")

    bot = start_bot()
    print("Bot started.")

    last_check = time.time()

    while True:
        time.sleep(5)

        if bot.poll() is not None:
            print("Bot crashed, restarting...")
            bot = start_bot()

        if time.time() - last_check >= CHECK_INTERVAL:
            last_check = time.time()
            latest = get_latest_release()
            if latest and latest != get_current_version():
                print(f"New release {latest} found, updating...")
                bot.terminate()
                bot.wait()
                pull_release(latest)
                install_requirements()
                bot = start_bot()
                print(f"Bot restarted on release {latest}.")


if __name__ == "__main__":
    main()
