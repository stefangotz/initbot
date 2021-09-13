import discord

from .config import CFG

client = discord.Client()


@client.event
async def on_ready():
    print("Logged in as {0.user}".format(client))


if __name__ == "__main__":
    client.run(CFG.token)
