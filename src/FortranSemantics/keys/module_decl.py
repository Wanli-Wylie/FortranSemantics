from __future__ import annotations
import re
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from .base import BaseKey
from .regex_patterns import MODULE_DECL_ID_REGEX

@dataclass_json
@dataclass(frozen=True, slots=True)
class ModuleDeclKey(BaseKey):
    module_name: str
    declaration_name: str

    def __post_init__(self):
        if not MODULE_DECL_ID_REGEX.fullmatch(str(self)):
            raise ValueError(f"Invalid ModuleDeclID: {str(self)!r}")

    @classmethod
    def from_string(cls, s: str) -> "ModuleDeclKey":
        m = MODULE_DECL_ID_REGEX.fullmatch(s)
        if not m:
            raise ValueError(f"Invalid ModuleDeclID string: {s!r}")
        return cls(**m.groupdict())

    def __str__(self) -> str:
        return (
            f"(module){self.module_name}"
            f"->(declaration){self.declaration_name}"
        )

    def __eq__(self, other) -> bool:
        return BaseKey.__eq__(self, other)
