import sqlite3
import asyncio
import datetime

def withConnection(func):
    async def wrapper(*args, **kwargs):
        connection = sqlite3.connect('storage/database.db')
        try:
            cursor = connection.cursor()
            result = await func(cursor, *args, **kwargs)
            connection.commit()
            return result
        except Exception as e:
            connection.rollback()
            print(e)
            return False
        finally:
            connection.close()
    return wrapper

@withConnection
async def createTables(cursor: sqlite3.Cursor) -> bool:
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        discordID INTEGER PRIMARY KEY,
        minecraftUsername TEXT NOT NULL,
        minecraftUUID TEXT NOT NULL,
        tier TEXT NOT NULL,
        lastTest INTEGER NOT NULL,
        server TEXT NOT NULL,
        region TEXT NOT NULL
    )""")
    return True

@withConnection
async def addUser(cursor: sqlite3.Cursor, discordID: int, minecraftUsername: str, minecraftUUID: str, tier: str, lastTest: int, server: str, region: str) -> bool:
    cursor.execute("""
    INSERT INTO users (discordID, minecraftUsername, minecraftUUID, tier, lastTest, server, region)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(discordID) DO UPDATE SET
        minecraftUsername = excluded.minecraftUsername,
        minecraftUUID = excluded.minecraftUUID,
        server = excluded.server,
        region = excluded.region
    """, (discordID, minecraftUsername, minecraftUUID, tier, lastTest, server, region))
    return True

@withConnection
async def getUserTicket(cursor: sqlite3.Cursor, discordID: int):
    cursor.execute("""
    SELECT minecraftUsername, tier, server, minecraftUUID FROM users WHERE discordID = ?
    """, (discordID,))

    return cursor.fetchone()


@withConnection
async def getResultInfo(cursor: sqlite3.Cursor, discordID: int):
    cursor.execute("""
    SELECT minecraftUsername, tier, region FROM users WHERE discordID = ?
    """, (discordID,))

    return cursor.fetchone()


@withConnection
async def addResult(cursor: sqlite3.Cursor, discordID: int, tier: str) -> bool:
    lastTest = int(datetime.datetime.now().timestamp())
    cursor.execute("""
    UPDATE users
        SET tier = ?, lastTest = ?
    WHERE
        discordID = ?    
    """, (tier, lastTest, discordID))
    return True

@withConnection
async def userExists(cursor: sqlite3.Cursor, discordID: int) -> bool:
    cursor.execute("SELECT 1 FROM users WHERE discordID = ? LIMIT 1", (discordID,))
    return cursor.fetchone() is not None

@withConnection
async def updateUsername(cursor: sqlite3.Cursor, discordID: int, username: str, uuid: int) -> bool:
    cursor.execute("""
    UPDATE users
        SET minecraftUsername = ?, minecraftUUID = ?
    WHERE
        discordID = ?    
    """, (username, uuid, discordID))
    return True