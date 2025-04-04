from nextcord.ext import commands
import os
import json
from dotenv import load_dotenv
import yaml
import nextcord
from src.utils import mojang

load_dotenv()

with open("config/config.yml", "r") as file:
    config = yaml.safe_load(file)

with open("config/resultmessage.json", "r") as file:
    resultmessage = json.load(file)  # Load JSON properly

intents = nextcord.Intents.all()
bot = commands.Bot(intents=intents)

tiers: list[str] = [key for key in config["bot"]["tiers"]]; tiers.append("none")
regions: list[str] = [key for key in config["bot"]["regions"]]
databaseEnabled: bool = config["database"]["type"] != "none"
resultschannel: int = config["bot"]["channels"]["results"]


@bot.event
async def on_ready():
    print(f"Tier Testing bot has logged online ✅")

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
        choices=tiers
    ),
    oldtier: str = nextcord.SlashOption(
        description="Enter their old tier",
        required=True,
        choices=tiers
    ),
    region: str = nextcord.SlashOption(
        description="Enter their region",
        required=True,
        choices=regions
    )
    ):

    uuid = await mojang.getuserid(username=username)
    # Replace placeholders in resultmessage
    formatted_message = json.dumps(resultmessage).replace("{{PLAYER}}", user.name)
    formatted_message = formatted_message.replace("{{TESTER}}", f"<@{interaction.user.id}>")
    formatted_message = formatted_message.replace("{{REGION}}", region)
    formatted_message = formatted_message.replace("{{USERNAME}}", username)
    formatted_message = formatted_message.replace("{{PREV_TIER}}", oldtier)
    formatted_message = formatted_message.replace("{{NEW_TIER}}", newtier)
    formatted_message = formatted_message.replace("{{THUMBNAIL_URL}}", f"https://render.crafty.gg/3d/bust/{uuid}")
    # Convert back to dictionary
    result_embed_data = json.loads(formatted_message)
    
    # Create embed
    embed = nextcord.Embed.from_dict(result_embed_data)
    
    await bot.get_channel(resultschannel).send(content=f"<@{user.id}>" ,embed=embed)
    await interaction.response.send_message("Result message sent!", ephemeral=True)



if __name__ == "__main__":
    bot.run(os.getenv("TOKEN"))