# bot.py

import os
import json
import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ui import View, Button
from dotenv import load_dotenv
from datetime import datetime, time

# ------------------------
# Load environment variables
# ------------------------
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# Replace with your server (guild) ID
GUILD_ID = 1284305558509195325 # <-- REPLACE this with your server ID

# ------------------------
# Intents and bot setup
# ------------------------
intents = discord.Intents.default()
intents.message_content = True  # <- REQUIRED for Discord now

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree  # for slash commands
guild = discord.Object(id=GUILD_ID)


# ------------------------
# Helper functions
# ------------------------
def load_scores():
    if not os.path.exists("scores.json"):
        return {}
    with open("scores.json", "r") as f:
        return json.load(f)

def save_scores(scores):
    with open("scores.json", "w") as f:
        json.dump(scores, f, indent=4)

# ------------------------
# Slash Commands (Guild-Specific)
# ------------------------
@tree.command(name="osrsguessr", description="Get the daily OSRSGuessr link", guild=guild)
async def slash_osrsguessr(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎮 OSRSGuessr – Guess the Location!",
        description="Click to start playing:",
        url="https://www.osrsguessr.com/",
        color=0x1abc9c
    )
    await interaction.response.send_message(embed=embed)

@tree.command(name="score", description="Submit your OSRSGuessr score", guild=guild)
@app_commands.describe(points="Your score for today")
async def slash_score(interaction: discord.Interaction, points: int):
    user_id = str(interaction.user.id)
    username = interaction.user.name

    scores = load_scores()
    if user_id not in scores:
        scores[user_id] = {"name": username, "best": 0, "totalGames": 0, "today": None}

    user = scores[user_id]
    user["totalGames"] = user.get("totalGames", 0) + 1
    user["today"] = points
    if points > user.get("best", 0):
        user["best"] = points
    save_scores(scores)

    await interaction.response.send_message(
        f"✅ {username}, your score of **{points}** was recorded! (Best: {user['best']})"
    )

@tree.command(name="leaderboard", description="Show top 10 OSRSGuessr scores", guild=guild)
async def slash_leaderboard(interaction: discord.Interaction):
    scores = load_scores()
    if not scores:
        await interaction.response.send_message("No scores yet. Use `/score <points>` to submit a score.")
        return

    entries = list(scores.values())
    entries.sort(key=lambda s: s.get("best", 0), reverse=True)
    top = entries[:10]

    lines = []
    for i, s in enumerate(top, start=1):
        name = s.get("name", "Unknown")
        best = s.get("best", 0)
        games = s.get("totalGames", 0)
        lines.append(f"**{i}. {name}** — 🏅 {best} pts ({games} games)")

    embed = discord.Embed(title="🏆 OSRSGuessr Leaderboard", description="\n".join(lines), color=0xf1c40f)
    await interaction.response.send_message(embed=embed)

# ------------------------
# Daily OSRSGuessr Post with Button
# ------------------------
@tasks.loop(time=time(hour=12, minute=0))  # change hour/minute as needed
async def daily_post():
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        # Create clickable button
        button = Button(label="Play OSRSGuessr", url="https://www.osrsguessr.com/", style=discord.ButtonStyle.link)
        view = View()
        view.add_item(button)

        embed = discord.Embed(
            title="🎮 Daily OSRSGuessr",
            description="Click the button below to play today's OSRSGuessr!",
            color=0x1abc9c
        )

        await channel.send(embed=embed, view=view)

# ------------------------
# On Ready Event
# ------------------------
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    await tree.sync(guild=guild)  # sync commands to your server
    print("✅ Guild-specific slash commands synced!")
    daily_post.start()

# ------------------------
# Run the Bot
# ------------------------
bot.run(TOKEN)

