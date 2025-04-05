from src.utils import format
from src.utils.loadConfig import *

class TierlistQueue():
    def __init__(self, maxQueue: int, maxTesters: int, cooldown: int):
        from main import bot
        
    
        self.queue = {}
        self.maxQueue = maxQueue
        self.maxTesters = maxTesters
        self.cooldown = cooldown
        self.bot=bot

    def setup(self, regions: dict) -> None:
        for region_name, region_data in regions.items():
            self.queue[region_name] = {
                "queueChannel": region_data["queue_channel"],
                "ticketCatagory": region_data["ticket_catagory"],
                "pingRole": region_data["role_ping"],
                "open": False,
                "testers": [],
                "queue": []
            }

    def openqueue(self, queue: str, open: bool):
        self.queue[queue]["open"] = open

    def addUser(self, region: str, userID: int):
        if region in self.queue:
            if len(self.queue[region]["queue"]) < self.maxQueue:
                self.queue[region]["queue"].append(userID)

    def addTester(self, region: str, userID: int):
        if self.queue[region]["testers"] == []:
            self.openqueue(queue=region, open=True)
            self.sendQueueMessage(region=region)
        
        if userID in self.queue[region]["testers"]:
            return "You are already testing this queue!"

        if len(self.queue[region]["testers"]) < self.maxTesters:
            self.queue[region]["testers"].append(userID)
            return f"{messages["testerOpenQueue"]}: <#{listRegions[region]["queue_channel"]}>"

        
    def makeQueueMessage(self, region: str):
        capacity = f"{len(self.queue[region]["queue"])}/{self.maxQueue}"
        testerCapacity = f"{len(self.queue[region]["testers"])}/{self.maxTesters}"
        queue = "\n".join([f"{i+1}. <@{user_id}>" for i, user_id in enumerate(self.queue[region]["queue"])])
        testers = "\n".join([f"{i+1}. <@{user_id}>" for i, user_id in enumerate(self.queue[region]["testers"])])

        return format.formatqueue(capacity=capacity, queue=queue, testerCapacity=testerCapacity, testers=testers)
    
    def sendQueueMessage(self, region: str):
        message = self.makeQueueMessage(region=region)
    
    def getqueueraw(self) -> dict: # for testing
        return self.queue