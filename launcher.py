import subprocess
import time
import sys
import os

CHECK_INTERVAL = 60  # seconds between update checks

def run(cmd, **kwargs):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, **kwargs)

def has_update():
    run("git fetch origin")
    result = run("git rev-parse HEAD")
    local = result.stdout.strip()
    result = run("git rev-parse origin/main")
    remote = result.stdout.strip()
    return local != remote

def pull_update():
    run("git pull origin main")
    run("pip install -r requirements.txt")

def start_bot():
    return subprocess.Popen([sys.executable, "minecraft_bot.py"])

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    pull_update()

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
            if has_update():
                print("Update found, pulling and restarting...")
                bot.terminate()
                bot.wait()
                pull_update()
                bot = start_bot()
                print("Bot restarted with updates.")

if __name__ == "__main__":
    main()
