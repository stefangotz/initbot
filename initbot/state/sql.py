from collections.abc import Iterable, Sequence, Set
from dataclasses import asdict
from inspect import isclass
from pathlib import Path
from typing import Type, cast

from peewee import (
    Model,
    CharField,
    CompositeKey,
    IntegerField,
    SqliteDatabase,
    BooleanField,
    Field,
    ForeignKeyField,
)

from ..base import BaseData
from ..data.ability import AbilityData, AbilityModifierData
from ..data.augur import AugurData
from ..data.character import CharacterData
from ..data.cls import ClassData
from ..data.crit import CritTableData
from ..data.occupation import OccupationData
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

    def import_from(self, src: AbilityState) -> None:
        _import_from(_SqlAbilityData, src.get_all())
        _import_from(_SqlAbilityModifierData, src.get_mods())


class _SqlAugurData(Model):
    description = CharField()
    roll = IntegerField(primary_key=True)


class _SqlAugurState(AugurState):
    def get_all(self) -> Sequence[AugurData]:
        return cast(Sequence[AugurData], tuple(_SqlAugurData.select()))

    def get_from_roll(self, roll: int) -> AugurData:
        return cast(AugurData, _SqlAugurData.select().where(_SqlAugurData.roll == roll))

    def import_from(self, src: AugurState) -> None:
        _import_from(_SqlAugurData, src.get_all())


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
        return cast(Sequence[CharacterData], tuple(_SqlCharacterData.select()))

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

    def import_from(self, src: CharacterState) -> None:
        _import_from(_SqlCharacterData, src.get_all())


class _IntSeqField(Field):
    field_type = "text"

    def db_value(self, value: Iterable[int]) -> str:
        return "\x1e".join(map(str, value))

    def python_value(self, value: str) -> Sequence[int]:
        return tuple(map(int, value.split("\x1e")))


class _SqlOccupationData(Model):
    rolls = _IntSeqField()
    name = CharField()
    weapon = CharField()
    goods = CharField()


class _SqlOccupationState(OccupationState):
    def get_all(self) -> Sequence[OccupationData]:
        return cast(Sequence[OccupationData], tuple(_SqlOccupationData.select()))

    def import_from(self, src: OccupationState) -> None:
        _import_from(_SqlOccupationData, src.get_all())


class _SqlClassData(Model):
    name = CharField(primary_key=True)
    hit_die = IntegerField()
    weapons = _StrSeqField()


class _SqlSpellsByLevelData(Model):
    level = IntegerField()
    spells = IntegerField()
    class_name = CharField()
    class_level = IntegerField()

    class Meta:
        primary_key = CompositeKey("class_name", "class_level", "level")


class _SqlLevelData(Model):
    level = IntegerField()
    attack_die = CharField()
    crit_die = CharField()
    crit_table = IntegerField()
    action_dice = _StrSeqField()
    ref = IntegerField()
    fort = IntegerField()
    will = IntegerField()
    thief_luck_die = IntegerField()
    threat_range = _IntSeqField()
    spells = IntegerField()
    max_spell_level = IntegerField()
    sneak_hide = IntegerField()
    class_data = ForeignKeyField(_SqlClassData, backref="levels")

    class Meta:
        primary_key = CompositeKey("class_data", "level")

    # Ideally, we could express the relationship between _SqlLevelData and _SqlSpellsByLevelData through a ForeignKeyField.
    # Unfortunately, peewee appears to have some internal limitations that prevents two nested levels of foreign keys from working as expected.
    # We therefore express this relationship explicitly here and through the class_name and class_name attributes of _SqlSpellsByLevelData.
    @property
    def spells_by_level(self) -> Sequence[_SqlSpellsByLevelData]:
        return tuple(
            _SqlSpellsByLevelData.select().join(
                _SqlLevelData,
                on=(
                    _SqlSpellsByLevelData.class_name == _SqlLevelData.class_data.name
                    and _SqlSpellsByLevelData.class_level == _SqlLevelData.level
                ),
            )
        )


class _SqlClassState(ClassState):
    def get_all(self) -> Sequence[ClassData]:
        return cast(Sequence[ClassData], tuple(_SqlClassData.select()))

    def import_from(self, src: ClassState) -> None:
        _SqlLevelData.delete().execute()  # pylint: disable=no-value-for-parameter
        _SqlSpellsByLevelData.delete().execute()  # pylint: disable=no-value-for-parameter
        _SqlClassData.delete().execute()  # pylint: disable=no-value-for-parameter
        for src_class in src.get_all():
            tgt_class = _SqlClassData.create(
                **{k: v for k, v in src_class.as_dict().items() if k != "levels"}
            )
            for src_level in src_class.levels:
                data = {
                    k: v
                    for k, v in src_level.as_dict().items()
                    if k != "spells_by_level"
                }
                data.update({"class_data": tgt_class})
                _SqlLevelData.create(**data)
                for src_spells_by_level in src_level.spells_by_level:
                    data = dict(src_spells_by_level.as_dict())
                    data.update(
                        {"class_name": src_class.name, "class_level": src_level.level}
                    )
                    _SqlSpellsByLevelData.create(**data)


class _SqlCritTableData(Model):
    number = IntegerField(primary_key=True)


class _SqlCritData(Model):
    rolls = _IntSeqField()
    effect = CharField()
    _table = ForeignKeyField(_SqlCritTableData, backref="crits")


class _SqlCritState(CritState):
    def get_all(self) -> Sequence[CritTableData]:
        return cast(Sequence[CritTableData], tuple(_SqlCritTableData.select()))

    def import_from(self, src: CritState) -> None:
        _SqlCritData.delete().execute()  # pylint: disable=no-value-for-parameter
        _SqlCritTableData.delete().execute()  # pylint: disable=no-value-for-parameter
        for src_crit_table in src.get_all():
            tgt_crit_table = _SqlCritTableData.create(number=src_crit_table.number)
            for src_crit in src_crit_table.crits:
                _SqlCritData.create(
                    rolls=src_crit.rolls, effect=src_crit.effect, _table=tgt_crit_table
                )


class SqlState(State):
    def __init__(
        self,
        source: str,
    ):
        self._abilities = _SqlAbilityState()
        self._augurs = _SqlAugurState()
        self._characters = _SqlCharacterState()
        self._crits = _SqlCritState()
        self._occupations = _SqlOccupationState()
        self._classes = _SqlClassState()

        state_type, state_source = source.split(":", maxsplit=1)
        if state_type == "sqlite":
            path = Path(state_source)
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch(exist_ok=True)
            self._db = SqliteDatabase(path)
        else:
            raise ValueError(f"Unsupported state type: {state_type}")

        data_classes = _get_data_classes()
        self._db.bind(data_classes)
        self._db.create_tables(data_classes)

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
        return self._occupations

    @property
    def classes(self) -> ClassState:
        return self._classes

    @property
    def crits(self) -> CritState:
        return self._crits

    @classmethod
    def get_supported_state_types(cls) -> Set[str]:
        return {"sqlite"}


def _import_from(cls: Type, items: Iterable[BaseData]) -> None:
    cls.insert_many(i.as_dict() for i in items)


def _get_data_classes() -> Sequence[type[Model]]:
    return tuple(
        cast(type[Model], i)
        for i in globals().values()
        if isclass(i) and issubclass(i, Model) and i is not Model
    )
