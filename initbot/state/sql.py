from dataclasses import asdict
from inspect import isclass
from pathlib import Path
from typing import Iterable, Sequence, Tuple, cast

from peewee import Model, CharField, IntegerField, SqliteDatabase, BooleanField, Field

from ..data.ability import AbilityData, AbilityModifierData
from ..data.augur import AugurData
from ..data.character import CharacterData
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


class _SqlAugurData(Model):
    description = CharField()
    roll = IntegerField(primary_key=True)


class _SqlAugurState(AugurState):
    def get_all(self) -> Sequence[AugurData]:
        return cast(Sequence[AugurData], tuple(_SqlAugurData.select()))

    def get_from_roll(self, roll: int) -> AugurData:
        return cast(AugurData, _SqlAugurData.select().where(_SqlAugurData.roll == roll))


class _StrSeqField(Field):
    field_type = "text"

    def db_value(self, value: Iterable[str]) -> str:
        return "\x1e".join(value)

    def python_value(self, value: str) -> Sequence[str]:
        return value.split("\x1e")


class _SqlCharacterData(Model):
    name = CharField(unique=True, primary_key=True)
    user = CharField()
    active = BooleanField(default=True)
    level = IntegerField(default=0)
    strength = IntegerField(null=True)
    agility = IntegerField(null=True)
    stamina = IntegerField(null=True)
    personality = IntegerField(null=True)
    intelligence = IntegerField(null=True)
    luck = IntegerField(null=True)
    initial_luck = IntegerField(null=True)
    hit_points = IntegerField(null=True)
    equipment = _StrSeqField(null=True)
    occupation = IntegerField(null=True)
    exp = IntegerField(null=True)
    alignment = CharField(null=True)
    initiative = IntegerField(null=True)
    initiative_time = IntegerField(null=True)
    initiative_modifier = IntegerField(null=True)
    hit_die = IntegerField(null=True)
    augur = IntegerField(null=True)
    cls = CharField(null=True)


class _SqlCharacterState(CharacterState):
    def get_all(self) -> Sequence[CharacterData]:
        return cast(Tuple[CharacterData, ...], tuple(_SqlCharacterData.select()))

    def add_store_and_get(self, char_data: CharacterData) -> CharacterData:
        return cast(
            CharacterData,
            _SqlCharacterData.create(
                **{k: v for k, v in asdict(char_data).items() if v is not None}
            ),
        )

    def remove_and_store(self, char_data: CharacterData) -> None:
        _SqlCharacterData.delete().where(_SqlCharacterData.name == char_data.name)

    def update_and_store(self, char_data: CharacterData) -> None:
        if not isinstance(char_data, _SqlCharacterData):
            raise TypeError(
                f"Only character data returned by the State class can be updated: {char_data}"
            )
        cast(_SqlCharacterData, char_data).save()


class SqlState(State):
    def __init__(self, sqlite_db_file: Path):  # type: ignore
        self._abilities = _SqlAbilityState()
        self._augurs = _SqlAugurState()
        self._characters = _SqlCharacterState()

        data_classes: Tuple[type[Model], ...] = tuple(
            cast(type[Model], i)
            for i in globals().values()
            if isclass(i) and issubclass(i, Model)
        )
        self._db = SqliteDatabase(sqlite_db_file)
        self._db.bind(data_classes)

    @property
    def abilities(self) -> AbilityState:
        return self._abilities

    @property
    def augurs(self) -> AugurState:
        return self._augurs

    @property
    def characters(self) -> CharacterState:
        return self._characters

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
            (_SqlAugurData, src.augurs.get_all()),
            (_SqlCharacterData, src.characters.get_all()),
        )
        for cls, items in data_classes_and_items:
            cls.insert_many(i.as_dict() for i in items)
