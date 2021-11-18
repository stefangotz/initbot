from pathlib import Path
from typing import Dict
import logging

from discord.ext import commands  # type: ignore

from ...models.crit import CritTableModel, CritTablesModel
from ..utils import get_first_set_match_or_over_under_flow


def _match(table: CritTableModel, roll: int) -> str:
    return get_first_set_match_or_over_under_flow(
        roll, table.crits, lambda c: c.rolls
    ).effect


CRIT_TABLES: CritTablesModel = CritTablesModel(crit_tables=[])
PATH: Path = Path(__file__).parent / "crits.json"
if PATH.exists():
    CRIT_TABLES = CritTablesModel.parse_file(PATH)
else:
    logging.warning("Unable to find %s", PATH)

TABLES: Dict[int, CritTableModel] = {tbl.number: tbl for tbl in CRIT_TABLES.crit_tables}


@commands.command()
async def crit(ctx, table: int, roll: int):
    await ctx.send(_match(TABLES[table], roll))


@crit.error
async def crit_error(ctx, error):
    await ctx.send(str(error), delete_after=5)
