from Fortran2.semantics.contexts.ast import ASTContext
from Fortran2.semantics.contexts.semantics import SemanticsContext
from Fortran2.semantics.contexts.dependency_graph import build_dependency_graph
from Fortran2.semantics.core_context import SemanticsCore
from Fortran2.utils.process_fortran_string import fortran_string_to_ast, pickup_module_ast
from pathlib import Path
import networkx as nx
import pickle
import json

if __name__ == "__main__":
    dir = Path(__file__).parent
    modules = []
    for file in dir.glob("*.f90"):
        ast = fortran_string_to_ast(file.read_text())
        module_ast = pickup_module_ast(ast)
        modules.append(module_ast)
        
    pass