import os
import sys
import logging
import time

import nextcord
from nextcord.ext import commands
from dotenv import load_dotenv
import yaml

from src.utils import mojang, format
from src.tierlistQueue import TierlistQueue
from src.ui.waitlistButton import WaitlistButton
from src.database import sqlite
from src.utils.loadConfig import *


try:
    os.makedirs("logs", exist_ok=True)
    os.makedirs("storage", exist_ok=True)
except Exception as e:
    print(f"Uanble to create logs/storage directory: ", e)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s:%(levelname)s:%(name)s: %(message)s",
        handlers=[
        logging.FileHandler(f"logs/logs-{time.time()}.log")  # This logs to a file
    ]
)

load_dotenv()

intents = nextcord.Intents.all()
bot = commands.Bot(intents=intents)


try:
    queue = TierlistQueue(maxQueue=maxQueue, maxTesters=maxTester, cooldown=cooldown)
    queue.setup(listRegions)

except Exception as e:
    logging.exception(f"Setting up queue failed:")
    sys.exit("Error: Failed to setup queue")

def is_me(m):
    return m.author == bot.user

async def setupBot():
    await sqlite.createTables()
    await bot.get_channel(channels["enterWaitlist"]).purge(limit=10, check=is_me)
    await bot.get_channel(channels["enterWaitlist"]).send(embed=nextcord.Embed.from_dict(format.enterwaitlistmessage), view=WaitlistButton())
    
@bot.event
async def on_ready():
    print(f"Tier Testing bot has logged online ✅")
    try:
        await setupBot()
    except Exception as e:
        logging.exception("Failed bot startup sequence: ")
        sys.exit("Failed startup sequence")

@bot.slash_command(name="results", description="closes a ticket and gives a tier to a user") #TODO add database and ticket close
async def results(
    interaction: nextcord.Interaction,
    username: str = nextcord.SlashOption(
        description="Enter their username",
        required=True,
    ),
    user: nextcord.User = nextcord.SlashOption(
        description="Enter their discord account",
        required=True,
    ),
    newtier: str = nextcord.SlashOption(
        description="Enter their new tier",
        required=True,
        choices=listTiers
    ),
    oldtier: str = nextcord.SlashOption(
        description="Enter their old tier",
        required=True,
        choices=listTiers
    ),
    region: str = nextcord.SlashOption(
        description="Enter their region",
        required=True,
        choices=listRegionsText
    )
    ):
    try:
        if testerRole not in [role.id for role in interaction.user.roles]: await interaction.response.send_message(messages["noPermission"], ephemeral=True); return
        if interaction.channel.category.id not in listRegions: await interaction.response.send_message(messages["notTicketCatagory"], ephemeral=True); return

        uuid = await mojang.getuserid(username=username)

        result_embed_data = format.formatresult(discordUsername=user.name, testerID=interaction.user.id, region=region, minecraftUsername=username, oldTier=oldtier, newTier=newtier, uuid=uuid) # such bad practice <3
        embed = nextcord.Embed.from_dict(result_embed_data)
        
        await bot.get_channel(channels["results"]).send(content=f"<@{user.id}>" ,embed=embed)
        await interaction.response.send_message(content=messages["resultMessageSent"], ephemeral=True)
    except Exception as e:
        logging.exception("Error in /results command:")
        await interaction.response.send_message(content=messages["error"], ephemeral=True)

if __name__ == "__main__":
    bot.run(os.getenv("TOKEN"))