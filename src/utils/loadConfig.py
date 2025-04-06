import yaml
import logging  
import sys

try:
    with open("config/config.yml", "r") as file:
        config = yaml.safe_load(file)
except Exception as e:
    logging.exception("Failed to load configuration file:")
    sys.exit("Error: Unable to load config file.")

try:
    listTiers: list[str] = [key for key in config["bot"]["tiers"]]; listTiers.append("none")
    listRegionsText: list[str] = [key for key in config["bot"]["regions"]]
    listRegionCategories: list[str] = [region["ticket_catagory"] for region in config["bot"]["regions"].values()]
    listRegionQueueChannel: list[str] = [region["queue_channel"] for region in config["bot"]["regions"].values()]

    testerRole: int = config["bot"]["roles"]["tester"]

    messages = config["bot"]["messages"]

    listRegions = config["bot"]["regions"]

    maxQueue = config["bot"]["options"]["queueLimit"]
    maxTester = config["bot"]["options"]["testerLimit"]
    cooldown = config["bot"]["options"]["cooldown"]
    reloadQueue = config["bot"]["options"]["reloadQueue"]

    channels = config["bot"]["channels"]
    
except Exception as e:
    logging.exception(f"Setting up config failed:")
    sys.exit("Error: Failed to setup config")