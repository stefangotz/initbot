from dataclasses import dataclass
from typing import List
from discord.ext import commands  # type: ignore

from ..utils import get_first_set_match
from .roll import DieRoll
from .equipment import Equipment


@dataclass
class OccupationDI:
    rolls: List[int]
    name: str
    weapon: str
    goods: Equipment


OCCUPATIONS: List[OccupationDI] = [
    OccupationDI([1], "Alchemist", "Staff", Equipment("Oil, 1 flask")),
    OccupationDI([2], "Animal trainer", "Club", Equipment("Pony")),
    OccupationDI([3], "Armorer", "Hammer (as club)", Equipment("Iron helmet")),
    OccupationDI([4], "Astrologer", "Dagger", Equipment("Spyglass")),
    OccupationDI([5], "Barber", "Razor (as dagger)", Equipment("Scissors")),
    OccupationDI([6], "Beadle", "Staff", Equipment("Holy symbol")),
    OccupationDI([7], "Beekeeper", "Staff", Equipment("Jar of honey")),
    OccupationDI([8], "Blacksmith", "Hammer (as club)", Equipment("Steel tongs")),
    OccupationDI([9], "Butcher", "Cleaver (as axe)", Equipment("Side of beef")),
    OccupationDI([10], "Caravan guard", "Short sword", Equipment("Linen, 1 yard")),
    OccupationDI([11], "Cheesemaker", "Cudgel (as staff)", Equipment("Stinky cheese")),
    OccupationDI([12], "Cobbler", "Awl (as dagger)", Equipment("Shoehorn")),
    OccupationDI([13], "Confidence artist", "Dagger", Equipment("Quality cloak")),
    OccupationDI([14], "Cooper", "Crowbar (as club)", Equipment("Barrel")),
    OccupationDI([15], "Costermonger", "Knife (as dagger)", Equipment("Fruit")),
    OccupationDI([16], "Cutpurse", "Dagger", Equipment("Small chest")),
    OccupationDI(
        [17], "Ditch digger", "Shovel (as staff)", Equipment("Fine dirt, 1 lb.")
    ),
    OccupationDI(
        [18], "Dwarven apothecarist", "Cudgel (as staff)", Equipment("Steel vial")
    ),
    OccupationDI(
        [19, 20], "Dwarven blacksmith", "Hammer (as club)", Equipment("Mithril, 1 oz.")
    ),
    OccupationDI(
        [21], "Dwarven chest-maker", "Chisel (as dagger)", Equipment("Wood, 10 lbs.")
    ),
    OccupationDI(
        [22],
        "Dwarven herder",
        "Staff",
        Equipment(
            "Sow (Why did the chicken cross the hallway? To check for traps! In all seriousness, if the party includes more than one farmer or herder, randomly determine the second and subsequent farm animals for each duplicated profession with 1d6: (1) sheep, (2) goat, (3) cow, (4) duck, (5) goose, (6) mule.)"
        ),
    ),
    OccupationDI([23, 24], "Dwarven miner", "Pick (as club)", Equipment("Lantern")),
    OccupationDI([25], "Dwarven mushroom-farmer", "Shovel", Equipment("Sack")),
    OccupationDI([26], "Dwarven rat-catcher", "Club", Equipment("Net")),
    OccupationDI(
        [27, 28], "Dwarven stonemason", "Hammer", Equipment("Fine stone, 10 lbs.")
    ),
    OccupationDI([29], "Elven artisan", "Staff", Equipment("Clay, 1 lb.")),
    OccupationDI([30], "Elven barrister", "Quill (as dart)", Equipment("Book")),
    OccupationDI(
        [31], "Elven chandler", "Scissors (as dagger)", Equipment("Candles, 20")
    ),
    OccupationDI([32], "Elven falconer", "Dagger", Equipment("Falcon")),
    OccupationDI([33, 34], "Elven forester", "Staff", Equipment("Herbs, 1 lb.")),
    OccupationDI([35], "Elven glassblower", "Hammer", Equipment("Glass beads")),
    OccupationDI([36], "Elven navigator", "Bow", Equipment("Spyglass")),
    OccupationDI(
        [37, 38], "Elven sage", "Dagger", Equipment("Parchment and quill pen")
    ),
    OccupationDI(
        list(range(39, 48)),
        "Farmer (Roll 1d8 to determine farmer type: (1) potato, (2) wheat, (3) turnip, (4) corn, (5) rice, (6) parsnip, (7) radish, (8) rutabaga.)",
        "Pitchfork (as spear)",
        Equipment(
            "Hen (Why did the chicken cross the hallway? To check for traps! In all seriousness, if the party includes more than one farmer or herder, randomly determine the second and subsequent farm animals for each duplicated profession with 1d6: (1) sheep, (2) goat, (3) cow, (4) duck, (5) goose, (6) mule."
        ),
    ),
    OccupationDI([48], "Fortune-teller", "Dagger", Equipment("Tarot deck")),
    OccupationDI([49], "Gambler", "Club", Equipment("Dice")),
    OccupationDI(
        [50], "Gongfarmer", "Trowel (as dagger)", Equipment("Sack of night soil")
    ),
    OccupationDI([51, 52], "Grave digger", "Shovel (as staff)", Equipment("Trowel")),
    OccupationDI([53, 54], "Guild beggar", "Sling", Equipment("Crutches")),
    OccupationDI(
        [55], "Halfling chicken butcher", "Hand axe", Equipment("Chicken meat, 5 lbs.")
    ),
    OccupationDI([56, 57], "Halfling dyer", "Staff", Equipment("Fabric, 3 yards")),
    OccupationDI(
        [58],
        "Halfling glovemaker",
        "Awl (as dagger)",
        Equipment("Pair of Gloves", 0, 4),
    ),
    OccupationDI([59], "Halfling gypsy", "Sling", Equipment("Hex doll")),
    OccupationDI(
        [60],
        "Halfling haberdasher",
        "Scissors (as dagger)",
        Equipment("Fine suit", 0, 3),
    ),
    OccupationDI(
        [61], "Halfling mariner", "Knife (as dagger)", Equipment("Sailcloth, 2 yards")
    ),
    OccupationDI(
        [62], "Halfling moneylender", "Short sword", Equipment("Money", 1, 800)
    ),
    OccupationDI([63], "Halfling trader", "Short sword", Equipment("20 sp")),
    OccupationDI([64], "Halfling vagrant", "Club", Equipment("Begging bowl")),
    OccupationDI([65], "Healer", "Club", Equipment("Holy water, 1 vial")),
    OccupationDI([66], "Herbalist", "Club", Equipment("Herbs, 1 lb.")),
    OccupationDI(
        [67],
        "Herder",
        "Staff",
        Equipment(
            "Herding dog (Why did the chicken cross the hallway? To check for traps! In all seriousness, if the party includes more than one farmer or herder, randomly determine the second and subsequent farm animals for each duplicated profession with 1d6: (1) sheep, (2) goat, (3) cow, (4) duck, (5) goose, (6) mule.)"
        ),
    ),
    OccupationDI([68, 69], "Hunter", "Shortbow", Equipment("Deer pelt")),
    OccupationDI([70], "Indentured servant", "Staff", Equipment("Locket")),
    OccupationDI([71], "Jester", "Dart", Equipment("Silk clothes")),
    OccupationDI([72], "Jeweler", "Dagger", Equipment("Gem worth 20 gp")),
    OccupationDI([73], "Locksmith", "Dagger", Equipment("Fine tools")),
    OccupationDI([74], "Mendicant", "Club", Equipment("Cheese dip")),
    OccupationDI([75], "Mercenary", "Longsword", Equipment("Hide armor")),
    OccupationDI([76], "Merchant", "Dagger", Equipment("4 gp, 14 sp, 27 cp")),
    OccupationDI([77], "Miller/baker", "Club", Equipment("Flour, 1 lb.")),
    OccupationDI([78], "Minstrel", "Dagger", Equipment("Ukulele")),
    OccupationDI([79], "Noble", "Longsword", Equipment("Gold ring worth 10 gp")),
    OccupationDI([80], "Orphan", "Club", Equipment("Rag doll")),
    OccupationDI([81], "Ostler", "Staff", Equipment("Bridle")),
    OccupationDI([82], "Outlaw", "Short sword", Equipment("Leather armor")),
    OccupationDI([83], "Rope maker", "Knife (as dagger)", Equipment("Rope, 100'")),
    OccupationDI([84], "Scribe", "Dart", Equipment("Parchment, 10 sheets")),
    OccupationDI([85], "Shaman", "Mace", Equipment("Herbs, 1 lb.")),
    OccupationDI([86], "Slave", "Club", Equipment("Strange-looking rock")),
    OccupationDI([87], "Smuggler", "Sling", Equipment("Waterproof sack")),
    OccupationDI([88], "Soldier", "Spear", Equipment("Shield")),
    OccupationDI([89, 90], "Squire", "Longsword", Equipment("Steel helmet")),
    OccupationDI([91], "Tax collector", "Longsword", Equipment("100 cp")),
    OccupationDI([92, 93], "Trapper", "Sling", Equipment("Badger pelt")),
    OccupationDI([94], "Urchin", "Stick (as club)", Equipment("Begging bowl")),
    OccupationDI(
        [95],
        "Wainwright",
        "Club",
        Equipment(
            "Pushcart (Roll 1d6 to determine what's in the cart: (1) tomatoes, (2) nothing, (3) straw, (4) your dead, (5) dirt, (6) rocks.)"
        ),
    ),
    OccupationDI([96], "Weaver", "Dagger", Equipment("Fine suit of clothes")),
    OccupationDI([97], "Wizard's apprentice", "Dagger", Equipment("Black grimoire")),
    OccupationDI([98, 99, 100], "Woodcutter", "Handaxe", Equipment("Bundle of wood")),
]


def get_random_occupation() -> OccupationDI:
    roll: int = DieRoll(100).roll_one()
    return get_occupation(roll)


def get_occupation(roll: int) -> OccupationDI:
    return get_first_set_match(roll, OCCUPATIONS, lambda o: o.rolls)


@commands.command()
async def occupations(ctx):
    await ctx.send(str(OCCUPATIONS))


@occupations.error
async def occupations_error(ctx, error):
    await ctx.send(str(error), delete_after=5)
