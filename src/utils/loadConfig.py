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
    catagories = config["bot"]["catagories"]
    
    listTiers: list[str] = [key for key in config["bot"]["tiers"]]; listTiers.append("none")
    listHighTiers: list[str] = config["bot"]["highTiers"]
    listRegionsText: list[str] = [key for key in config["bot"]["regions"]]
    listRegionCategories: list[int] = [region["ticket_catagory"] for region in config["bot"]["regions"].values()]; listRegionCategories.append(catagories["highTests"])
    listRegionQueueChannel: list[int] = [region["queue_channel"] for region in config["bot"]["regions"].values()]
    listRegionRolePing: list[int] = [region["role_ping"] for region in config["bot"]["regions"].values()]

    testerRole: int = config["bot"]["roles"]["tester"]

    listTierRoles: dict[str, int] = {tier: role_id for tier, role_id in config["bot"]["tiers"].items()}

    messages = config["bot"]["messages"]

    listRegions = config["bot"]["regions"]

    maxQueue = config["bot"]["options"]["queueLimit"]
    maxTester = config["bot"]["options"]["testerLimit"]
    cooldown = config["bot"]["options"]["cooldown"]
    reloadQueue = config["bot"]["options"]["reloadQueue"]

    channels = config["bot"]["channels"]

    mysqlInfo = config["database"]["mysql"]
    databaseType = config["database"]["type"]
    
except Exception as e:
    logging.exception(f"Setting up config failed:")
    sys.exit("Error: Failed to setup config")