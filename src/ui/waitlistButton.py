import nextcord
from nextcord import ui
from src.database import sqlite
from src.utils.mojang import getuserid
from src.utils.loadConfig import listRegions

class WaitlistButton(ui.View):
    def __init__(self):
        super().__init__(timeout=None)


    @nextcord.ui.button(label="Enter Waitlist", style=nextcord.ButtonStyle.primary, custom_id="waitlistButton")
    async def enter_waitlist(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
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
        uuid = await getuserid(self.ign.value)
        if uuid == "8667ba71b85a4004af54457a9734eed7": await interaction.response.send_message("Minecraft username does not exist", ephemeral=True); return
        if self.region.value not in listRegions: await interaction.response.send_message("Selected Region does not exist", ephemeral=True); return

        await sqlite.addUser(discordID=interaction.user.id, minecraftUsername=self.ign.value, minecraftUUID=uuid, tier="NONE", lastTest=0, server=self.server.value)

        role = interaction.guild.get_role(listRegions[self.region.value]["role_ping"])
        if role is None: await interaction.response.send_message("Bot not setup correctly, role for region not found.", ephemeral=True); return
        await interaction.response.send_message(
            f"Entered waitlist, <#{listRegions[self.region.value]["queue_channel"]}>",
            ephemeral=True
        )
