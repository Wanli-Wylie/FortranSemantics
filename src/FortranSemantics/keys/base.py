from __future__ import annotations
from abc import ABC, abstractmethod

class BaseKey(ABC):
    """公共接口：子类需实现 __str__ / from_string；此处提供 str-like 行为。"""

    # ——— 子类必须实现 ———
    @classmethod
    @abstractmethod
    def from_string(cls, s: str) -> "BaseKey": 
        pass
    
    @abstractmethod
    def __str__(self) -> str: 
        pass

    # ——— 像字符串一样比较 / 哈希 ———
    def __repr__(self) -> str:           # print-friendly
        return f"{self.__class__.__name__}({str(self)!r})"

    def __eq__(self, other) -> bool:     # 与 BaseID 或 str 等价比较
        if isinstance(other, BaseKey) or hasattr(other, "__str__"):
            try:
                return str(self) == str(other)
            except Exception:
                return False
        if isinstance(other, str):
            return str(self) == other
        return False

    def __hash__(self) -> int:
        return hash(str(self))

    # 便捷 str 行为
    def __len__(self) -> int:
        return len(str(self))

    def __contains__(self, item: str) -> bool:
        return item in str(self)
