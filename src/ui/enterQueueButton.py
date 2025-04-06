import nextcord
from nextcord import ui

from src.utils.loadConfig import *
from src.tierlistQueue import TierlistQueue

class EnterQueueButton(ui.View):
    def __init__(self, queue):
        super().__init__(timeout=None)
        self.queue: TierlistQueue = queue


    @nextcord.ui.button(label="Enter Queue", style=nextcord.ButtonStyle.primary, custom_id="queueButton")
    async def enter_waitlist(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.queue.addUser(interaction.message.id, interaction.user.id)
        await interaction.response.send_message(messages["addToQueue"], ephemeral=True)