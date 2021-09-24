from dataclasses import dataclass
from typing import List
from discord.ext import commands  # type: ignore


@dataclass
class Equipment:
    name: str
    base_cost: int = 0
    quantity: int = 1


EQUIPMENT: List[Equipment] = [Equipment("Backpack", 200, 1), Equipment("Candle", 1, 2)]


@commands.command()
async def equipment(ctx):
    await ctx.send(str(EQUIPMENT))


@equipment.error
async def equipment_error(ctx, error):
    await ctx.send(str(error))
