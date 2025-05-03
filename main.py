# === Imports ===

import discord
from discord.ext import commands
from discord import app_commands
from skyfield.api import load, Topos, Star
from skyfield import almanac 
from datetime import datetime, timedelta, timezone
import pytz
import os
from geopy.geocoders import Nominatim

# === Configuration ===

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
print(f"🔍 TOKEN VALUE: {repr(TOKEN)}")

if not TOKEN:
    raise ValueError("❌ DISCORD_BOT_TOKEN is missing. Check .env or Render env tab.")

DEFAULT_LAT, DEFAULT_LON = 49.2827, -123.1207 # vancouver
TIMEZONE = "America/Vancouver"

# === Bot Setup === 

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# === Events ===

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"Failed to sync: {e}")

# === Commands ===

# /now

@bot.tree.command(name="now", description="Show celestial highlights visible now")
@app_commands.describe(location="City name (currently placeholder)")
async def now(interaction: discord.Interaction, location: str = "Vancouver"):
    await interaction.response.defer()
    
    result = getlocation(location)

    if result is False:
        await interaction.followup.send(f"❌ Could not find location: {location}")
        return
    
    obs, now, t0, t1, ts, location_obj, eph, observer, lat, lon = result
    
    planets = {
    'Moon': eph['moon'],                    # mag ~ -12.7
    'Venus': eph['venus'],                  # mag ~ -4.6
    'Jupiter': eph['jupiter barycenter'],   # mag ~ -2.9
    'Mars': eph['mars'],                    # mag ~ -2.0
    'Mercury': eph['mercury'],              # mag ~ -1.9
    'Saturn': eph['saturn barycenter'],     # mag ~ 0.7
    'Uranus': eph['uranus barycenter'],     # mag ~ 5.6
    'Neptune': eph['neptune barycenter'],   # mag ~ 7.8
    }

    messier_objects = {
    "M1 Crab Nebula": {"ra": (5, 34, 31),  "dec": (22, 0, 52)},
    "M5 Globular Cluster": {"ra": (15, 18, 33), "dec": (2, 4, 51)},
    "M8 Lagoon Nebula": {"ra": (18, 3, 37),  "dec": (-24, 23, 12)},
    "M13 Hercules Cluster": {"ra": (16, 41, 41), "dec": (36, 27, 36)},
    "M27 Dumbbell Nebula": {"ra": (19, 59, 36), "dec": (22, 43, 16)},
    "M31 Andromeda Galaxy": {"ra": (0, 42, 44),  "dec": (41, 16, 9)},
    "M33 Triangulum Galaxy": {"ra": (1, 33, 51),  "dec": (30, 39, 36)},
    "M42 Orion Nebula": {"ra": (5, 35, 17),  "dec": (-5, 23, 28)},
    "M44 Beehive Cluster": {"ra": (8, 40, 24),  "dec": (19, 40, 0)},
    "M45 Pleiades": {"ra": (3, 47, 24),  "dec": (24, 7, 0)},
    "M57 Ring Nebula": {"ra": (18, 53, 35), "dec": (33, 1, 45)},
    "M81 Bode's Galaxy": {"ra": (9, 55, 33),  "dec": (69, 3, 55)},
    "M82 Cigar Galaxy": {"ra": (9, 55, 52),  "dec": (69, 40, 47)},
    "M101 Pinwheel Galaxy": {"ra": (14, 3, 12),  "dec": (54, 20, 56)},
    "M104 Sombrero Galaxy": {"ra": (12, 39, 59), "dec": (-11, 37, 23)}
    }

    visible = []

    for name, body in planets.items():
        astrometric = obs.at(t0).observe(body)
        alt, az, _ = astrometric.apparent().altaz()
        if alt.degrees > 20: # added to visible list if alt > 20
            visible.append(f"🪐 **{name}** (alt: {alt.degrees:.1f}°)")

    for name, coords in messier_objects.items():
        star = Star(ra_hours=coords["ra"], dec_degrees=coords["dec"])
        astrometric = obs.at(t0).observe(star)
        alt, az, _ = astrometric.apparent().altaz()
        if alt.degrees > 20:
            visible.append(f"✨ {name} (alt: {alt.degrees:.1f}°)")

    embed = discord.Embed(
        title=f"Tonight’s Sky – {location}",
        description=f"Time: {now.strftime('%Y-%m-%d %H:%M %Z')}",
        color=discord.Color.dark_blue()
    )

    if visible and is_astronomical_night:
        embed.add_field(name="Visible Objects (Planets and Messier Objects with Magnitude < 10.5 above 20° altitude):", value="\n".join(visible), inline=False)
    elif visible and not is_astronomical_night:
        embed.add_field(
        name="Visible Objects (Planets and Messier Objects with Magnitude < 10.5 above 20° altitude):",
        value="\n".join(visible) + "\n\n🔎 *Note: Some objects may not be visible due to sky brightness or twilight conditions.*",
        inline=False
        )
    else:
        embed.description += "No major objects visible tonight above 20° altitude."

    await interaction.followup.send(embed=embed)

