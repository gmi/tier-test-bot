import nextcord
from nextcord import ui

from src.utils.loadConfig import *

class EnterQueueButton(ui.View):
    def __init__(self):
        super().__init__(timeout=None)


    @nextcord.ui.button(label="Enter Queue", style=nextcord.ButtonStyle.primary, custom_id="queueButton")
    async def enter_waitlist(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.send_message(messages["addToQueue"], ephemeral=True)