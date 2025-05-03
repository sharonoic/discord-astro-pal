# AstroPal 🌌
A Discord bot that helps users explore real-time astronomical data — including planet visibility, moon phases, and more — based on city input.

## Features

- `/now`: Shows visible planets and Messier objects above 20° altitude in your location
- `/getlatlong`: Returns the latitude and longitude of a given city
- `/planet`: Reports current altitude and azimuth of a specified planet
- `/sun`: Shows sunrise and sunset times in your city
- `/moon`: Displays the moon’s visibility and current phase

## Setup

1. Clone the repo:
   ```
   git clone https://github.com/sharonoic/discord-astro-pal.git
   ```
2. Install required libraries:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory with your bot token:
   ```
   DISCORD_BOT_TOKEN=your_token_here
   ```
4. Run the bot:
   ```
   python main.py
   ```

## Requirements

- Python 3.10+
- `discord.py` (with `app_commands`)
- `skyfield`, `pytz`, `geopy`

## Author

Created by [@sharonoic](https://github.com/sharonoic)
