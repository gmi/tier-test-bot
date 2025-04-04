import nextcord
from nextcord import ui

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
        self.region = ui.TextInput(label="Region", placeholder="Enter your region", style=nextcord.TextInputStyle.short, required=True)
        self.server = ui.TextInput(label="Preferred Server", placeholder="Enter your preferred server", style=nextcord.TextInputStyle.short, required=True)

        self.add_item(self.ign)
        self.add_item(self.region)
        self.add_item(self.server)

    async def callback(self, interaction: nextcord.Interaction):
        await interaction.response.send_message(
            f"Entered waitlist",
            ephemeral=True
        )
