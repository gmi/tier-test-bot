# used not to clutter main.py
import json
import datetime

with open("config/resultmessage.json", "r") as file:
    resultmessage = json.load(file)

with open("config/noqueue.json", "r") as file:
    noqueuemessage = json.load(file)

with open("config/enterwaitlist.json", "r") as file:
    enterwaitlistmessage = json.load(file)

with open("config/queue.json", "r") as file:
    queuemessage = json.load(file)

with open("config/ticket.json", "r") as file:
    ticketmessage = json.load(file)

with open("config/highticket.json", "r") as file:
    highticketmessage = json.load(file)

with open("config/info.json", "r") as file:
    infomessage = json.load(file)

def formatresult(discordUsername, testerID, region, minecraftUsername, oldTier, newTier, uuid):
    formatted_message = json.dumps(resultmessage).replace("{{PLAYER}}", discordUsername)
    formatted_message = formatted_message.replace("{{TESTER}}", f"<@{testerID}>")
    formatted_message = formatted_message.replace("{{REGION}}", region)
    formatted_message = formatted_message.replace("{{USERNAME}}", minecraftUsername)
    formatted_message = formatted_message.replace("{{PREV_TIER}}", oldTier)
    formatted_message = formatted_message.replace("{{NEW_TIER}}", newTier)
    formatted_message = formatted_message.replace("{{THUMBNAIL_URL}}", f"https://render.crafty.gg/3d/bust/{uuid}")
    return json.loads(formatted_message)

def formatnoqueue():
    formatted_message = json.dumps(noqueuemessage).replace("{{TIMESTAMP}}", f"<t:{int(datetime.datetime.now().timestamp())}:f>") # in seconds
    return json.loads(formatted_message)

def formatqueue(capacity, queue, testerCapacity, testers):
    formatted_message = json.loads(json.dumps(queuemessage))
    
    queue_field = formatted_message["fields"][0]
    queue_field["name"] = queue_field["name"].replace("{{CAPACITY}}", capacity)
    queue_field["value"] = queue_field["value"].replace("{{QUEUE}}", queue)

    testers_field = formatted_message["fields"][1]
    testers_field["name"] = testers_field["name"].replace("{{TESTERCAPACITY}}", testerCapacity)
    testers_field["value"] = testers_field["value"].replace("{{TESTERS}}", testers)
    
    return formatted_message

def formatticketmessage(username, tier, server, uuid):
    formatted_message = json.dumps(ticketmessage).replace("{{SERVER}}", server)
    formatted_message = formatted_message.replace("{{USERNAME}}", username)
    formatted_message = formatted_message.replace("{{TIER}}", tier)
    formatted_message = formatted_message.replace("{{THUMBNAIL_URL}}", f"https://render.crafty.gg/3d/bust/{uuid}")
    return json.loads(formatted_message)

def formathighticketmessage(username, tier, uuid):
    formatted_message = json.dumps(highticketmessage).replace("{{USERNAME}}", username)
    formatted_message = formatted_message.replace("{{TIER}}", tier)
    formatted_message = formatted_message.replace("{{THUMBNAIL_URL}}", f"https://render.crafty.gg/3d/bust/{uuid}")
    return json.loads(formatted_message)

def formatinfo(discordName, username, tier, lastTest, region, restricted, uuid):
    formatted_message = json.dumps(infomessage).replace("{{USERNAME}}", username)
    formatted_message = formatted_message.replace("{{TIER}}", tier)
    if lastTest == 0:
        formatted_message = formatted_message.replace("{{LAST}}", f"Not tested before")
    else:
        formatted_message = formatted_message.replace("{{LAST}}", f"<t:{lastTest}:f>")
    formatted_message = formatted_message.replace("{{REGION}}", region)
    if restricted == 1:
        formatted_message = formatted_message.replace("{{RESTRICTED}}", "true")
    else:
        formatted_message = formatted_message.replace("{{RESTRICTED}}", "false")

    formatted_message = formatted_message.replace("{{DISCORDUSER}}", discordName)
    formatted_message = formatted_message.replace("{{THUMBNAIL_URL}}", f"https://render.crafty.gg/3d/bust/{uuid}")
    return json.loads(formatted_message)
