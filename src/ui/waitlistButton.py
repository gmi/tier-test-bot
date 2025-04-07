import nextcord
from nextcord import ui
import datetime

from src.database import databaseManager
from src.utils.mojang import getuserid
from src.utils.loadConfig import messages, listRegions, cooldown, listHighTiers, catagories
from src.utils import format

class WaitlistButton(ui.View):
    def __init__(self):
        super().__init__(timeout=None)


    @nextcord.ui.button(label="Enter Waitlist", style=nextcord.ButtonStyle.primary, custom_id="waitlistButton")
    async def enter_waitlist(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        
        exists = await databaseManager.userExists(interaction.user.id)
        if exists:
            isrestricted = await databaseManager.isRestriced(interaction.user.id)
            if isrestricted: await interaction.response.send_message(content="You are currently restricted", ephemeral=True); return
            lastTest = await databaseManager.getLastTest(interaction.user.id)
            lastTest = lastTest[0]
            if int(datetime.datetime.now().timestamp()) - lastTest <= cooldown * 60: await interaction.response.send_message(content=f"You can test again at: <t:{lastTest + (cooldown*60)}:f>", ephemeral=True); return
        
            current_tier = await databaseManager.getTier(interaction.user.id)
            current_tier = current_tier[0]
            if(current_tier) in listHighTiers:
                categoryChannel = interaction.guild.get_channel(catagories["highTests"])

                channelID = await interaction.guild.create_text_channel(name=f"highTest-{interaction.user.name}", category=categoryChannel)
                overwrite = nextcord.PermissionOverwrite()
                overwrite.view_channel = True
                overwrite.send_messages = True
                await channelID.set_permissions(interaction.user, overwrite=overwrite)

                messageData = await databaseManager.getUserTicket(interaction.user.id)
                ticketMessage = format.formathighticketmessage(username=messageData[0], tier=messageData[1], uuid=messageData[3])
                await channelID.send(content=f"<@{interaction.user.id}>" ,embed=nextcord.Embed.from_dict(ticketMessage))
                await interaction.response.send_message(content=f"A high tier ticket has been created: <#{channelID.id}>", ephemeral=True)
                return

        modal = WaitlistForm()
        await interaction.response.send_modal(modal)


class WaitlistForm(ui.Modal):
    def __init__(self):
        super().__init__("Join the Waitlist")

        self.ign = ui.TextInput(label="Minecraft Username", placeholder="Enter your in-game name", required=True)
        self.region = ui.TextInput(label=f"Region ({', '.join(listRegions.keys())})", placeholder="Enter your region", style=nextcord.TextInputStyle.short, required=True)
        self.server = ui.TextInput(label="Preferred Server", placeholder="Enter your preferred server", style=nextcord.TextInputStyle.short, required=True)

        self.add_item(self.ign)
        self.add_item(self.region)
        self.add_item(self.server)

    async def callback(self, interaction: nextcord.Interaction):
        try:
            uuid = await getuserid(self.ign.value)
            if uuid == "8667ba71b85a4004af54457a9734eed7": await interaction.response.send_message("Minecraft username does not exist", ephemeral=True); return
            if self.region.value not in listRegions: await interaction.response.send_message("Selected Region does not exist", ephemeral=True); return

            await databaseManager.addUser(discordID=interaction.user.id, minecraftUsername=self.ign.value, minecraftUUID=uuid, tier="none", lastTest=0, server=self.server.value, region=self.region.value)

            

            current_roles = interaction.user.roles
            role_ids_to_remove = [role.id for role in current_roles if role.id in [r["role_ping"] for r in listRegions.values()]]
            if role_ids_to_remove:
                await interaction.user.remove_roles(*[interaction.guild.get_role(role_id) for role_id in role_ids_to_remove])
            
            role = interaction.guild.get_role(listRegions[self.region.value]["role_ping"])
            if role is None: await interaction.response.send_message("Bot not setup correctly, role for region not found.", ephemeral=True); return
            await interaction.user.add_roles(role)

            await interaction.response.send_message(content=f"Entered waitlist, <#{listRegions[self.region.value]["queue_channel"]}>", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(content=messages["error"], ephemeral=True)
