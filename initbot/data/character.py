from dataclasses import dataclass
from typing import Union, List

from ..base import BaseData


# pylint: disable=R0801
@dataclass
class CharacterData(BaseData):
    name: str
    user: str
    active: bool = True
    level: int = 0
    strength: Union[int, None] = None
    agility: Union[int, None] = None
    stamina: Union[int, None] = None
    personality: Union[int, None] = None
    intelligence: Union[int, None] = None
    luck: Union[int, None] = None
    initial_luck: Union[int, None] = None
    hit_points: Union[int, None] = None
    equipment: Union[List[str], None] = None
    occupation: Union[int, None] = None
    exp: Union[int, None] = None
    alignment: Union[str, None] = None
    initiative: Union[int, None] = None
    initiative_time: Union[int, None] = None
    initiative_modifier: Union[int, None] = None
    hit_die: Union[int, None] = None
    augur: Union[int, None] = None
    cls: Union[str, None] = None
