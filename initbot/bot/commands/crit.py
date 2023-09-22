from pathlib import Path
from typing import Dict
import logging

from discord.ext import commands  # type: ignore

from ...data.crit import CritTableData, CritTablesData
from ...utils import get_first_set_match_or_over_under_flow


def _match(table: CritTableData, roll: int) -> str:
    return get_first_set_match_or_over_under_flow(
        roll, table.crits, lambda c: c.rolls
    ).effect


_CRIT_TABLES_DATA: CritTablesData = CritTablesData(crit_tables=[])
_PATH: Path = Path(__file__).parent / "crits.json"
if _PATH.exists():
    _CRIT_TABLES_DATA = CritTablesData.parse_file(_PATH)
else:
    logging.warning("Unable to find %s", _PATH)

_TABLES: Dict[int, CritTableData] = {
    tbl.number: tbl for tbl in _CRIT_TABLES_DATA.crit_tables
}


def get_crit_table(number: int):
    return _TABLES[number]


@commands.command()
async def crit(
    ctx,
    table: int = commands.parameter(description="The number of the crit table (1-4)"),
    roll: int = commands.parameter(description="What you rolled on your crit die"),
):
    """Shows the result of a roll on a crit table."""
    await ctx.send(_match(get_crit_table(table), roll))


@crit.error
async def crit_error(ctx, error):
    await ctx.send(str(error), delete_after=5)
