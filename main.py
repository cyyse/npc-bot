import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
COG_FOLDER = "cogs"

async def load_cogs(bot):
    for filename in os.listdir(COG_FOLDER):
        print(filename)
        if filename.endswith(".py") and filename != "__init__.py":
            module = __import__(f"{COG_FOLDER}.{filename[:-3]}", fromlist=["setup"])
            await module.setup(bot)

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='~', intents=intents)

@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}!")

@bot.event
async def on_connect():
    await load_cogs(bot) # loads cogs when the bot connects

bot.run(TOKEN)