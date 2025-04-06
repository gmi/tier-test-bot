import aiohttp

async def getuserid(username: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.mojang.com/users/profiles/minecraft/{username}") as response:
            if response.status == 200:
                data = await response.json()
                return str(data.get("id"))
            else:
                return "8667ba71b85a4004af54457a9734eed7" # default id of 'steve' (i think), very unlikely a person with the username steve will test <3, used a valid id so images will work