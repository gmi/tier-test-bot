
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
        if len(self.queue[region]["queue"]) < self.maxTesters:
            self.queue[region]["testers"].append(userID)
    
    def getqueueraw(self) -> dict: # for testing
        return self.queue