import nextcord
from nextcord import ui
from src.utils.loadConfig import messages

class CloseTicketButton(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.cancelled = False

    @nextcord.ui.button(label="Cancel", style=nextcord.ButtonStyle.danger, custom_id="cancel")
    async def exit_queue(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        try:
            self.cancelled = True
            await interaction.response.send_message(content="Ticket will stay open")
        except Exception as e:
            await interaction.response.send_message(content=messages["error"], ephemeral=True)