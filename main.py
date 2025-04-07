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
from src.database import databaseManager
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
    await databaseManager.createTables()
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



@bot.slash_command(name="results", description="closes a ticket and gives a tier to a user")
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
        
        exists = await databaseManager.userExists(user.id)
        if not exists: await interaction.response.send_message("User does not exist in the database", ephemeral=True); return
        
        isrestricted = await databaseManager.isRestriced(interaction.user.id)
        if isrestricted: await interaction.response.send_message(content="User is currently restricted", ephemeral=True); return

        restricted = await databaseManager.isRestriced(user.id)
        if restricted: await interaction.response.send_message("User is restricted", ephemeral=True); return

        username, oldtier, region = await databaseManager.getResultInfo(user.id)

        uuid = await mojang.getuserid(username=username)

        result_embed_data = format.formatresult(discordUsername=user.name, testerID=interaction.user.id, region=region, minecraftUsername=username, oldTier=oldtier, newTier=newtier, uuid=uuid) # such bad practice <3
        embed = nextcord.Embed.from_dict(result_embed_data)

        await databaseManager.addResult(discordID=user.id, tier=newtier)

        member = interaction.guild.get_member(user.id)
        region_roles_to_remove = [role for role in member.roles if role.id in listRegionRolePing]
        if region_roles_to_remove:
            await member.remove_roles(*region_roles_to_remove, reason="Region roles removed by /results command")

        tier_roles_to_remove = [role for role in member.roles if role.id in listTierRoles.values()]
        if tier_roles_to_remove:
            await member.remove_roles(*tier_roles_to_remove, reason="Old tier roles removed by /results command")
        
        if newtier != "none" and newtier in listTierRoles:
            new_tier_role = interaction.guild.get_role(listTierRoles[newtier])
            if new_tier_role:
                await member.add_roles(new_tier_role, reason="New tier role added by /results command")

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
        if interaction.user.id not in queue.queue[region]["testers"]: await interaction.response.send_message("You are not testing this region!", ephemeral=True); return
        user = queue.getNextTest(testerID=interaction.user.id, region=region)
        if user[0] == None: await interaction.response.send_message(content=user[1], ephemeral=True); return

        user: nextcord.Member = await interaction.guild.fetch_member(user[0])

        channelID = await interaction.guild.create_text_channel(category=interaction.guild.get_channel(listRegions[region]["ticket_catagory"]), name=f"eval-{user.name}") # i dont like discord
        overwrite = nextcord.PermissionOverwrite()
        overwrite.view_channel = True
        overwrite.send_messages = True
        await channelID.set_permissions(user, overwrite=overwrite)
        
        messageData = await databaseManager.getUserTicket(user.id)
        ticketMessage = format.formatticketmessage(username=messageData[0], tier=messageData[1], server=messageData[2], uuid=messageData[3])

        current_roles = user.roles
        role_ids_to_remove = [role.id for role in current_roles if role.id in [r["role_ping"] for r in listRegions.values()]]
        if role_ids_to_remove:
            await interaction.user.remove_roles(*[interaction.guild.get_role(role_id) for role_id in role_ids_to_remove])
            
        await channelID.send(content=f"<@{user.id}>", embed=nextcord.Embed.from_dict(ticketMessage))
        await interaction.response.send_message(f"Ticket has been created: <#{channelID.id}>", ephemeral=True)
    except Exception as e:
        logging.exception("Error in /next command:")
        print(e)
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
        exists = await databaseManager.userExists(user.id)
        if not exists: await interaction.response.send_message("User does not exist in the database", ephemeral=True); return

        uuid = await mojang.getuserid(username=username)
        if uuid == "8667ba71b85a4004af54457a9734eed7": await interaction.response.send_message(content="Minecraft user does not exist"); return
        await databaseManager.updateUsername(discordID=user.id, username=username, uuid=uuid)
        await interaction.response.send_message(content="Username sucessfully updated", ephemeral=True)
    except Exception as e:
        logging.exception("Error in /updateusername command:")
        await interaction.response.send_message(content=messages["error"], ephemeral=True)


@bot.slash_command(name="updatetier", description="changes a tier of a user in database")
async def updatetier(
    interaction: nextcord.Interaction,
    user: nextcord.User = nextcord.SlashOption(
        description="Enter their discord account",
        required=True,
    ),
    tier: str = nextcord.SlashOption(
        description="Enter their tier",
        required=True,
        choices=listTiers
    )
    ):
    try:
        if testerRole not in [role.id for role in interaction.user.roles]: await interaction.response.send_message(content=messages["noPermission"], ephemeral=True); return
        exists = await databaseManager.userExists(user.id)
        if not exists: await interaction.response.send_message("User does not exist in the database", ephemeral=True); return

        await databaseManager.updateTier(discordID=user.id, tier=tier)
        await interaction.response.send_message(content="Tier sucessfully updated in database, you will need to change their roles", ephemeral=True)
    except Exception as e: 
        logging.exception("Error in /updatetier command:")
        await interaction.response.send_message(content=messages["error"], ephemeral=True)

