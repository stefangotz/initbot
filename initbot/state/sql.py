from pathlib import Path
from typing import Sequence, cast

from peewee import Model, CharField, IntegerField, SqliteDatabase

from ..data.ability import AbilityData, AbilityModifierData
from .state import (
    AbilityState,
    AugurState,
    CharacterState,
    ClassState,
    CritState,
    OccupationState,
    State,
)


class _SqlAbilityData(Model):
    name = CharField(unique=True)
    description = CharField()


class _SqlAbilityModifierData(Model):
    score = IntegerField(unique=True)
    mod = IntegerField()
    spells = IntegerField()
    max_spell_level = IntegerField()


class _SqlAbilityState(AbilityState):
    def get_all(self) -> Sequence[AbilityData]:
        return cast(Sequence[AbilityData], tuple(_SqlAbilityData.select()))

    def get_mods(self) -> Sequence[AbilityModifierData]:
        return cast(
            Sequence[AbilityModifierData], tuple(_SqlAbilityModifierData.select())
        )


class SqlState(State):
    def __init__(self, sqlite_db_file: Path):  # type: ignore
        self._abilities = _SqlAbilityState()
        data_classes = (
            _SqlAbilityData,
            _SqlAbilityModifierData,
        )
        self._db = SqliteDatabase(sqlite_db_file)
        self._db.bind(data_classes)

    @property
    def abilities(self) -> AbilityState:
        return self._abilities

    @property
    def augurs(self) -> AugurState:
        raise NotImplementedError()

    @property
    def characters(self) -> CharacterState:
        raise NotImplementedError()

    @property
    def occupations(self) -> OccupationState:
        raise NotImplementedError()

    @property
    def classes(self) -> ClassState:
        raise NotImplementedError()

    @property
    def crits(self) -> CritState:
        raise NotImplementedError()

    def import_state(self, src: State) -> None:
        data_classes_and_items = (
            (_SqlAbilityData, src.abilities.get_all()),
            (_SqlAbilityModifierData, src.abilities.get_mods()),
        )
        for cls, items in data_classes_and_items:
            cls.insert_many(i.as_dict() for i in items)
