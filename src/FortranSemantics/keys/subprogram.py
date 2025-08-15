from __future__ import annotations
import re
from dataclasses import dataclass
from .base import BaseKey
from .module import ModuleKey
from .regex_patterns import SUBPROGRAM_ID_REGEX

@dataclass(frozen=True, slots=True)
class SubprogramKey(BaseKey):
    module_name: str
    subprogram_type: str   # "subroutine" | "function"
    subprogram_name: str

    def __post_init__(self):
        if not SUBPROGRAM_ID_REGEX.fullmatch(str(self)):
            raise ValueError(f"Invalid SubprogramID: {str(self)!r}")

    @classmethod
    def from_string(cls, s: str) -> "SubprogramKey":
        m = SUBPROGRAM_ID_REGEX.fullmatch(s)
        if not m:
            raise ValueError(f"Invalid SubprogramID string: {s!r}")
        return cls(**m.groupdict())

    def __str__(self) -> str:
        return (
            f"(module){self.module_name}"
            f"->({self.subprogram_type}){self.subprogram_name}"
        )

    def __eq__(self, other) -> bool:
        return BaseKey.__eq__(self, other)

    # —— 便捷：取父模块 —— #
    @property
    def parent_module(self) -> "ModuleKey":

        return ModuleKey(module_name=self.module_name)
