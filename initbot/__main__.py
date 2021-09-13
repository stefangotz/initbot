from dataclasses import dataclass
import random
import re

import discord

from .config import CFG

client = discord.Client()
_DIE_PATTERN = re.compile(r"^([0-9]*)d([0-9]+)([+-][0-9]+)?$", re.IGNORECASE)


@dataclass
class DieRoll:
    sides: int
    dice: int = 1
    modifier: int = 0

    def __init__(self, text: str):
        match = _DIE_PATTERN.match(text)
        if match:
            self.sides = int(match.group(2))
            if match.group(1):
                self.dice = int(match.group(1))
            if match.group(3):
                self.modifier = int(match.group(3))

    def roll(self):
        return self.dice * random.randint(1, self.sides) + self.modifier

    @staticmethod
    def is_die_roll(text: str) -> bool:
        return bool(_DIE_PATTERN.match(text))


@client.event
async def on_ready():
    print("Logged in as {0.user}".format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if DieRoll.is_die_roll(message.content):
        result = DieRoll(message.content).roll()
        await message.channel.send(
            f"You rolled **{result}** ({message.content} - {message.author.display_name})"
        )


if __name__ == "__main__":
    client.run(CFG.token)
