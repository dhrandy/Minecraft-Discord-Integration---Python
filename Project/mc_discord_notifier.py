import json
import time
from datetime import datetime, timedelta, timezone
import requests
import re
import os

# === CONFIG ===
# Replace hidden with your Discord Webhoook (right click on channel and select integration). Replace log path with your actual log path.
WEBHOOK_PLAYER_EVENTS = "hidden"
WEBHOOK_ACHIEVEMENTS = "hidden"
LOG_PATH = r"C:\Users\Name\Desktop\Crafty\servers\server\logs\latest.log"
DATA_FILE = "mc_player_data.json"

# Session & global tracking
SESSION_STARTS = {}
CURRENT_PLAYERS = set()
SERVER_START_DATE = datetime(2025, 1, 1, tzinfo=timezone.utc)  # Set your server start date here
LAST_MC_VERSION = "1.21.5"  # Update accordingly

# Regex patterns for events
JOIN_PATTERN = re.compile(r"\[.+\]: (.+) joined the game")
LEAVE_PATTERN = re.compile(r"\[.+\]: (.+) left the game")
DEATH_PATTERNS = {
    "Kaboom": re.compile(r".+ was blown up by Creeper"),
    "Drown": re.compile(r".+ drowned"),
    "Fall": re.compile(r".+ fell from a high place"),
    "Burn": re.compile(r".+ burned to death"),
    "Other": re.compile(r".+ died"),
}
CHAT_PATTERN = re.compile(r"\[.+\]: <(.+)> (.+)")
COMMAND_SAY_PATTERN = re.compile(r"\[.+\]: (.+) issued server command: /say")

# Load or init player data
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
else:
    data = {"players": {}, "daily": {"date": "", "first_death_done": False}}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def utcnow():
    return datetime.now(timezone.utc)

def send_discord_message(webhook_url, embed):
    try:
        requests.post(webhook_url, json={"embeds": [embed]})
    except Exception as e:
        print(f"Error sending discord message: {e}")

def format_embed(title, description, color=0x00ff00):
    return {
        "title": title,
        "description": description,
        "color": color,
        "timestamp": utcnow().isoformat(),
    }

def reset_daily_data_if_needed(player, now):
    pdata = data["players"].setdefault(player, {})
    today_str = now.date().isoformat()
    if pdata.get("daily_date") != today_str:
        pdata["daily_date"] = today_str
        pdata["daily_play_seconds"] = 0
        pdata["deaths_today"] = 0

def check_global_daily_reset():
    today_str = utcnow().date().isoformat()
    if data["daily"].get("date") != today_str:
        data["daily"]["date"] = today_str
        data["daily"]["first_death_done"] = False
        for p in data["players"].values():
            p["deaths_today"] = 0
            p["daily_play_seconds"] = 0
        save_data()
        print(f"Global daily data reset for {today_str}")

def player_joined(player):
    now = utcnow()
    reset_daily_data_if_needed(player, now)
    CURRENT_PLAYERS.add(player)
    SESSION_STARTS[player] = now
    pdata = data["players"].setdefault(player, {
        "joins": 0,
        "last_login": None,
        "last_logout": None,
        "deaths_today": 0,
        "total_deaths": 0,
        "chat_count": 0,
        "achievements": {},
        "login_streak": 0,
        "last_login_date": None,
        "total_play_seconds": 0,
        "daily_play_seconds": 0,
        "daily_date": None,
        "last_version_login": None,
        "last_activity": now.isoformat(),
    })

    # Update join count and streak logic
    last_login_date = pdata["last_login_date"]
    today = now.date()
    if last_login_date:
        last_date = datetime.fromisoformat(last_login_date).date()
        if (today - last_date).days == 1:
            pdata["login_streak"] += 1
        elif (today - last_date).days > 1:
            pdata["login_streak"] = 1
    else:
        pdata["login_streak"] = 1

    # World Traveler: first login after 30+ days inactivity
    if pdata["last_login"]:
        last_login_dt = datetime.fromisoformat(pdata["last_login"])
        if (now - last_login_dt).days >= 30 and "World Traveler" not in pdata["achievements"]:
            unlock_achievement(player, "🌍 World Traveler", "Welcome back after a long time!")

    # Day One OG
    if now.date() == SERVER_START_DATE.date() and "Day One OG" not in pdata["achievements"]:
        unlock_achievement(player, "👋 Day One OG", "You were here from day one!")

    # 100th Login
    pdata["joins"] += 1
    if pdata["joins"] == 100 and "100th Login" not in pdata["achievements"]:
        unlock_achievement(player, "🎉 100th Login", "Wow! 100 visits!")

    # Level Up - first login after Minecraft version update (simplified)
    if pdata["last_version_login"] != LAST_MC_VERSION:
        pdata["last_version_login"] = LAST_MC_VERSION
        unlock_achievement(player, "📈 Level Up", f"Welcome to Minecraft {LAST_MC_VERSION}!")

    pdata["last_login"] = now.isoformat()
    pdata["last_login_date"] = now.isoformat()

    # Send join message
    embed = format_embed("Player Joined", f"🔹 Player **{player}** has joined the world.", color=0x00ff00)
    send_discord_message(WEBHOOK_PLAYER_EVENTS, embed)
    save_data()