@bot.slash_command(name="restrict", description="restrict a user")
async def restrict(
    interaction: nextcord.Interaction,
    user: nextcord.User = nextcord.SlashOption(
        description="Enter their discord account",
        required=True,
    )
    ):
    try:
        if testerRole not in [role.id for role in interaction.user.roles]: await interaction.response.send_message(content=messages["noPermission"], ephemeral=True); return
        exists = await databaseManager.userExists(user.id)
        if not exists: await interaction.response.send_message("User does not exist in the database", ephemeral=True); return

        await databaseManager.updateRestriction(discordID=user.id, restricted=True)

        await interaction.response.send_message(content="User has been restricted", ephemeral=True)
    except Exception as e: 
        logging.exception("Error in /restrict command:")
        await interaction.response.send_message(content=messages["error"], ephemeral=True)

@bot.slash_command(name="unrestrict", description="unrestrict a user")
async def unrestrict(
    interaction: nextcord.Interaction,
    user: nextcord.User = nextcord.SlashOption(
        description="Enter their discord account",
        required=True,
    )
    ):
    try:
        if testerRole not in [role.id for role in interaction.user.roles]: await interaction.response.send_message(content=messages["noPermission"], ephemeral=True); return
        exists = await databaseManager.userExists(user.id)
        if not exists: await interaction.response.send_message("User does not exist in the database", ephemeral=True); return

        await databaseManager.updateRestriction(discordID=user.id, restricted=False)

        await interaction.response.send_message(content="User has been unrestricted", ephemeral=True)
    except Exception as e: 
        logging.exception("Error in /unrestrict command:")
        await interaction.response.send_message(content=messages["error"], ephemeral=True)

@bot.slash_command(name="info", description="gathers info on a user")
async def unrestrict(
    interaction: nextcord.Interaction,
    user: nextcord.User = nextcord.SlashOption(
        description="Enter their discord account",
        required=True,
    )
    ):
    try:
        exists = await databaseManager.userExists(user.id)
        if not exists: await interaction.response.send_message("User does not exist in the database", ephemeral=True); return

        result = await databaseManager.getUserInfo(user.id)
        username, tier, lastTest, region, restricted, uuid = result

        await interaction.response.send_message(embed=nextcord.Embed.from_dict(format.formatinfo(discordName=str(user.name) ,username=username, tier=tier, lastTest=lastTest, region=region, restricted=restricted, uuid=uuid)))
    except Exception as e: 
        logging.exception("Error in /info command:")
        await interaction.response.send_message(content=messages["error"], ephemeral=True)

@bot.slash_command(name="add", description="adds a user to the ticket")
async def add(
    interaction: nextcord.Interaction,
    user: nextcord.User = nextcord.SlashOption(
        description="Enter their discord account",
        required=True,
    )
    ):
    try:
        if testerRole not in [role.id for role in interaction.user.roles]: await interaction.response.send_message(content=messages["noPermission"], ephemeral=True); return
        if interaction.channel.category.id not in listRegionCategories: await interaction.response.send_message(messages["notTicketCatagory"], ephemeral=True); return

        channel = interaction.channel
        overwrite = nextcord.PermissionOverwrite()
        overwrite.view_channel = True
        overwrite.send_messages = True
        await channel.set_permissions(user, overwrite=overwrite)
        await interaction.response.send_message(content=f"<@{user.id}> has been added to the ticket!")

    except Exception as e: 
        logging.exception("Error in /add command:")
        await interaction.response.send_message(content=messages["error"], ephemeral=True)

@bot.slash_command(name="remove", description="removes a user from a ticket")
async def remove(
    interaction: nextcord.Interaction,
    user: nextcord.User = nextcord.SlashOption(
        description="Enter their discord account",
        required=True,
    )
    ):
    try:
        if testerRole not in [role.id for role in interaction.user.roles]: await interaction.response.send_message(content=messages["noPermission"], ephemeral=True); return
        if interaction.channel.category.id not in listRegionCategories: await interaction.response.send_message(messages["notTicketCatagory"], ephemeral=True); return
        
        channel = interaction.channel
        overwrite = nextcord.PermissionOverwrite()
        overwrite.view_channel = False
        overwrite.send_messages = False
        await channel.set_permissions(user, overwrite=overwrite)
        await interaction.response.send_message(content=f"<@{user.id}> has been removed from the ticket!")

    except Exception as e: 
        logging.exception("Error in /remove command:")
        await interaction.response.send_message(content=messages["error"], ephemeral=True)

@bot.slash_command(name="passeval", description="passes eval")
async def passeval(
    interaction: nextcord.Interaction,
    user: nextcord.User = nextcord.SlashOption(
    description="Enter their discord account",
    required=True,
    )
    ):
    try:
        if testerRole not in [role.id for role in interaction.user.roles]: await interaction.response.send_message(content=messages["noPermission"], ephemeral=True); return
        if interaction.channel.category.id not in listRegionCategories or interaction.channel.id in listRegionQueueChannel: await interaction.response.send_message(content="You cannot use this command in this channel", ephemeral=True); return
        
        channel = interaction.channel
        await channel.edit(name=f"passeval-{user.name}")
        await interaction.response.send_message(content=f"<@{user.id}> has passed eval!")

    except Exception as e: 
        logging.exception("Error in /passeval command:")
        await interaction.response.send_message(content=messages["error"], ephemeral=True)

if __name__ == "__main__":
    bot.run(os.getenv("TOKEN"))