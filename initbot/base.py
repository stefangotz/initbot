from dataclasses import asdict
from typing import Any, Dict


class BaseData:
    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)  # type: ignore