# /getlatlong

@bot.tree.command(name="getlatlong", description="Show latitude and longtitude of a location")
@app_commands.describe(location="City name (currently placeholder)")
async def getlatlong(interaction: discord.Interaction, location: str = "Vancouver"):
    await interaction.response.defer()

    if result is False:
        await interaction.followup.send(f"❌ Could not find location: {location}")
        return
    
    obs, now, t0, t1, ts, location_obj, eph, observer, lat, lon = result

    def decimal_to_dms(deg: float, is_lat: bool) -> str:
        direction = ""
        if is_lat:
            direction = "N" if deg >= 0 else "S"
        else:
            direction = "E" if deg >= 0 else "W"

        abs_deg = abs(deg)
        degrees = int(abs_deg)
        minutes_float = (abs_deg - degrees) * 60
        minutes = int(minutes_float)
        seconds = (minutes_float - minutes) * 60

        return f"{degrees}°{minutes}'{seconds:.2f}\" {direction}"

    result = getlocation(location)

    lat_dms = decimal_to_dms(lat, is_lat=True)
    lon_dms = decimal_to_dms(lon, is_lat=False)

    embed = discord.Embed(
    title=f"Coordinates for {location}",
    color=discord.Color.orange()
    )

    embed.description = f"🌍 Latitude of {location} is {lat:.4f}° | {lat_dms} \n"
    embed.description += f"🌐 Longitude of {location} is {lon:.4f}° | {lon_dms}"
    
    await interaction.followup.send(embed=embed)

# /planet

@bot.tree.command(name="planet", description="Show visibility and position of a planet in a given location now")
@app_commands.describe(planet = "Planet in Solar System", location="City name (currently placeholder)")
async def planet(interaction: discord.Interaction, planet: str = "Mars", location: str = "Vancouver"):
    await interaction.response.defer()
    
    result = getlocation(location)

    if result is False:
        await interaction.followup.send(f"❌ Could not find location: {location}")
        return
    
    obs, now, t0, t1, ts, location_obj, eph, observer, lat, lon = result
    
    # check object's altitude
    planets = {               
    'Venus': eph['venus'],                  # mag ~ -4.6
    'Jupiter': eph['jupiter barycenter'],   # mag ~ -2.9
    'Mars': eph['mars'],                    # mag ~ -2.0
    'Mercury': eph['mercury'],              # mag ~ -1.9
    'Saturn': eph['saturn barycenter'],     # mag ~ 0.7
    'Uranus': eph['uranus barycenter'],     # mag ~ 5.6
    'Neptune': eph['neptune barycenter'],   # mag ~ 7.8
    }

    planet_name = planet.title()

    if planet_name in planets:
        body = planets[planet_name]
        astrometric = obs.at(t0).observe(body)
        alt, az, _ = astrometric.apparent().altaz()

        if alt.degrees > 20 and is_astronomical_night(location):
            await interaction.followup.send(
            f"🔭 {planet_name} is visible in {location} now, currently at:\n"
            f"📍 Altitude: `{alt.degrees:.2f}°`\n"
            f"🧭 Azimuth: `{az.degrees:.2f}°`"
            )
        elif alt.degrees > 20 and not is_astronomical_night(location):
            await interaction.followup.send(
            f"🔭 {planet_name} is up in {location} now, currently at:\n"
            f"📍 Altitude: `{alt.degrees:.2f}°`\n"
            f"🧭 Azimuth: `{az.degrees:.2f}°` \n"
            f"🔎 *Note: {planet_name} may not be visible due to sky brightness or twilight conditions.*"

            )
        else:
            await interaction.followup.send(
            f"🔭 {planet_name} is not visible in {location} now, currently at:\n"
            f"📍 Altitude: `{alt.degrees:.2f}°`\n"
            f"🧭 Azimuth: `{az.degrees:.2f}°`"
            )

    else:
        await interaction.followup.send(f"❌ `{planet}` is not a recognized planet.")


