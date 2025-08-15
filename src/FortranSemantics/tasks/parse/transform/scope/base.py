from abc import ABC, abstractmethod
from fparser.two.Fortran2003 import Module, Subroutine_Subprogram, Function_Subprogram
from typing import Any

class BaseTableTransformer(ABC):
    @staticmethod
    @abstractmethod
    def from_module(module: Module) -> Any:
        pass
    
    @staticmethod
    @abstractmethod
    def from_subprogram(subprogram: Subroutine_Subprogram | Function_Subprogram) -> Any:
        pass
    