def player_left(player):
    now = utcnow()
    if player not in SESSION_STARTS:
        return  # no session data

    CURRENT_PLAYERS.discard(player)
    pdata = data["players"].get(player)
    if not pdata:
        return

    start = SESSION_STARTS[player]
    session_length = (now - start).total_seconds()
    pdata["total_play_seconds"] += session_length

    # Update daily play seconds too (initialize if needed)
    pdata["daily_play_seconds"] = pdata.get("daily_play_seconds", 0) + session_length

    # One and Done: leave within 1 min
    if session_length < 60 and "One and Done" not in pdata["achievements"]:
        unlock_achievement(player, "🎯 One and Done", "Logged in and left quickly.")

    # Deep Digger: 2+ hours
    if session_length >= 2*3600 and "Deep Digger" not in pdata["achievements"]:
        unlock_achievement(player, "⛏️ Deep Digger", "Played 2+ hours in one session.")

    # Marathon Miner: 4+ hours
    if session_length >= 4*3600 and "Marathon Miner" not in pdata["achievements"]:
        unlock_achievement(player, "🔥 Marathon Miner", "Played 4+ hours in one session.")

    # Streaker: 5 days in a row
    if pdata["login_streak"] >= 5 and "Streaker" not in pdata["achievements"]:
        unlock_achievement(player, "📆 Streaker", "Logged in 5 days in a row!")

    # Watcher: 2 hours no deaths or chat (simplified check)
    if session_length >= 2*3600 and pdata["chat_count"] == 0 and pdata["deaths_today"] == 0:
        unlock_achievement(player, "👀 Watcher", "2 hours online with no deaths or chat.")

    pdata["last_logout"] = now.isoformat()
    pdata["chat_count"] = 0  # reset chat count per session

    # Format session length
    hrs, rem = divmod(session_length, 3600)
    mins, secs = divmod(rem, 60)
    session_str = f"{int(hrs)}h {int(mins)}m {int(secs)}s"

    # Format daily play length
    daily_seconds = pdata.get("daily_play_seconds", 0)
    d_hrs, d_rem = divmod(daily_seconds, 3600)
    d_mins, d_secs = divmod(d_rem, 60)
    daily_str = f"{int(d_hrs)}h {int(d_mins)}m {int(d_secs)}s"

    embed = format_embed(
        "Player Left",
        f"🔹 Player **{player}** left the world.\n"
        f"Session length: {session_str}\n"
        f"Total playtime today: {daily_str}",
        color=0xffa500
    )
    send_discord_message(WEBHOOK_PLAYER_EVENTS, embed)
    save_data()
    SESSION_STARTS.pop(player, None)

def unlock_achievement(player, title, desc):
    pdata = data["players"].setdefault(player, {"achievements": {}})
    if title in pdata["achievements"]:
        return
    pdata["achievements"][title] = {"unlocked": utcnow().isoformat()}
    embed = format_embed(f"Achievement Unlocked! {title}", f"Player **{player}**: {desc}", color=0xFFD700)
    send_discord_message(WEBHOOK_ACHIEVEMENTS, embed)
    save_data()

