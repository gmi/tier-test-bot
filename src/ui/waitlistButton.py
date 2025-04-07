import nextcord
from nextcord import ui
import datetime

from src.database import sqlite
from src.utils.mojang import getuserid
from src.utils.loadConfig import messages, listRegions, cooldown, listRegionRolePing

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
        try:
            uuid = await getuserid(self.ign.value)
            if uuid == "8667ba71b85a4004af54457a9734eed7": await interaction.response.send_message("Minecraft username does not exist", ephemeral=True); return
            if self.region.value not in listRegions: await interaction.response.send_message("Selected Region does not exist", ephemeral=True); return

            await sqlite.addUser(discordID=interaction.user.id, minecraftUsername=self.ign.value, minecraftUUID=uuid, tier="none", lastTest=0, server=self.server.value, region=self.region.value)

            lastTest = await sqlite.getLastTest(interaction.user.id)
            lastTest = lastTest[0]

            if int(datetime.datetime.now().timestamp()) - lastTest <= cooldown * 60: await interaction.response.send_message(content=f"You can test again at: <t:{lastTest + (cooldown*60)}:f>", ephemeral=True); return
            
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
