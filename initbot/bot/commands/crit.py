from pathlib import Path
from typing import List, Dict
import json
import logging
from discord.ext import commands  # type: ignore
from pydantic.dataclasses import dataclass

from ..utils import get_first_set_match_or_over_under_flow
from .roll import DieRoll


@dataclass
class Crit:
    rolls: List[int]
    effect: str


@dataclass
class CritTable:
    number: int
    crits: List[Crit]

    def match(self, roll: int) -> str:
        return get_first_set_match_or_over_under_flow(
            roll, self.crits, lambda c: c.rolls
        ).effect


TABLES: Dict[int, CritTable] = {}
PATH: Path = Path(__file__).parent / "crits.json"
if PATH.exists():
    with open(PATH, encoding="utf8") as fd:
        TABLES = {
            t["number"]: CritTable(**t)  # type: ignore
            for t in json.load(fd)["crit_tables"]
        }
else:
    logging.warning("Unable to find %s", PATH)


@dataclass
class Criticality:
    die: DieRoll
    table: CritTable


@commands.command()
async def crit(ctx, table: int, roll: int):
    await ctx.send(TABLES[table].match(roll))


@crit.error
async def crit_error(ctx, error):
    await ctx.send(str(error), delete_after=5)