def process_death(line):
    for cause, pattern in DEATH_PATTERNS.items():
        if pattern.search(line):
            player = extract_player_from_death(line)
            if not player:
                return
            pdata = data["players"].setdefault(player, {"deaths_today": 0, "achievements": {}})
            pdata["total_deaths"] = pdata.get("total_deaths", 0) + 1

            # Use global daily reset check to keep date current, but double check here
            today_str = utcnow().date().isoformat()
            if data["daily"].get("date") != today_str:
                data["daily"]["date"] = today_str
                data["daily"]["first_death_done"] = False
                for p in data["players"].values():
                    p["deaths_today"] = 0
                    p["daily_play_seconds"] = 0
                save_data()

            pdata["deaths_today"] = pdata.get("deaths_today", 0) + 1
            if pdata["deaths_today"] >= 10 and "🪦 Death Magnet" not in pdata["achievements"]:
                unlock_achievement(player, "🪦 Death Magnet", "10 deaths in one day!")

            if not data["daily"]["first_death_done"]:
                unlock_achievement(player, "🏆 First Blood", "First death on the server today!")
                data["daily"]["first_death_done"] = True

            session_start = SESSION_STARTS.get(player)
            if session_start:
                seconds_in = (utcnow() - session_start).total_seconds()
                if seconds_in < 60 and "🚫 Hardcore Moment" not in pdata["achievements"]:
                    unlock_achievement(player, "🚫 Hardcore Moment", "Died immediately after joining.")

            if cause == "Kaboom" and "💥 Kaboom!" not in pdata["achievements"]:
                unlock_achievement(player, "💥 Kaboom!", "Blown up by a creeper!")
            elif cause == "Drown" and "🌊 Just Keep Dying" not in pdata["achievements"]:
                unlock_achievement(player, "🌊 Just Keep Dying", "Drowned.")
            elif cause == "Fall" and "☄️ Gravity Hurts" not in pdata["achievements"]:
                unlock_achievement(player, "☄️ Gravity Hurts", "Death by fall.")
            elif cause == "Burn" and "🔥 Crispy Steve" not in pdata["achievements"]:
                unlock_achievement(player, "🔥 Crispy Steve", "Burned to death.")

            break

def extract_player_from_death(line):
    m = re.match(r"\[.+\]: (\w+) ", line)
    if m:
        return m.group(1)
    return None

def process_chat(line):
    m = CHAT_PATTERN.match(line)
    if m:
        player, message = m.groups()
        pdata = data["players"].setdefault(player, {"chat_count": 0, "achievements": {}})
        pdata["chat_count"] = pdata.get("chat_count", 0) + 1
        pdata["last_activity"] = utcnow().isoformat()

        if pdata["chat_count"] >= 50 and "🗣️ Chatty Crafter" not in pdata["achievements"]:
            unlock_achievement(player, "🗣️ Chatty Crafter", "Sent 50+ chat messages in a session!")

        if message.startswith("/say") and "🎤 DJ" not in pdata["achievements"]:
            unlock_achievement(player, "🎤 DJ", "Used /say command!")

def check_idle():
    now = utcnow()
    for player in CURRENT_PLAYERS:
        pdata = data["players"].get(player)
        if not pdata:
            continue
        last_activity = pdata.get("last_activity")
        if last_activity:
            last_act_time = datetime.fromisoformat(last_activity)
            if (now - last_act_time) > timedelta(minutes=20):
                if "💤 Idle King" not in pdata["achievements"]:
                    unlock_achievement(player, "💤 Idle King", "No chat or action for 20+ minutes!")

def check_party_time():
    if len(CURRENT_PLAYERS) >= 5:
        for player in CURRENT_PLAYERS:
            pdata = data["players"].get(player)
            if pdata and "👥 Party Time" not in pdata["achievements"]:
                unlock_achievement(player, "👥 Party Time", "5 or more players online simultaneously!")

def monitor_log():
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        f.seek(0, os.SEEK_END)
        while True:
            check_global_daily_reset()

            line = f.readline()
            if not line:
                time.sleep(1)
                continue

            if JOIN_PATTERN.search(line):
                player = JOIN_PATTERN.findall(line)[0]
                player_joined(player)

            elif LEAVE_PATTERN.search(line):
                player = LEAVE_PATTERN.findall(line)[0]
                player_left(player)

            else:
                for pattern in DEATH_PATTERNS.values():
                    if pattern.search(line):
                        process_death(line)
                        break
                else:
                    if CHAT_PATTERN.search(line):
                        process_chat(line)

            check_idle()
            check_party_time()

if __name__ == "__main__":
    monitor_log()
