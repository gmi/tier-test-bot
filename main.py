import os
import sys
import logging
import time
import asyncio

import nextcord
from nextcord.ext import commands, tasks
from dotenv import load_dotenv

from src.utils import mojang, format
from src.tierlistQueue import TierlistQueue
from src.ui.waitlistButton import WaitlistButton
from src.ui.enterQueueButton import EnterQueueButton
from src.ui.closeTicketButton import CloseTicketButton
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

@tasks.loop(seconds=reloadQueue)
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
    user: nextcord.User = nextcord.SlashOption(
        description="Enter their discord account",
        required=True,
    ),
    newtier: str = nextcord.SlashOption(
        description="Enter their new tier",
        required=True,
        choices=listTiers
    )
    ):
    try:
        if testerRole not in [role.id for role in interaction.user.roles]: await interaction.response.send_message(messages["noPermission"], ephemeral=True); return
        if interaction.channel.category.id not in listRegionCategories: await interaction.response.send_message(messages["notTicketCatagory"], ephemeral=True); return
        
        exists = await sqlite.userExists(user.id)
        if not exists: await interaction.response.send_message("User does not exist in the database", ephemeral=True); return

        username, oldtier, region = await sqlite.getResultInfo(user.id)

        uuid = await mojang.getuserid(username=username)

        result_embed_data = format.formatresult(discordUsername=user.name, testerID=interaction.user.id, region=region, minecraftUsername=username, oldTier=oldtier, newTier=newtier, uuid=uuid) # such bad practice <3
        embed = nextcord.Embed.from_dict(result_embed_data)



        await sqlite.addResult(discordID=user.id, tier=newtier)


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

@bot.slash_command(name="next", description="gets the next user you want to test")
async def next(
    interaction: nextcord.Interaction,
    region: str = nextcord.SlashOption(
        description="Enter region",
        required=True,
        choices=listRegionsText
    )
    ):
    try:
        if testerRole not in [role.id for role in interaction.user.roles]: await interaction.response.send_message(messages["noPermission"], ephemeral=True); return
        user = queue.getNextTest(testerID=interaction.user.id, region=region)
        if user[0] == None: await interaction.response.send_message(content=user[1], ephemeral=True); return

        user: nextcord.User = await bot.fetch_user(user[0])

        channelID = await interaction.guild.create_text_channel(category=interaction.guild.get_channel(listRegions[region]["ticket_catagory"]), name=f"eval-{user.name}") # i dont like discord
        messageData = await sqlite.getUserTicket(user.id)
        ticketMessage = format.formatticketmessage(username=messageData[0], tier=messageData[1], server=messageData[2], uuid=messageData[3])

        await channelID.send(content=f"<@{user.id}>", embed=nextcord.Embed.from_dict(ticketMessage))
        await interaction.response.send_message(f"Ticket has been created: <#{channelID.id}>")
    except Exception as e:
        logging.exception("Error in /closequeue command:")
        await interaction.response.send_message(content=messages["error"], ephemeral=True)

@bot.slash_command(name="closetest", description="closes the current test")
async def closetest(
    interaction: nextcord.Interaction,
    ):
    try:
        if testerRole not in [role.id for role in interaction.user.roles]: await interaction.response.send_message(messages["noPermission"], ephemeral=True); return
        if (interaction.channel.category.id not in listRegionCategories) or interaction.channel.id in listRegionQueueChannel: await interaction.response.send_message(content="You cannot use this command in this channel", ephemeral=True); return
        
        view = CloseTicketButton()

        await interaction.response.send_message("Ticket will be closed in 10 seconds", view=view)
        await asyncio.sleep(10)
        if view.cancelled == False:
            await interaction.channel.delete(reason="Ticket channel closed by command.")
    except Exception as e:
        logging.exception("Error in /closetest command:")
        await interaction.response.send_message(content=messages["error"], ephemeral=True)

@bot.slash_command(name="forceclosetest", description="closes the current test with force")
async def forceclosetest(
    interaction: nextcord.Interaction,
    ):
    try:
        if testerRole not in [role.id for role in interaction.user.roles]: await interaction.response.send_message(messages["noPermission"], ephemeral=True); return
        if (interaction.channel.category.id not in listRegionCategories) or interaction.channel.id in listRegionQueueChannel: await interaction.response.send_message(content="You cannot use this command in this channel", ephemeral=True); return

        await interaction.response.send_message("Ticket will be closed in 10 seconds, cannot cancel")
        await asyncio.sleep(10)
        await interaction.channel.delete(reason="Ticket channel closed by command.")
    except Exception as e:
        logging.exception("Error in /forceclosetest command:")
        await interaction.response.send_message(content=messages["error"], ephemeral=True)

@bot.slash_command(name="updateusername", description="changes a username of a user")
async def updateusername(
    interaction: nextcord.Interaction,
    user: nextcord.User = nextcord.SlashOption(
        description="Enter their discord account",
        required=True,
    ),
    username: str = nextcord.SlashOption(
        description="Enter their minecraft username",
        required=True,
    )
    ):
    try:
        if testerRole not in [role.id for role in interaction.user.roles]: await interaction.response.send_message(content=messages["noPermission"], ephemeral=True); return
        exists = await sqlite.userExists(user.id)
        if not exists: await interaction.response.send_message("User does not exist in the database", ephemeral=True); return

        uuid = await mojang.getuserid(username=username)
        if uuid == "8667ba71b85a4004af54457a9734eed7": await interaction.response.send_message(content="Minecraft user does not exist"); return
        await sqlite.updateUsername(discordID=user.id, username=username, uuid=uuid)
        await interaction.response.send_message(content="Username sucessfully updated")
    except Exception as e:
        logging.exception("Error in /forceclosetest command:")
        await interaction.response.send_message(content=messages["error"], ephemeral=True)
    



if __name__ == "__main__":
    bot.run(os.getenv("TOKEN"))