from pathlib import Path
from typing import List, Dict
import logging
from discord import Embed  # type: ignore
from discord.ext import commands  # type: ignore

from ...data.ability import AbilityData, AbilityModifierData, AbilitiesData
from ...utils import get_unique_prefix_match


_PATH: Path = Path(__file__).parent / "abilities.json"
_ABILITIES_DATA: AbilitiesData = AbilitiesData(abilities=[])
if _PATH:
    _ABILITIES_DATA = AbilitiesData.parse_file(_PATH)
else:
    logging.warning("Unable to find %s", _PATH)

_ABILITIES: List[AbilityData] = _ABILITIES_DATA.abilities


def get_ability(name: str) -> AbilityData:
    return get_unique_prefix_match(name, _ABILITIES, lambda a: a.name)


def get_abilities() -> List[AbilityData]:
    return _ABILITIES


_ABILITY_MODIFIERS: List[AbilityModifierData] = [
    AbilityModifierData(
        score=3, mod=-3, spells=-99, max_spell_level=-99
    ),  # type: ignore
    AbilityModifierData(score=4, mod=-2, spells=-2, max_spell_level=1),  # type: ignore
    AbilityModifierData(score=5, mod=-2, spells=-2, max_spell_level=1),  # type: ignore
    AbilityModifierData(score=6, mod=-1, spells=-1, max_spell_level=1),  # type: ignore
    AbilityModifierData(score=7, mod=-1, spells=-1, max_spell_level=1),  # type: ignore
    AbilityModifierData(score=8, mod=-1, spells=0, max_spell_level=2),  # type: ignore
    AbilityModifierData(score=9, mod=0, spells=0, max_spell_level=2),  # type: ignore
    AbilityModifierData(score=10, mod=0, spells=0, max_spell_level=3),  # type: ignore
    AbilityModifierData(score=11, mod=0, spells=0, max_spell_level=3),  # type: ignore
    AbilityModifierData(score=12, mod=0, spells=0, max_spell_level=4),  # type: ignore
    AbilityModifierData(score=13, mod=1, spells=0, max_spell_level=4),  # type: ignore
    AbilityModifierData(score=14, mod=1, spells=1, max_spell_level=4),  # type: ignore
    AbilityModifierData(score=15, mod=1, spells=1, max_spell_level=5),  # type: ignore
    AbilityModifierData(score=16, mod=2, spells=1, max_spell_level=5),  # type: ignore
    AbilityModifierData(score=17, mod=2, spells=2, max_spell_level=5),  # type: ignore
    AbilityModifierData(score=18, mod=3, spells=2, max_spell_level=6),  # type: ignore
]

_ABILITY_MODIFIERS_DICT: Dict[int, AbilityModifierData] = {
    mod.score: mod for mod in _ABILITY_MODIFIERS
}


def get_mod(score: int) -> int:
    return _ABILITY_MODIFIERS_DICT[score].mod


@commands.command()
async def abls(ctx):
    """Lists the six character abilities and their descriptions."""
    embed = Embed(
        title="Abilities",
        description="**Luck**\n"
        + ctx.bot.initbot_state.abilities.get_from_prefix("Luck").description,
    )
    for ability in ctx.bot.initbot_state.abilities.get_all():
        if ability.name != "Luck":
            embed.add_field(name=ability.name, value=ability.description)
    await ctx.send(embed=embed)


@commands.command()
async def abl(ctx, name: str):
    await ctx.send(str(ctx.bot.initbot_state.abilities.get_from_prefix(name)))


@commands.command()
async def mods(ctx):
    await ctx.send(str(_ABILITY_MODIFIERS))


@commands.command()
async def mod(ctx, score: int):
    await ctx.send(str(_ABILITY_MODIFIERS_DICT[score]))


@abls.error
@abl.error
@mods.error
@mod.error
async def handle_error(ctx, error):
    await ctx.send(str(error), delete_after=5)
