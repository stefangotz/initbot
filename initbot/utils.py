from typing import Dict, Any, List
import re

_INT_PATTERN = re.compile(r"^-?(0|([1-9][0-9]*))$")
_CHARACTERS: Dict[str, Any] = {"mediocre_mel": {}}


def is_int(txt: str):
    return _INT_PATTERN.match(txt) is not None


def char_from_tokens(tokens: List[str], user: str):
    name: str = " ".join(tokens)
    return char_from_str(name, user)


def char_from_str(name: str, user: str):
    if name:
        return char_from_name(name)
    return char_from_user(user)


def char_from_name(name: str):
    nrm: str = normalize_name(name)
    return _CHARACTERS[nrm]


def char_from_user(user: str):
    return user


def normalize_name(name: str) -> str:
    return name.lower().replace(" ", "_")
