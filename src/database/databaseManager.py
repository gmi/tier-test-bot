from src.utils.loadConfig import databaseType

if databaseType == "mysql":
    # Adjust the import path if needed
    from src.database import mysql as db
elif databaseType == "sqlite":
    from src.database import sqlite as db
else:
    raise ValueError(f"Unsupported database type: {databaseType}")

async def createTables() -> bool:
    return await db.createTables()

async def addUser(discordID: int, minecraftUsername: str, minecraftUUID: str,
                  tier: str, lastTest: int, server: str, region: str) -> bool:
    return await db.addUser(discordID, minecraftUsername, minecraftUUID, tier, lastTest, server, region)

async def getUserTicket(discordID: int):
    return await db.getUserTicket(discordID)

async def getResultInfo(discordID: int):
    return await db.getResultInfo(discordID)

async def addResult(discordID: int, tier: str) -> bool:
    return await db.addResult(discordID, tier)

async def userExists(discordID: int) -> bool:
    return await db.userExists(discordID)

async def getLastTest(discordID: int):
    return await db.getLastTest(discordID)

async def getTier(discordID: int):
    return await db.getTier(discordID)

async def updateUsername(discordID: int, username: str, uuid: str) -> bool:
    return await db.updateUsername(discordID, username, uuid)

async def updateTier(discordID: int, tier: str) -> bool:
    return await db.updateTier(discordID, tier)

async def isRestriced(discordID: int) -> bool:
    return await db.isRestricted(discordID=discordID)

async def updateRestriction(discordID: int, restricted: bool) -> bool:
    return await db.updateRestriction(discordID=discordID, restricted=restricted)

async def getUserInfo(discordID: int):
    return await db.getUserInfo(discordID=discordID)