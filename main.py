import os
import sys
import logging
import time
import datetime


import nextcord
from nextcord.ext import commands, tasks
from dotenv import load_dotenv

from src.utils import mojang, format
from src.tierlistQueue import TierlistQueue
from src.ui.waitlistButton import WaitlistButton
from src.ui.enterQueueButton import EnterQueueButton
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
    for region in listRegions:
        await bot.get_channel(listRegions[region]["queue_channel"]).purge(limit=10, check=is_me)
        await bot.get_channel(listRegions[region]["queue_channel"]).send(embed=nextcord.Embed.from_dict(format.formatnoqueue()))
    
    
@bot.event
async def on_ready():
    print(f"Tier Testing bot has logged online ✅")
    try:
        await setupBot()
        updateQueue.start()
    except Exception as e:
        logging.exception("Failed bot startup sequence: ")
        sys.exit("Failed startup sequence")

@tasks.loop(seconds=30)
async def updateQueue():
    queues = queue.getqueueraw()
    for region, data in queues.items():
        if not data["open"]:
            continue

        messageID = data["queueMessage"]
        if messageID == None:
            continue
        channel = bot.get_channel(data["queueChannel"])
        message: nextcord.Message = await channel.fetch_message(messageID)
        messageUpdate = queue.makeQueueMessage(region=region)
        await message.edit(embed=nextcord.Embed.from_dict(messageUpdate))



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

@bot.slash_command(name="openqueue", description="opens a queue in a set region")
async def openqueue(
    interaction: nextcord.Interaction,
    region: str = nextcord.SlashOption(
        description="Enter region",
        required=True,
        choices=listRegionsText
    )
    ):
    try:
        response = queue.addTester(region=region , userID=interaction.user.id)

        if response[1] != "":
            await bot.get_channel(listRegions[region]["queue_channel"]).purge(limit=10, check=is_me)
            queueMessage: nextcord.Message = await bot.get_channel(listRegions[region]["queue_channel"]).send(content=f"<@&{listRegions[region]["role_ping"]}>", embed=nextcord.Embed.from_dict(response[1]), view=EnterQueueButton(queue=queue))
            queue.addQueueMessageId(region=region, messageID=queueMessage.id)
        await interaction.response.send_message(content=response[0], ephemeral=True)
    except Exception as e:
        logging.exception("Error in /openqueue command:")
        await interaction.response.send_message(content=messages["error"], ephemeral=True)

@bot.slash_command(name="closequeue", description="closes queue for a specific region")
async def closequeue(
    interaction: nextcord.Interaction,
    region: str = nextcord.SlashOption(
        description="Enter region",
        required=True,
        choices=listRegionsText
    )
    ):
    try:
        response = queue.removeTester(userID=interaction.user.id, region=region)
        if response == "Testing is closed": await interaction.response.send_message(content=response); return

        message_text, embed_data, channel_id, message_id = response

        queueChannel = bot.get_channel(channel_id)
        queueMessage = await queueChannel.fetch_message(message_id)

        if isinstance(embed_data, dict):
            if message_text == "testing has closed":
                await queueMessage.edit(embed=nextcord.Embed.from_dict(embed_data), view=None)
            else:
                await queueMessage.edit(embed=nextcord.Embed.from_dict(embed_data))
        else:
            logging.warning("Expected embed data to be a dict, got: %s", type(embed_data))
            await interaction.response.send_message("Something went wrong with formatting the queue embed.", ephemeral=True)
            return

        await interaction.response.send_message(content=message_text, ephemeral=True)
    except Exception as e:
        logging.exception("Error in /closequeue command:")
        await interaction.response.send_message(content=messages["error"], ephemeral=True)
    

if __name__ == "__main__":
    bot.run(os.getenv("TOKEN"))