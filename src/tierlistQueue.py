from src.utils import format
from src.utils.loadConfig import *

class TierlistQueue():
    def __init__(self, maxQueue: int, maxTesters: int, cooldown: int):

    
        self.queue = {}
        self.maxQueue = maxQueue
        self.maxTesters = maxTesters
        self.cooldown = cooldown

    def setup(self, regions: dict) -> None:
        for region_name, region_data in regions.items():
            self.queue[region_name] = {
                "queueChannel": region_data["queue_channel"],
                "queueMessage": None,
                "ticketCatagory": region_data["ticket_catagory"],
                "pingRole": region_data["role_ping"],
                "open": False,
                "testers": [],
                "queue": []
            }

    def openqueue(self, queue: str, open: bool):
        self.queue[queue]["open"] = open
        if open == False:
            self.queue[queue]["queue"] = []
            self.queue[queue]["testers"] = []

    def addUser(self, messageID: int, userID: int):
        region = ""
        for reg, data in self.queue.items():
            if data["queueMessage"] == messageID:
                region = reg
                break

        if region == "":
            return "region doesnt exist"
        
        if userID in self.queue[region]["queue"]:
            return messages["alreadyInQueue"]
        
        if len(self.queue[region]["queue"]) >= self.maxQueue:
            return messages["queueFull"]
        
        self.queue[region]["queue"].append(userID)
        return messages["addToQueue"]

    
    def removeUser(self, messageID: int, userID: int):
        region = ""
        for reg, data in self.queue.items():
            if data["queueMessage"] == messageID:
                region = reg
                break

        if region == "":
            return "region doesnt exist"
        
        if userID not in self.queue[region]["queue"]:
            return messages["notInQueue"]
        
        self.queue[region]["queue"].remove(userID)
        return messages["leaveQueue"]
        

    def addTester(self, region: str, userID: int):
        if self.queue[region]["testers"] == []:
            self.openqueue(queue=region, open=True)
        
        if userID in self.queue[region]["testers"]:
            return ("You are already testing this queue!", "")

        if len(self.queue[region]["testers"]) < self.maxTesters:
            self.queue[region]["testers"].append(userID)
            return (f"{messages["testerOpenQueue"]}: <#{listRegions[region]["queue_channel"]}>", self.makeQueueMessage(region=region))
        
    def removeTester(self, region: str, userID: str):   # ahh code right here
        if self.queue[region]["open"] == False: return "Testing is closed"

        if userID in self.queue[region]["testers"]:
            self.queue[region]["testers"].remove(userID)
            
            if self.queue[region]["testers"] == []:
                self.openqueue(queue=region, open=False)
                return ("testing has closed", format.formatnoqueue(), self.queue[region]["queueChannel"], self.queue[region]["queueMessage"])

            return ("you have stopped testing", self.makeQueueMessage(region=region), self.queue[region]["queueChannel"], self.queue[region]["queueMessage"])
        
        return ("you are not testing this region", self.makeQueueMessage(region=region), self.queue[region]["queueChannel"], self.queue[region]["queueMessage"])
    
    def getNextTest(self, testerID: int, region: str):
        if self.queue[region]["queue"] == []:
            return (None, f"No users are in the queue for the {region} region")
        user = self.queue[region]["queue"].pop(0)
        return (user, None)

        
    def makeQueueMessage(self, region: str):
        capacity = f"{len(self.queue[region]["queue"])}/{self.maxQueue}"
        testerCapacity = f"{len(self.queue[region]["testers"])}/{self.maxTesters}"
        queue = "\n".join([f"{i+1}. <@{user_id}>" for i, user_id in enumerate(self.queue[region]["queue"])])
        testers = "\n".join([f"{i+1}. <@{user_id}>" for i, user_id in enumerate(self.queue[region]["testers"])])

        return format.formatqueue(capacity=capacity, queue=queue, testerCapacity=testerCapacity, testers=testers)

    def addQueueMessageId(self, region: str, messageID: int):
        self.queue[region]["queueMessage"] = messageID
    
    def getqueueraw(self) -> dict: # for testing
        return self.queue
        