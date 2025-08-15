from __future__ import annotations
import re
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from .base import BaseKey
from .regex_patterns import MODULE_ID_REGEX

@dataclass_json
@dataclass(frozen=True, slots=True)
class ModuleKey(BaseKey):
    module_name: str

    # —— 校验 —— #
    def __post_init__(self):
        if not MODULE_ID_REGEX.fullmatch(str(self)):
            raise ValueError(f"Invalid ModuleID: {str(self)!r}")

    # —— 构造器 —— #
    @classmethod
    def from_string(cls, s: str) -> "ModuleKey":
        m = MODULE_ID_REGEX.fullmatch(s)
        if not m:
            raise ValueError(f"Invalid ModuleID string: {s!r}")
        return cls(**m.groupdict())

    # —— 序列化 —— #
    def __str__(self) -> str:
        return f"(module){self.module_name}"

    def __eq__(self, other) -> bool:
        return BaseKey.__eq__(self, other)
