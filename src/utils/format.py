# used not to clutter main.py
import json

with open("config/resultmessage.json", "r") as file:
    resultmessage = json.load(file)

with open("config/noqueue.json", "r") as file:
    noqueuemessage = json.load(file)

with open("config/enterwaitlist.json", "r") as file:
    enterwaitlistmessage = json.load(file)

def formatresult(discordUsername, testerID, region, minecraftUsername, oldTier, newTier, uuid):
    formatted_message = json.dumps(resultmessage).replace("{{PLAYER}}", discordUsername)
    formatted_message = formatted_message.replace("{{TESTER}}", f"<@{testerID}>")
    formatted_message = formatted_message.replace("{{REGION}}", region)
    formatted_message = formatted_message.replace("{{USERNAME}}", minecraftUsername)
    formatted_message = formatted_message.replace("{{PREV_TIER}}", oldTier)
    formatted_message = formatted_message.replace("{{NEW_TIER}}", newTier)
    formatted_message = formatted_message.replace("{{THUMBNAIL_URL}}", f"https://render.crafty.gg/3d/bust/{uuid}")
    return json.loads(formatted_message)

def formatnoqueue(timestamp):
    formatted_message = json.dumps(noqueuemessage).replace("{{TIMESTAMP}}", timestamp)
    return json.loads(formatted_message)