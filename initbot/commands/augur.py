from dataclasses import dataclass
from typing import List, Dict
import random

from discord.ext import commands  # type: ignore


@dataclass
class Augur:
    description: str
    roll: int


AUGURS: List[Augur] = [
    Augur("Harsh winter: All attack rolls", 1),
    Augur("The bull: Melee attack rolls", 2),
    Augur("Fortunate date: Missile fire attack rolls", 3),
    Augur("Raised by wolves: Unarmed attack rolls", 4),
    Augur("Conceived on horseback: Mounted attack rolls", 5),
    Augur("Born on the battlefield: Damage rolls", 6),
    Augur("Path of the bear: Melee damage rolls", 7),
    Augur("Hawkeye: Missile fire damage rolls", 8),
    Augur("Pack hunter: Attack and damage rolls for 0-level starting weapon", 9),
    Augur("Born under the loom: Skill checks (including thief skills)", 10),
    Augur("Fox's cunning: Find/disable traps", 11),
    Augur("Four-leafed clover: Find secret doors", 12),
    Augur("Seventh son: Spell checks", 13),
    Augur("The raging storm: Spell damage", 14),
    Augur("Righteous heart: Turn unholy checks", 15),
    Augur(
        "Survived the plague: Magical healing (If a cleric, applies to all healing the cleric performs. If not a cleric, applies to all magical healing received from other sources.)",
        16,
    ),
    Augur("Lucky sign: Saving throws", 17),
    Augur("Guardian angel: Savings throws to escape traps", 18),
    Augur("Survived a spider bite: Saving throws against poison", 19),
    Augur("Struck by lightning: Reflex saving throws", 20),
    Augur("Lived through famine: Fortitude saving throws", 21),
    Augur("Resisted temptation: Willpower saving throws", 22),
    Augur("Charmed house: Armor Class", 23),
    Augur("Speed of the cobra: Initiative", 24),
    Augur("Bountiful harvest: Hit points (applies at each level)", 25),
    Augur(
        "Warrior's arm: Critical hit tables (Luck normally affects critical hits and fumbles. On this result, the modifier is doubled for purposes of crits or fumbles.)",
        26,
    ),
    Augur("Unholy house: Corruption rolls", 27),
    Augur(
        "The Broken Star: Fumbles (Luck normally affects critical hits and fumbles. On this result, the modifier is doubled for purposes of crits or fumbles.)",
        28,
    ),
    Augur("Birdsong: Number of languages", 29),
    Augur("Wild child: Speed (each +1/-1 = +5'/-5' speed)", 30),
]

AUGURS_DICT: Dict[int, Augur] = {aug.roll: aug for aug in AUGURS}


@commands.command()
async def augurs(ctx):
    await ctx.send(str(AUGURS))


@commands.command()
async def augur(ctx):
    await ctx.send(str(random.choice(AUGURS)))


@augurs.error
async def augur_error(ctx, error):
    await ctx.send(str(error), delete_after=5)
