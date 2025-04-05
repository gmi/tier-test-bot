# used not to clutter main.py
import json

with open("config/resultmessage.json", "r") as file:
    resultmessage = json.load(file)

with open("config/noqueue.json", "r") as file:
    noqueuemessage = json.load(file)

with open("config/enterwaitlist.json", "r") as file:
    enterwaitlistmessage = json.load(file)

with open("config/queue.json", "r") as file:
    queuemessage = json.load(file)


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
    formatted_message = json.dumps(noqueuemessage).replace("{{TIMESTAMP}}", f"<t:{timestamp}:f>")
    return json.loads(formatted_message)

def formatqueue(capacity, queue, testerCapacity, testers):
    # Create a deep copy of the original queuemessage to avoid modifying it
    formatted_message = json.loads(json.dumps(queuemessage))
    
    # Update the Queue field
    queue_field = formatted_message["fields"][0]
    queue_field["name"] = queue_field["name"].replace("{{CAPACITY}}", capacity)
    queue_field["value"] = queue_field["value"].replace("{{QUEUE}}", queue)
    
    # Update the Testers field
    testers_field = formatted_message["fields"][1]
    testers_field["name"] = testers_field["name"].replace("{{TESTERCAPACITY}}", testerCapacity)
    testers_field["value"] = testers_field["value"].replace("{{TESTERS}}", testers)
    
    return formatted_message