from __future__ import annotations
import re
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from .base import BaseKey
from .regex_patterns import SUBPROGRAM_DECL_ID_REGEX


@dataclass_json
@dataclass(frozen=True, slots=True)
class SubprogramDeclKey(BaseKey):
    module_name: str
    subprogram_type: str
    subprogram_name: str
    declaration_name: str

    def __post_init__(self):
        if not SUBPROGRAM_DECL_ID_REGEX.fullmatch(str(self)):
            raise ValueError(f"Invalid SubprogramDeclID: {str(self)!r}")

    @classmethod
    def from_string(cls, s: str) -> "SubprogramDeclKey":
        m = SUBPROGRAM_DECL_ID_REGEX.fullmatch(s)
        if not m:
            raise ValueError(f"Invalid SubprogramDeclID string: {s!r}")
        return cls(**m.groupdict())

    def __str__(self) -> str:
        return (
            f"(module){self.module_name}"
            f"->({self.subprogram_type}){self.subprogram_name}"
            f"->(declaration){self.declaration_name}"
        )

    def __eq__(self, other) -> bool:
        return BaseKey.__eq__(self, other)
