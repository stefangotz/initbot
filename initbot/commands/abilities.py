from dataclasses import dataclass
from typing import List, Dict
from discord.ext import commands  # type: ignore


@dataclass
class Ability:
    name: str
    description: str


ABILITIES: List[Ability] = [
    Ability(
        "Strength",
        "Physical power for lifting, hurling, cutting, and dragging. Your Strength modifier affects melee attack and damage rolls. Note that a successful attack always does a minimum of 1 point of damage regardless of Strength. Characters with a Strength of 5 or less can carry a weapon or a shield but not both.",
    ),
    Ability(
        "Agility",
        "Balance, grace, and fine motion skills, whether in the hands or the feet. Your Agility modifier affects Armor Class, missile fire attack rolls, initiative rolls, and Reflex saving throws, as well as the ability to fight with a weapon in each hand.",
    ),
    Ability(
        "Stamina",
        "Endurance, resistance to pain, disease, and poison. Your Stamina modifier affects hit points (even at level 0) and Fortitude saving throws. Note that a character earns a minimum of 1 hit point per character level regardless of Stamina Characters with a Stamina of 5 or less automatically take double damage from all poisons and diseases.",
    ),
    Ability(
        "Personality",
        "Charm, strength of will, persuasive talent. Personality affects Willpower saving throws for all characters. Personality is vitally important to clerics, as it affects the ability to draw upon divine power and determines the maximum spell level they can cast, as shown on table 1-1.",
    ),
    Ability(
        "Intelligence",
        "Ability to discern information, retain knowledge, and assess complex situations. For wizards, Intelligence affects spell count and maximum spell level, as noted on table 1-1. For all characters, Intelligence affects known languages, as described in Appendix L. Characters with an Intelligence of 7 or less can speak only Common, and those with an Intelligence of 5 or less cannot read or write.",
    ),
    Ability(
        "Luck",
        "“Right place, right time;” favor of the gods, good fortune, or hard-to-define talent. Players would be well advised to understand the goals of gods and demons that shape the world around them, for they are but pawns in a cosmic struggle, and their luck on this mortal plane can be influenced by the eternal conflict that rages around them. Luck affects several elements of the game, as follows: • After rolling 3d6 to determine a player’s Luck score, roll on table 1-2 to determine which roll is affected by the character’s Luck modifier. This “lucky roll” is modified by the character’s starting 0-level Luck modifier (for good or bad) in addition to all other normal modifiers. In some cases, the “lucky roll” is completely useless because the character chooses a class where it is not applicable.\n"
        "• Note that the lucky roll modifier does not change over time as the character’s Luck changes. For example, if a character’s Luck modifier is +1 and his lucky roll is spell checks, he receives a +1 modifier to all spell checks henceforth. This modifier does not change if his Luck score changes.\n"
        "• The character’s Luck modifier affects other rolls in the game: critical hits, fumbles, corruption, and select other rolls, as described henceforth. In addition, Luck modifies a different element of play for each character class, as described in the class descriptions.\n"
        "• Characters can burn off Luck to survive life-or-death situations. Any character can permanently burn Luck to give a one-time bonus to a roll. For example, you could burn 6 points of Luck to get a +6 modifier on a roll, but your Luck score is now 6 points lower.\n"
        "• Characters can make Luck checks to attempt feats that succeed based on Luck alone. The judge will provide the specifics of any attempt, but the attempt is usually resolved by rolling equal to or less than the character’s Luck score on 1d20.\n"
        "• For all characters, Luck may be restored over the course of their adventures, and this restoration process is loosely linked to the character’s alignment. Characters that act against their alignment may find themselves suddenly unlucky. Those who swear an oath to a patron of their newly desired alignment may find the change easier.\n"
        "• Thieves and halflings have a particular affinity with luck. These classes renew their Luck score at a defined rate, as discussed in their class descriptions.",
    ),
]

ABILITIES_DICT: Dict[str, Ability] = {abl.name: abl for abl in ABILITIES}


@dataclass
class AbilityScoreModifier:
    score: int
    mod: int
    spells: int
    max_spell_level: int


ABILITY_SCORE_MODIFIERS: List[AbilityScoreModifier] = [
    AbilityScoreModifier(3, -3, -99, -99),
    AbilityScoreModifier(4, -2, -2, 1),
    AbilityScoreModifier(5, -2, -2, 1),
    AbilityScoreModifier(6, -1, -1, 1),
    AbilityScoreModifier(7, -1, -1, 1),
    AbilityScoreModifier(8, -1, 0, 2),
    AbilityScoreModifier(9, 0, 0, 2),
    AbilityScoreModifier(10, 0, 0, 3),
    AbilityScoreModifier(11, 0, 0, 3),
    AbilityScoreModifier(12, 0, 0, 4),
    AbilityScoreModifier(13, 1, 0, 4),
    AbilityScoreModifier(14, 1, 1, 4),
    AbilityScoreModifier(15, 1, 1, 5),
    AbilityScoreModifier(16, 2, 1, 5),
    AbilityScoreModifier(17, 2, 2, 5),
    AbilityScoreModifier(18, 3, 2, 6),
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
    await ctx.send(str(ABILITIES))


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
    await ctx.send(str(error))