# /sun

@bot.tree.command(name="sun", description="Show sunrise and sunset in a given location now")
@app_commands.describe(location="City name (currently placeholder)")
async def sun(interaction: discord.Interaction,location: str = "Vancouver"):
    await interaction.response.defer()

    output_lines = []

    result = getlocation(location)
    
    if result is False:
        await interaction.followup.send(f"❌ Could not find location: {location}")
        return

    obs, now, t0, t1, ts, location_obj, eph, observer, lat, lon = result

    f = almanac.sunrise_sunset(eph, observer)
    times, events = almanac.find_discrete(t0, t1, f)

    for t, e in zip(times, events):
        label = "🌅 Sunrise" if e == 0 else "🌇 Sunset"
        output_lines.append(f"{label}: `{t.utc_datetime().strftime('%Y-%m-%d %H:%M UTC')}`")

    embed = discord.Embed(
        title=f"Sunrise and Sunset in {location.title()}",
        description="\n".join(output_lines),
        color=discord.Color.yellow()
    )
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="moon", description="Show information of the Moon in a given location now")
@app_commands.describe(location="City name (currently placeholder)")
async def moon(interaction: discord.Interaction,location: str = "Vancouver"):
    await interaction.response.defer()

    output_lines = []

    result = getlocation(location)
    
    if result is False:
        await interaction.followup.send(f"❌ Could not find location: {location}")
        return

    obs, now, t0, t1, ts, location_obj, eph, observer, lat, lon = result

    sun = eph['sun']
    moon = eph['moon']
    astrometric_moon = obs.at(t0).observe(moon).apparent()
    
    astrometric_sun = obs.at(t0).observe(sun).apparent()
    phase_angle = astrometric_moon.separation_from(astrometric_sun).degrees 

    if phase_angle < 45:
        phase_name = "New Moon to Waxing Crescent"
    elif phase_angle < 90:
        phase_name = "First Quarter"
    elif phase_angle < 135:
        phase_name = "Waxing Gibbous"
    elif phase_angle < 180:
        phase_name = "Full Moon"
    elif phase_angle < 225:
        phase_name = "Waning Gibbous"
    elif phase_angle < 270:
        phase_name = "Last Quarter"
    else:
        phase_name = "Waning Crescent"

    alt, az, _ = astrometric_moon.altaz()
    if alt.degrees > 20: # true if alt > 20
        output_lines.append(f"The Moon is visible now!")
    else:
        output_lines.append(f"The Moon is currently below the horizon")

    output_lines.append(f"🌙 Current Moon Phase is {phase_name}")

    embed = discord.Embed(
        title=f"The Moon Now in {location.title()}",
        description="\n".join(output_lines),
        color=discord.Color.blue()
    )
    
    await interaction.followup.send(embed=embed)


#  === Helper Functions ===

# get_location

def getlocation(location):

    ts = load.timescale()
    eph = load('de421.bsp')

    # geocode location

    geolocator = Nominatim(user_agent="astropal_bot")
    location_obj = geolocator.geocode(location)

    if location_obj is None:
        return False
    
    lat = location_obj.latitude
    lon = location_obj.longitude

    observer = Topos(latitude_degrees=lat, longitude_degrees=lon)
    
    # gets current local time in Vancouver and converts it to Skyfield format
    now = datetime.now(pytz.timezone(TIMEZONE)) 
    t0 = ts.from_datetime(now)
    t1 = ts.utc(now + timedelta(days=1))
    obs = eph['earth'] + observer

    return obs, now, t0, t1, ts, location_obj, eph, observer, lat, lon

# is_astronomical_night

def is_astronomical_night(location: str) -> bool:
    try:
        result = getlocation(location)
        obs, now, t0, t1, ts, location_obj, eph, observer, lat, lon = result
        geolocator = Nominatim(user_agent="astropal_bot")
        loc = geolocator.geocode(location)
        
        if not loc:
            print(f"Could not geocode location: {location}")
            return False

        lat, lon = loc.latitude, loc.longitude

        now = datetime.now(timezone.utc)
        t_now = ts.utc(now)
        sun = eph['sun']
        astrometric = obs.at(t_now).observe(sun)
        alt, _, _ = astrometric.apparent().altaz()

        return alt.degrees < -18

    except Exception as e:
        print(f"Error checking night status: {e}")
        return False


bot.run(TOKEN)
