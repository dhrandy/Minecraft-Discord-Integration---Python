# Minecraft-Discord-Integration---Python

## Crafty Player Monitor

### Real-Time Minecraft Server Activity and Achievement Tracker

**Crafty Player Monitor** is a Python-based log watcher for Minecraft servers managed through [Crafty Controller](https://craftycontrol.com/). It monitors player activity in real-time by reading the server’s `latest.log` file and sends rich Discord notifications via webhooks for key events and achievements.

---

## Features

### Real-Time Notifications

* Join/Leave Alerts: Notifies when players join or leave the server with timestamps and session durations.
* Death Detection: Sends death messages including cause (e.g., fall, fire, creeper).
* Custom Achievements: Recognizes and announces gameplay, behavioral, and milestone achievements.

### Supported Achievements

Organized by category:

* Gameplay-Based

  * One and Done – Logs in and leaves within 1 minute.
  * Deep Digger – Online for 2+ hours in one session.
  * World Traveler – First login after 30+ days.
  * Marathon Miner – 4+ hours online in one go.
  * Idle King – No activity for 20+ minutes.
  * Streaker – Logged in 5 days in a row.

* Death-Related

  * Death Magnet – 10 deaths in one day.
  * Hardcore Moment – Dies within 1 minute of joining.
  * Kaboom! – Creeper explosion.
  * Just Keep Dying – Drowns.
  * Gravity Hurts – Fall damage.
  * Crispy Steve – Burned to death.

* Behavior-Based

  * Chatty Crafter – 50+ messages in one session.
  * Silent Type – No chat in a 1+ hour session.
  * DJ – Uses `/say` command (if enabled).

* Milestones

  * First Blood – First death of the day.
  * Day One OG – Joined on the first server day.
  * 100th Login – Self-explanatory.
  * Level Up – First to join after a version update.
  * Party Time – 5+ players online.
  * Watcher – 2 hours online, no deaths or chat.

### Data Tracking

* Stores player statistics in a local JSON file named `player_data.json` (or as configured).
* Tracks logins, deaths, chat activity, login streaks, and more.

### Discord Rich Embeds

* Color-coded embeds by event type (join/leave/death/achievement).
* Includes timestamps, icons, and dynamic messages.
* Can use separate webhooks for achievements.

### Crash Resilience

* Automatically restarts if the script crashes or exits unexpectedly.

---

## Usage

1. Place the `mc_discord_notifier.py` script inside your Crafty Controller server directory where the `latest.log` file is located, so it can monitor the correct log.
2. Ensure the JSON data file (default `player_data.json`) will be created or is writable in the same directory. This file stores player stats and progress.
3. Edit the script’s configuration section to add your Discord webhook URLs.
4. Run the script using the included `.bat` file (on Windows) or directly via Python on Linux.
5. Optionally, configure it to launch automatically on system startup for continuous monitoring.
6. Monitor your Discord server for live notifications of player events and achievements.

---

## Future Plans

* AFK detection
* Cross-server milestone tracking
* Live GUI stats dashboard

---

## License

MIT – free to use and modify.
