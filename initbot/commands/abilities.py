from pathlib import Path
from typing import List, Dict
import json
from discord import Embed  # type: ignore
from discord.ext import commands  # type: ignore
from pydantic.dataclasses import dataclass

from .roll import DieRoll


@dataclass
class Ability:
    name: str
    description: str

    def roll(self) -> "AbilityScore":
        return AbilityScore(self, DieRoll(6, 3).roll_one())  # type: ignore


with open(Path(__file__).parent / "abilities.json", encoding="utf8") as fd:
    ABILITIES: List[Ability] = [
        Ability(**a) for a in json.load(fd)["abilities"]  # type: ignore
    ]

ABILITIES_DICT: Dict[str, Ability] = {abl.name: abl for abl in ABILITIES}
ABILITIES_DICT.update({abl.name.lower(): abl for abl in ABILITIES})


@dataclass
class AbilityScoreModifier:
    score: int
    mod: int
    spells: int
    max_spell_level: int


ABILITY_SCORE_MODIFIERS: List[AbilityScoreModifier] = [
    AbilityScoreModifier(3, -3, -99, -99),  # type: ignore
    AbilityScoreModifier(4, -2, -2, 1),  # type: ignore
    AbilityScoreModifier(5, -2, -2, 1),  # type: ignore
    AbilityScoreModifier(6, -1, -1, 1),  # type: ignore
    AbilityScoreModifier(7, -1, -1, 1),  # type: ignore
    AbilityScoreModifier(8, -1, 0, 2),  # type: ignore
    AbilityScoreModifier(9, 0, 0, 2),  # type: ignore
    AbilityScoreModifier(10, 0, 0, 3),  # type: ignore
    AbilityScoreModifier(11, 0, 0, 3),  # type: ignore
    AbilityScoreModifier(12, 0, 0, 4),  # type: ignore
    AbilityScoreModifier(13, 1, 0, 4),  # type: ignore
    AbilityScoreModifier(14, 1, 1, 4),  # type: ignore
    AbilityScoreModifier(15, 1, 1, 5),  # type: ignore
    AbilityScoreModifier(16, 2, 1, 5),  # type: ignore
    AbilityScoreModifier(17, 2, 2, 5),  # type: ignore
    AbilityScoreModifier(18, 3, 2, 6),  # type: ignore
]

ABILITY_SCORE_MODIFIERS_DICT: Dict[int, AbilityScoreModifier] = {
    asm.score: asm for asm in ABILITY_SCORE_MODIFIERS
}


@dataclass
class AbilityScore:
    abl: Ability
    score: int = 0

    @property
    def mod(self) -> int:
        return self.modifier.mod

    @property
    def modifier(self) -> AbilityScoreModifier:
        return ABILITY_SCORE_MODIFIERS_DICT[self.score]


@commands.command()
async def abls(ctx):
    """Lists the six character abilities and their descriptions."""
    embed = Embed(
        title="Abilities", description="**Luck**\n" + ABILITIES_DICT["Luck"].description
    )
    for ability in ABILITIES:
        if ability.name != "Luck":
            embed.add_field(name=ability.name, value=ability.description)
    await ctx.send(embed=embed)


@commands.command()
async def abl(ctx, name: str):
    await ctx.send(str(ABILITIES_DICT[name]))


@commands.command()
async def asms(ctx):
    await ctx.send(str(ABILITY_SCORE_MODIFIERS))


@commands.command()
async def asm(ctx, score: int):
    await ctx.send(str(ABILITY_SCORE_MODIFIERS_DICT[score]))


@abls.error
@abl.error
@asms.error
@asm.error
async def handle_error(ctx, error):
    await ctx.send(str(error), delete_after=5)
